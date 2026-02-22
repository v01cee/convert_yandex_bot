import logging
import re
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Optional

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


def _progress_bar(current: int, total: int, width: int = 10) -> str:
    filled = int(width * current / total) if total else 0
    bar = '█' * filled + '░' * (width - filled)
    pct = int(100 * current / total) if total else 0
    return f"[{bar}] {pct}%"


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} МБ"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} КБ"
    return f"{size_bytes} Б"


def _file_list_text(videos: List[Dict]) -> str:
    lines = []
    shown = videos[:20]
    for i, v in enumerate(shown, 1):
        name = v.get("name", "?")
        size = v.get("size", 0)
        lines.append(f"{i}. {name} ({_format_size(size)})")
    text = f"🎬 Найдено видео: {len(videos)}\n\n" + "\n".join(lines)
    if len(videos) > 20:
        text += f"\n…и ещё {len(videos) - 20} файлов"
    return text


def _status_text(file_idx: int, total_files: int, step: int, video_name: str, stage: str) -> str:
    # step: 1=скачать, 2=конвертировать, 3=транскрибировать, 4=отправить
    total_steps = total_files * 3
    current_step = (file_idx - 1) * 3 + min(step, 3)
    bar = _progress_bar(current_step, total_steps)
    return (
        f"⏳ Файл {file_idx}/{total_files}\n"
        f"{bar}\n\n"
        f"📄 {video_name}\n"
        f"➤ {stage}"
    )


# ── Загрузка одного файла ─────────────────────────────────────────────────────

async def _download_video(video: Dict, save_path: Path) -> bool:
    """Скачивает видео — приватное или публичное."""
    if "public_key" in video:
        inner_path = video.get("inner_path")
        return await _disk.download_public_file(
            video["public_key"], str(save_path), inner_path
        )
    else:
        return await _disk.download_file(video.get("path", ""), str(save_path))


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

    for i, video in enumerate(videos, 1):
        video_name = video.get("name", "video")
        video_ext = Path(video_name).suffix or ".mp4"
        uid = uuid.uuid4().hex[:8]

        video_path = TEMP_DIR / f"{uid}{video_ext}"
        audio_path: Optional[str] = None
        text_path = TEMP_DIR / f"{uid}.txt"

        try:
            # Скачивание — шаг 1
            await progress_msg.edit_text(_status_text(i, total, 1, video_name, "📥 Скачиваю…"))
            ok = await _download_video(video, video_path)
            if not ok:
                failed += 1
                await message.answer(f"❌ Не удалось скачать: {video_name}")
                continue

            # Конвертация — шаг 2
            await progress_msg.edit_text(_status_text(i, total, 2, video_name, "🎵 Конвертирую в аудио…"))
            audio_path = _converter.video_to_audio(str(video_path))
            if not audio_path:
                failed += 1
                await message.answer(f"❌ Не удалось конвертировать: {video_name}")
                continue

            # Транскрибация — шаг 3
            await progress_msg.edit_text(_status_text(i, total, 3, video_name, "📝 Транскрибирую…"))
            transcript = _transcription.transcribe(audio_path, language="ru")
            if not transcript:
                failed += 1
                await message.answer(f"❌ Не удалось транскрибировать: {video_name}")
                continue

            # Сохраняем и отправляем
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
