"""
Модуль для работы с Yandex Disk API
"""
import aiohttp
import re
from typing import Optional, List, Dict
from urllib.parse import unquote, urlparse, parse_qs


class YandexDisk:
    """Класс для работы с Яндекс.Диском"""
    
    API_BASE_URL = "https://cloud-api.yandex.net/v1/disk"
    
    # Расширения видео файлов
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg'}
    
    def __init__(self, access_token: str):
        """
        Инициализация клиента Яндекс.Диска
        
        Args:
            access_token: OAuth токен пользователя
        """
        self.access_token = access_token
        self.headers = {"Authorization": f"OAuth {access_token}"}
    
    @staticmethod
    def parse_disk_url(url: str) -> Optional[str]:
        """
        Парсит ссылку на Яндекс.Диск и извлекает путь к папке/файлу
        
        Args:
            url: Ссылка на Яндекс.Диск
        
        Returns:
            Путь к ресурсу на диске или None
        """
        # Паттерны для разных форматов ссылок Яндекс.Диска
        patterns = [
            r'yandex\.ru/disk/([^/?]+)',  # https://disk.yandex.ru/disk/folder_name
            r'yandex\.ru/d/([^/?]+)',     # https://disk.yandex.ru/d/folder_id
            r'yandex\.ru/i/([^/?]+)',     # https://disk.yandex.ru/i/public_key (публичная ссылка)
            r'yandex\.ru/client/disk\?.*path=([^&]+)',  # https://disk.yandex.ru/client/disk?path=...
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                path = match.group(1)
                # Декодируем URL-encoded путь
                path = unquote(path)
                # Если путь начинается с /, убираем его
                if path.startswith('/'):
                    path = path[1:]
                return path
        
        # Если не нашли по паттернам, пробуем извлечь из query параметров
        try:
            parsed = urlparse(url)
            if 'path' in parse_qs(parsed.query):
                path = parse_qs(parsed.query)['path'][0]
                return unquote(path)
        except:
            pass
        
        return None
    
    async def get_folder_contents(self, folder_path: str = "/") -> Optional[List[Dict]]:
        """
        Получает список файлов и папок в указанной директории
        
        Args:
            folder_path: Путь к папке на диске (по умолчанию корень)
        
        Returns:
            Список словарей с информацией о файлах/папках или None при ошибке
        """
        url = f"{self.API_BASE_URL}/resources"
        params = {
            "path": folder_path,
            "limit": 1000  # Максимальное количество элементов
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("_embedded", {}).get("items", [])
                    else:
                        error_text = await response.text()
                        print(f"Ошибка получения содержимого папки: {response.status} - {error_text}")
                        return None
            except Exception as e:
                print(f"Исключение при получении содержимого папки: {e}")
                return None
    
    def is_video_file(self, filename: str) -> bool:
        """
        Проверяет, является ли файл видео
        
        Args:
            filename: Имя файла
        
        Returns:
            True если файл видео, иначе False
        """
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.VIDEO_EXTENSIONS)
    
    async def get_video_files_from_folder(self, folder_path: str = "/", recursive: bool = True) -> List[Dict]:
        """
        Получает список всех видео файлов из папки (рекурсивно)
        
        Args:
            folder_path: Путь к папке на диске
            recursive: Искать рекурсивно во вложенных папках
        
        Returns:
            Список словарей с информацией о видео файлах
        """
        videos = []
        items = await self.get_folder_contents(folder_path)
        
        if not items:
            return videos
        
        for item in items:
            if item.get("type") == "file":
                # Это файл
                name = item.get("name", "")
                if self.is_video_file(name):
                    videos.append(item)
            elif item.get("type") == "dir" and recursive:
                # Это папка, рекурсивно ищем в ней
                subfolder_path = item.get("path", "")
                sub_videos = await self.get_video_files_from_folder(subfolder_path, recursive=True)
                videos.extend(sub_videos)
        
        return videos
    
    async def get_download_link(self, file_path: str) -> Optional[str]:
        """
        Получает прямую ссылку для скачивания файла
        
        Args:
            file_path: Путь к файлу на диске
        
        Returns:
            URL для скачивания или None при ошибке
        """
        url = f"{self.API_BASE_URL}/resources/download"
        params = {"path": file_path}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("href")
                    else:
                        error_text = await response.text()
                        print(f"Ошибка получения ссылки на скачивание: {response.status} - {error_text}")
                        return None
            except Exception as e:
                print(f"Исключение при получении ссылки на скачивание: {e}")
                return None
    
    async def get_public_download_link(self, public_key: str) -> Optional[str]:
        """
        Получает ссылку для скачивания из публичной папки
        
        Args:
            public_key: Ключ публичной папки
        
        Returns:
            URL для скачивания или None при ошибке
        """
        url = f"{self.API_BASE_URL}/public/resources/download"
        params = {"public_key": public_key}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("href")
                    else:
                        error_text = await response.text()
                        print(f"Ошибка получения публичной ссылки: {response.status} - {error_text}")
                        return None
            except Exception as e:
                print(f"Исключение при получении публичной ссылки: {e}")
                return None
    
    async def download_file(self, file_path: str, save_path: str) -> bool:
        """
        Скачивает файл с Яндекс.Диска
        
        Args:
            file_path: Путь к файлу на диске
            save_path: Путь для сохранения файла локально
        
        Returns:
            True если успешно, False при ошибке
        """
        download_link = await self.get_download_link(file_path)
        
        if not download_link:
            return False
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(download_link) as response:
                    if response.status == 200:
                        # Создаем директорию если нужно
                        from pathlib import Path
                        save_path_obj = Path(save_path)
                        save_path_obj.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Сохраняем файл
                        with open(save_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"Ошибка скачивания файла: {response.status} - {error_text}")
                        return False
            except Exception as e:
                print(f"Исключение при скачивании файла: {e}")
                return False

