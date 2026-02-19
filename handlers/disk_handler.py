from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from yandex_disk import YandexDisk
from config import YANDEX_DISK_TOKEN, ADMIN_IDS
from video_converter import VideoConverter
from transcription import TranscriptionService
from pathlib import Path
import re
import os
import asyncio

router = Router()

# Инициализация сервисов
video_converter = VideoConverter(temp_dir="temp")
transcription_service = TranscriptionService(model_size="base")


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


def is_yandex_disk_url(text: str) -> bool:
    """Проверяет, является ли текст ссылкой на Яндекс.Диск"""
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
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


@router.message()
async def handle_disk_link(message: Message):
    """
    Обработчик ссылок на Яндекс.Диск
    Извлекает видео файлы из указанной папки
    Доступно только для администраторов
    """
    import logging
    logger = logging.getLogger(__name__)
    
    user_id = message.from_user.id
    text = message.text or ""
    
    logger.info(f"Получено сообщение от {user_id}: {text[:100]}")
    
    # Пропускаем команды - их обрабатывают другие обработчики
    if text.startswith('/'):
        return
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        logger.info(f"Пользователь {user_id} не является администратором")
        return  # Игнорируем сообщения от не-админов
    
    # Извлекаем все ссылки из текста (на случай если есть префикс "Вы написали:" или другие префиксы)
    import re
    url_matches = re.findall(r'https?://[^\s\)]+', text)
    
    if not url_matches:
        logger.info("Ссылки не найдены в сообщении - игнорируем")
        return  # Молча игнорируем, если нет ссылок
    
    # Берем первую найденную ссылку
    clean_text = url_matches[0]
    logger.info(f"Извлечена ссылка: {clean_text}")
    
    # Проверяем, является ли ссылка на Яндекс.Диск
    if not is_yandex_disk_url(clean_text):
        logger.info(f"Ссылка не является ссылкой на Яндекс.Диск: {clean_text} - игнорируем")
        return  # Молча игнорируем, если это не ссылка на Яндекс.Диск
    
    # Используем чистый текст для обработки
    text = clean_text
    logger.info(f"Начинаю обработку ссылки: {text}")
    
    # Используем токен админа из конфига
    disk = YandexDisk(YANDEX_DISK_TOKEN)
    
    # Отправляем сообщение о начале обработки
    status_msg = await message.answer("🔍 Обрабатываю ссылку...")
    
    try:
        # Проверяем, является ли это публичной ссылкой (формат /i/)
        is_public_link = '/i/' in text or 'yandex.ru/i/' in text or 'disk.yandex.ru/i/' in text
        
        videos = []
        
        if is_public_link:
            # Это публичная ссылка - извлекаем ключ
            import re
            match = re.search(r'/i/([^/?]+)', text)
            if not match:
                await status_msg.edit_text(
                    "❌ Не удалось извлечь ключ из публичной ссылки.",
                    parse_mode="HTML"
                )
                return
            
            public_key = match.group(1)
            
            # Получаем информацию о публичном ресурсе
            await status_msg.edit_text("🔍 Получаю информацию о файле...", parse_mode="HTML")
            resource_info = await disk.get_public_resource_info(public_key)
            
            if not resource_info:
                await status_msg.edit_text(
                    "❌ Не удалось получить информацию о файле.\n\n"
                    "Проверьте, что ссылка корректна и файл доступен.",
                    parse_mode="HTML"
                )
                return
            
            # Проверяем, это файл или папка
            if resource_info.get("type") == "file":
                # Это одиночный файл
                name = resource_info.get("name", "")
                if disk.is_video_file(name):
                    # Создаем структуру как для файла из папки
                    videos.append({
                        "name": name,
                        "path": resource_info.get("path", ""),
                        "size": resource_info.get("size", 0),
                        "public_key": public_key  # Сохраняем для скачивания
                    })
                else:
                    await status_msg.edit_text(
                        f"❌ Файл не является видео: {name}",
                        parse_mode="HTML"
                    )
                    return
            elif resource_info.get("type") == "dir":
                # Это папка - получаем содержимое
                await status_msg.edit_text("🔍 Ищу видео файлы в папке...", parse_mode="HTML")
                # Для публичных папок нужна отдельная логика
                await status_msg.edit_text(
                    "⚠️ Публичные папки пока не поддерживаются.\n\n"
                    "Используйте ссылку на отдельный видео файл.",
                    parse_mode="HTML"
                )
                return
            else:
                await status_msg.edit_text(
                    "❌ Неизвестный тип ресурса.",
                    parse_mode="HTML"
                )
                return
        else:
            # Обычная ссылка на папку/файл
            parsed_path = disk.parse_disk_url(text)
            
            if not parsed_path:
                await status_msg.edit_text(
                    "❌ Не удалось распознать ссылку на Яндекс.Диск.\n\n"
                    "Пожалуйста, отправьте корректную ссылку на папку или файл.",
                    parse_mode="HTML"
                )
                return
            
            await status_msg.edit_text("🔍 Ищу видео файлы в папке...", parse_mode="HTML")
            # Получаем список видео файлов
            videos = await disk.get_video_files_from_folder(parsed_path, recursive=True)
        
        if not videos:
            await status_msg.edit_text(
                f"❌ Не найдено видео файлов.\n\n"
                f"Проверьте, что ссылка указывает на видео файл или папку с видео.",
                parse_mode="HTML"
            )
            return
        
        # Отправляем информацию о найденных видео
        video_list = []
        for i, video in enumerate(videos[:20], 1):  # Ограничиваем 20 файлами
            name = video.get("name", "Без имени")
            size = video.get("size", 0)
            size_mb = size / (1024 * 1024) if size else 0
            
            video_list.append(
                f"{i}. {name}\n"
                f"   Размер: {size_mb:.2f} MB"
            )
        
        result_text = (
            f"✅ Найдено видео файлов: {len(videos)}\n\n"
        )
        
        if len(videos) > 20:
            result_text += f"Показаны первые 20 из {len(videos)}:\n\n"
        
        result_text += "\n".join(video_list)
        
        if len(videos) > 20:
            result_text += f"\n\n... и еще {len(videos) - 20} файлов"
        
        await status_msg.edit_text(
            f"{result_text}\n\n🔄 Начинаю обработку видео файлов...",
            parse_mode="HTML"
        )
        
        # Обрабатываем видео файлы: скачиваем, конвертируем, транскрибируем
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        processed_count = 0
        failed_count = 0
        
        for i, video in enumerate(videos, 1):
            try:
                video_name = video.get("name", "video")
                file_path = video.get("path", "")
                
                # Обновляем статус
                await status_msg.edit_text(
                    f"{result_text}\n\n"
                    f"🔄 Обрабатываю {i}/{len(videos)}: {video_name}\n"
                    f"📥 Скачиваю видео...",
                    parse_mode="HTML"
                )
                
                # Скачиваем видео
                video_local_path = temp_dir / f"video_{i}_{Path(video_name).stem}"
                # Сохраняем с оригинальным расширением
                video_ext = Path(video_name).suffix or ".mp4"
                video_local_path = video_local_path.with_suffix(video_ext)
                
                # Проверяем, это публичная ссылка или обычная
                if "public_key" in video:
                    # Публичная ссылка - используем другой метод
                    download_link = await disk.get_public_download_link(video["public_key"])
                    if download_link:
                        # Скачиваем напрямую по ссылке
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            async with session.get(download_link) as response:
                                if response.status == 200:
                                    with open(video_local_path, 'wb') as f:
                                        async for chunk in response.content.iter_chunked(8192):
                                            f.write(chunk)
                                    success = True
                                else:
                                    success = False
                    else:
                        success = False
                else:
                    # Обычная ссылка
                    success = await disk.download_file(file_path, str(video_local_path))
                
                if not success:
                    failed_count += 1
                    await message.answer(f"❌ Не удалось скачать: {video_name}")
                    continue
                
                # Конвертируем в аудио
                await status_msg.edit_text(
                    f"{result_text}\n\n"
                    f"🔄 Обрабатываю {i}/{len(videos)}: {video_name}\n"
                    f"🎵 Конвертирую в аудио...",
                    parse_mode="HTML"
                )
                
                audio_path = video_converter.video_to_audio(str(video_local_path))
                
                if not audio_path:
                    failed_count += 1
                    await message.answer(f"❌ Не удалось конвертировать: {video_name}")
                    # Удаляем видео файл
                    video_converter.cleanup(str(video_local_path))
                    continue
                
                # Транскрибируем
                await status_msg.edit_text(
                    f"{result_text}\n\n"
                    f"🔄 Обрабатываю {i}/{len(videos)}: {video_name}\n"
                    f"📝 Транскрибирую аудио...",
                    parse_mode="HTML"
                )
                
                text = transcription_service.transcribe(audio_path, language="ru")
                
                if not text:
                    failed_count += 1
                    await message.answer(f"❌ Не удалось транскрибировать: {video_name}")
                    # Удаляем временные файлы
                    video_converter.cleanup(str(video_local_path))
                    video_converter.cleanup(audio_path)
                    continue
                
                # Сохраняем текст в файл
                text_file_path = temp_dir / f"{Path(video_name).stem}.txt"
                with open(text_file_path, "w", encoding="utf-8") as f:
                    f.write(text)
                
                # Отправляем текстовый файл
                await status_msg.edit_text(
                    f"{result_text}\n\n"
                    f"🔄 Обрабатываю {i}/{len(videos)}: {video_name}\n"
                    f"📤 Отправляю результат...",
                    parse_mode="HTML"
                )
                
                document = FSInputFile(str(text_file_path), filename=f"{Path(video_name).stem}.txt")
                await message.answer_document(
                    document,
                    caption=f"📝 Транскрибация: {video_name}"
                )
                
                processed_count += 1
                
                # Удаляем временные файлы
                video_converter.cleanup(str(video_local_path))
                video_converter.cleanup(audio_path)
                video_converter.cleanup(str(text_file_path))
                
                # Небольшая задержка между файлами
                await asyncio.sleep(1)
                
            except Exception as e:
                failed_count += 1
                await message.answer(
                    f"❌ Ошибка при обработке {video.get('name', 'файла')}:\n"
                    f"<code>{str(e)}</code>",
                    parse_mode="HTML"
                )
        
        # Финальное сообщение
        await status_msg.edit_text(
            f"✅ Обработка завершена!\n\n"
            f"Обработано: {processed_count}\n"
            f"Ошибок: {failed_count}\n"
            f"Всего файлов: {len(videos)}",
            parse_mode="HTML"
        )
    
    except Exception as e:
        await status_msg.edit_text(
            f"❌ Ошибка при обработке папки:\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Проверьте правильность ссылки и доступ к папке.",
            parse_mode="HTML"
        )

