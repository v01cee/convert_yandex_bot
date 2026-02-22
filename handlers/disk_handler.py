import logging
import re
import uuid
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=2)

from aiogram import Router
from aiogram.types import Message, FSInputFile

from services.yandex_disk import YandexDisk
from services.video_converter import VideoConverter
from services.transcription import TranscriptionService
from config import YANDEX_DISK_TOKEN, ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()

# Инициализация сервисов (один раз при старте)
_disk = YandexDisk(YANDEX_DISK_TOKEN)
_converter = VideoConverter(temp_dir="temp")
_transcription = TranscriptionService(model_size="base")

TEMP_DIR = Path("temp")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _is_yandex_disk_url(text: str) -> bool:
    if not text:
        return False
    patterns = [
        r'disk\.yandex\.ru',
        r'yandex\.ru/disk',
        r'yandex\.ru/d/',
        r'yandex\.ru/i/',
        r'disk\.yandex\.ru/i/',
        r'yandex\.ru/client/disk',
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _bar(pct: int, width: int = 12) -> str:
    """Рисует прогресс-бар для pct в диапазоне 0-100."""
    pct = max(0, min(100, pct))
    filled = round(width * pct / 100)
    return '█' * filled + '░' * (width - filled)


def _progress_text(video_name: str, stage: str, pct: int, file_idx: int, total: int) -> str:
    file_line = f"Файл {file_idx}/{total}\n" if total > 1 else ""
    return f"⏳ {file_line}[{_bar(pct)}] {pct}%\n\n📄 {video_name}\n➤ {stage}"


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} МБ"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} КБ"
    return f"{size_bytes} Б"


def _file_list_text(videos: List[Dict]) -> str:
    lines = []
    for i, v in enumerate(videos[:20], 1):
        name = v.get("name", "?")
        size = v.get("size", 0)
        lines.append(f"{i}. {name} ({_format_size(size)})")
    text = f"🎬 Найдено видео: {len(videos)}\n\n" + "\n".join(lines)
    if len(videos) > 20:
        text += f"\n…и ещё {len(videos) - 20} файлов"
    return text


def _step_range(file_idx: int, total_files: int, step: int):
    """Возвращает (start_pct, end_pct) для шага внутри файла.
    step: 1=скачать (0→33%), 2=конвертировать (33→66%), 3=транскрибировать (66→100%)
    Для N файлов диапазон каждого файла масштабируется пропорционально.
    """
    f_start = (file_idx - 1) * 100 // total_files
    f_end = file_idx * 100 // total_files
    span = f_end - f_start
    third = span // 3
    if step == 1:
        return f_start, f_start + third
    elif step == 2:
        return f_start + third, f_start + 2 * third
    else:
        return f_start + 2 * third, f_end


async def _try_edit(msg, text: str):
    """Редактирует сообщение, игнорируя ошибку 'not modified'."""
    try:
        await msg.edit_text(text)
    except Exception:
        pass


async def _simulate_progress(msg, video_name, stage, start, end, stop_evt, file_idx, total):
    """Плавно ползёт от start до end-5 пока stop_evt не выставлен."""
    cur = start
    while not stop_evt.is_set() and cur < end - 5:
        await asyncio.sleep(1.5)
        if stop_evt.is_set():
            break
        cur = min(cur + 5, end - 5)
        await _try_edit(msg, _progress_text(video_name, stage, cur, file_idx, total))


# ── Загрузка одного файла ─────────────────────────────────────────────────────

async def _download_video(video: Dict, save_path: Path, on_progress=None) -> bool:
    """Скачивает видео — приватное или публичное."""
    if "public_key" in video:
        inner_path = video.get("inner_path")
        return await _disk.download_public_file(
            video["public_key"], str(save_path), inner_path, on_progress=on_progress
        )
    else:
        return await _disk.download_file(video.get("path", ""), str(save_path), on_progress=on_progress)


