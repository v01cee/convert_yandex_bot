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
        self.access_token = access_token
        self.headers = {"Authorization": f"OAuth {access_token}"}

    @staticmethod
    def parse_disk_url(url: str) -> Optional[str]:
        """
        Парсит ссылку на Яндекс.Диск и извлекает путь к папке/файлу.
        Возвращает путь или None.
        """
        patterns = [
            r'yandex\.ru/disk/([^/?]+)',
            r'yandex\.ru/d/([^/?]+)',
            r'yandex\.ru/i/([^/?]+)',
            r'yandex\.ru/client/disk\?.*path=([^&]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                path = unquote(match.group(1))
                if path.startswith('/'):
                    path = path[1:]
                return path

        # Fallback: query param ?path=
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            if 'path' in qs:
                return unquote(qs['path'][0])
        except Exception:
            pass

        return None

    def is_video_file(self, filename: str) -> bool:
        """Возвращает True если файл является видео."""
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.VIDEO_EXTENSIONS)

    # ── Приватные папки / файлы ──────────────────────────────────────────────

    async def get_folder_contents(self, folder_path: str = "/") -> Optional[List[Dict]]:
        """Получает список файлов и папок в указанной директории."""
        url = f"{self.API_BASE_URL}/resources"
        params = {"path": folder_path, "limit": 1000}

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

    async def get_video_files_from_folder(self, folder_path: str = "/", recursive: bool = True) -> List[Dict]:
        """Рекурсивно собирает видеофайлы из приватной папки."""
        videos = []
        items = await self.get_folder_contents(folder_path)

        if not items:
            return videos

        for item in items:
            if item.get("type") == "file":
                if self.is_video_file(item.get("name", "")):
                    videos.append(item)
            elif item.get("type") == "dir" and recursive:
                subfolder_path = item.get("path", "")
                sub_videos = await self.get_video_files_from_folder(subfolder_path, recursive=True)
                videos.extend(sub_videos)

        return videos

    async def get_download_link(self, file_path: str) -> Optional[str]:
        """Возвращает прямую ссылку для скачивания приватного файла."""
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

    async def download_file(self, file_path: str, save_path: str, on_progress=None) -> bool:
        """Скачивает приватный файл с Яндекс.Диска."""
        download_link = await self.get_download_link(file_path)
        if not download_link:
            return False

        timeout = aiohttp.ClientTimeout(total=3600, connect=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(download_link) as response:
                    if response.status == 200:
                        from pathlib import Path
                        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                        total = int(response.headers.get('Content-Length', 0))
                        downloaded = 0
                        with open(save_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(65536):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if on_progress and total:
                                    await on_progress(downloaded, total)
                        return True
                    else:
                        error_text = await response.text()
                        print(f"Ошибка скачивания файла: {response.status} - {error_text}")
                        return False
            except Exception as e:
                print(f"Исключение при скачивании файла: {e}")
                return False

    # ── Публичные папки / файлы ──────────────────────────────────────────────

    async def get_public_resource_info(self, public_key: str) -> Optional[Dict]:
        """Получает метаданные публичного ресурса (файл или папка)."""
        url = f"{self.API_BASE_URL}/public/resources"
        params = {"public_key": public_key, "limit": 1}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"Ошибка получения информации о публичном ресурсе: {response.status} - {error_text}")
                        return None
            except Exception as e:
                print(f"Исключение при получении информации о публичном ресурсе: {e}")
                return None

    async def get_public_folder_contents(self, public_key: str, path: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Получает список файлов и подпапок внутри публичного ресурса.

        Args:
            public_key: ключ из ссылки /i/...
            path: путь к подпапке внутри публичного ресурса (для рекурсии)
        """
        url = f"{self.API_BASE_URL}/public/resources"
        params: Dict = {"public_key": public_key, "limit": 1000}
        if path:
            params["path"] = path

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("_embedded", {}).get("items", [])
                    else:
                        error_text = await response.text()
                        print(f"Ошибка получения содержимого публичной папки: {response.status} - {error_text}")
                        return None
            except Exception as e:
                print(f"Исключение при получении содержимого публичной папки: {e}")
                return None

    async def get_video_files_from_public_folder(
        self, public_key: str, path: Optional[str] = None
    ) -> List[Dict]:
        """
        Рекурсивно собирает видеофайлы из публичной папки.

        Возвращает список словарей вида:
            {"name": str, "size": int, "public_key": str, "inner_path": str}
        """
        videos: List[Dict] = []
        items = await self.get_public_folder_contents(public_key, path)

        if not items:
            return videos

        for item in items:
            if item.get("type") == "file":
                name = item.get("name", "")
                if self.is_video_file(name):
                    videos.append({
                        "name": name,
                        "size": item.get("size", 0),
                        "public_key": public_key,
                        "inner_path": item.get("path", ""),
                    })
            elif item.get("type") == "dir":
                sub_path = item.get("path", "")
                sub_videos = await self.get_video_files_from_public_folder(public_key, sub_path)
                videos.extend(sub_videos)

        return videos

    async def get_public_download_link(self, public_key: str, path: Optional[str] = None) -> Optional[str]:
        """Возвращает прямую ссылку для скачивания публичного файла/файла из публичной папки."""
        url = f"{self.API_BASE_URL}/public/resources/download"
        params: Dict = {"public_key": public_key}
        if path:
            params["path"] = path

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

    async def download_public_file(self, public_key: str, save_path: str, inner_path: Optional[str] = None, on_progress=None) -> bool:
        """Скачивает публичный файл по public_key (и опциональному inner_path внутри папки)."""
        download_link = await self.get_public_download_link(public_key, inner_path)
        if not download_link:
            return False

        timeout = aiohttp.ClientTimeout(total=3600, connect=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(download_link) as response:
                    if response.status == 200:
                        from pathlib import Path
                        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                        total = int(response.headers.get('Content-Length', 0))
                        downloaded = 0
                        with open(save_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(65536):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if on_progress and total:
                                    await on_progress(downloaded, total)
                        return True
                    else:
                        error_text = await response.text()
                        print(f"Ошибка скачивания публичного файла: {response.status} - {error_text}")
                        return False
            except Exception as e:
                print(f"Исключение при скачивании публичного файла: {e}")
                return False