# ── Основной обработчик ───────────────────────────────────────────────────────

@router.message()
async def handle_disk_link(message: Message):
    user_id = message.from_user.id
    text = message.text or ""

    logger.info(f"Сообщение от {user_id}: {text[:120]}")

    if text.startswith('/'):
        return

    if not _is_admin(user_id):
        logger.info(f"Пользователь {user_id} не администратор — игнорируем")
        return

    # Извлекаем ссылку из сообщения
    url_matches = re.findall(r'https?://\S+', text)
    if not url_matches:
        return

    url = url_matches[0].rstrip(')')  # убираем случайную )
    if not _is_yandex_disk_url(url):
        logger.info(f"Не ссылка на Яндекс.Диск: {url}")
        return

    logger.info(f"Обрабатываю ссылку: {url}")

    status_msg = await message.answer("🔍 Обрабатываю ссылку…")
    TEMP_DIR.mkdir(exist_ok=True)

    try:
        videos = await _resolve_videos(url, status_msg)
    except Exception as e:
        logger.exception("Ошибка при определении списка видео")
        await status_msg.edit_text(f"❌ Ошибка:\n<code>{e}</code>")
        return

    if videos is None:
        return  # статус уже обновлён внутри _resolve_videos

    if not videos:
        await status_msg.edit_text("❌ Видеофайлы не найдены.\nПроверьте ссылку.")
        return

    # 1. Редактируем первое сообщение → список найденных файлов
    await status_msg.edit_text(_file_list_text(videos))

    # 2. Новое сообщение под списком → прогресс обработки
    progress_msg = await message.answer("🔄 Начинаю обработку…")

    processed = 0
    failed = 0
    total = len(videos)
    loop = asyncio.get_event_loop()

    for i, video in enumerate(videos, 1):
        video_name = video.get("name", "video")
        video_ext = Path(video_name).suffix or ".mp4"
        uid = uuid.uuid4().hex[:8]

        video_path = TEMP_DIR / f"{uid}{video_ext}"
        audio_path: Optional[str] = None
        text_path = TEMP_DIR / f"{uid}.txt"

        try:
            # ── Шаг 1: Скачивание (реальный прогресс по байтам) ──────────────
            dl_start, dl_end = _step_range(i, total, 1)
            await _try_edit(progress_msg, _progress_text(video_name, "📥 Скачиваю…", dl_start, i, total))

            last_pct: list[int] = [dl_start]
            last_edit: list[float] = [0.0]

            async def on_download(downloaded: int, total_bytes: int):
                pct = dl_start + int((dl_end - dl_start) * downloaded / total_bytes)
                rounded = (pct // 5) * 5
                now = time.time()
                if rounded != last_pct[0] and now - last_edit[0] >= 1.0:
                    last_pct[0] = rounded
                    last_edit[0] = now
                    await _try_edit(progress_msg, _progress_text(video_name, "📥 Скачиваю…", rounded, i, total))

            ok = await _download_video(video, video_path, on_progress=on_download)
            if not ok:
                failed += 1
                await message.answer(f"❌ Не удалось скачать: {video_name}")
                continue
            await _try_edit(progress_msg, _progress_text(video_name, "📥 Скачиваю…", dl_end, i, total))

            # ── Шаг 2: Конвертация (симуляция прогресса) ─────────────────────
            cv_start, cv_end = _step_range(i, total, 2)
            stop_cv = asyncio.Event()
            sim_cv = asyncio.create_task(
                _simulate_progress(progress_msg, video_name, "🎵 Конвертирую в аудио…", cv_start, cv_end, stop_cv, i, total)
            )
            audio_path = await loop.run_in_executor(_executor, _converter.video_to_audio, str(video_path))
            stop_cv.set()
            await sim_cv
            if not audio_path:
                failed += 1
                await message.answer(f"❌ Не удалось конвертировать: {video_name}")
                continue
            await _try_edit(progress_msg, _progress_text(video_name, "🎵 Конвертирую в аудио…", cv_end, i, total))

            # ── Шаг 3: Транскрибация (симуляция прогресса) ───────────────────
            tr_start, tr_end = _step_range(i, total, 3)
            stop_tr = asyncio.Event()
            sim_tr = asyncio.create_task(
                _simulate_progress(progress_msg, video_name, "📝 Транскрибирую…", tr_start, tr_end, stop_tr, i, total)
            )
            transcript = await loop.run_in_executor(
                _executor, lambda: _transcription.transcribe(audio_path, language="ru")
            )
            stop_tr.set()
            await sim_tr
            if not transcript:
                failed += 1
                await message.answer(f"❌ Не удалось транскрибировать: {video_name}")
                continue
            await _try_edit(progress_msg, _progress_text(video_name, "📝 Транскрибирую…", tr_end, i, total))

            # ── Отправляем результат ──────────────────────────────────────────
            text_path.write_text(transcript, encoding="utf-8")
            stem = Path(video_name).stem
            doc = FSInputFile(str(text_path), filename=f"{stem}.txt")
            await message.answer_document(doc, caption=f"📝 {video_name}")

            processed += 1

        except Exception as e:
            failed += 1
            logger.exception(f"Ошибка при обработке {video_name}")
            await message.answer(f"❌ Ошибка при обработке <b>{video_name}</b>")

        finally:
            # Гарантированная очистка temp-файлов
            for f in (str(video_path), audio_path, str(text_path)):
                if f:
                    try:
                        p = Path(f)
                        if p.exists():
                            p.unlink()
                    except Exception:
                        pass

        await asyncio.sleep(0.5)

    # Итог
    await progress_msg.edit_text(
        f"✅ Готово!\n\n"
        f"Обработано: {processed}\n"
        f"Ошибок: {failed}\n"
        f"Всего: {total}"
    )


# ── Определение списка видео по ссылке ───────────────────────────────────────

async def _resolve_videos(url: str, status_msg) -> Optional[List[Dict]]:
    """
    Разбирает URL и возвращает список видеофайлов.
    При ошибке обновляет status_msg и возвращает None.
    """
    is_public = '/i/' in url or 'yandex.ru/i/' in url

    if is_public:
        match = re.search(r'/i/([^/?]+)', url)
        if not match:
            await status_msg.edit_text("❌ Не удалось извлечь ключ из публичной ссылки.")
            return None

        # Яндекс API принимает полный URL как public_key
        public_key = url
        await status_msg.edit_text("🔍 Получаю информацию о ресурсе…")
        info = await _disk.get_public_resource_info(public_key)

        if not info:
            await status_msg.edit_text(
                "❌ Не удалось получить информацию.\n"
                "Проверьте ссылку и доступ к ресурсу."
            )
            return None

        resource_type = info.get("type")

        if resource_type == "file":
            name = info.get("name", "")
            if not _disk.is_video_file(name):
                await status_msg.edit_text(f"❌ Файл не является видео: <b>{name}</b>")
                return None
            return [{
                "name": name,
                "size": info.get("size", 0),
                "public_key": public_key,
                "inner_path": None,
            }]

        elif resource_type == "dir":
            await status_msg.edit_text("🔍 Ищу видео в публичной папке…")
            videos = await _disk.get_video_files_from_public_folder(public_key)
            return videos

        else:
            await status_msg.edit_text("❌ Неизвестный тип ресурса.")
            return None

    else:
        parsed_path = _disk.parse_disk_url(url)
        if not parsed_path:
            await status_msg.edit_text(
                "❌ Не удалось распознать ссылку на Яндекс.Диск.\n"
                "Отправьте корректную ссылку на папку или файл."
            )
            return None

        await status_msg.edit_text("🔍 Ищу видео файлы…")
        videos = await _disk.get_video_files_from_folder(parsed_path, recursive=True)
        return videos
