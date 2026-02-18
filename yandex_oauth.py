"""
Модуль для работы с Yandex OAuth API
"""
import aiohttp
from typing import Optional, Dict
from config import (
    YANDEX_CLIENT_ID,
    YANDEX_CLIENT_SECRET,
    YANDEX_REDIRECT_URI,
    YANDEX_OAUTH_URL,
    YANDEX_TOKEN_URL
)


class YandexOAuth:
    """Класс для работы с Yandex OAuth"""
    
    def __init__(self):
        self.client_id = YANDEX_CLIENT_ID
        self.client_secret = YANDEX_CLIENT_SECRET
        self.redirect_uri = YANDEX_REDIRECT_URI
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Генерирует URL для авторизации пользователя
        
        Args:
            state: Опциональный параметр состояния для защиты от CSRF
        
        Returns:
            URL для авторизации
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{YANDEX_OAUTH_URL}?{query_string}"
    
    async def get_access_token(self, code: str) -> Optional[Dict]:
        """
        Обменивает код авторизации на access token
        
        Args:
            code: Код авторизации, полученный после редиректа
        
        Returns:
            Словарь с токеном и информацией о пользователе или None при ошибке
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(YANDEX_TOKEN_URL, data=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"Ошибка получения токена: {response.status} - {error_text}")
                        return None
            except Exception as e:
                print(f"Исключение при получении токена: {e}")
                return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Получает информацию о пользователе по access token
        
        Args:
            access_token: Access token пользователя
        
        Returns:
            Информация о пользователе или None при ошибке
        """
        headers = {"Authorization": f"OAuth {access_token}"}
        url = "https://login.yandex.ru/info"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"Ошибка получения информации о пользователе: {response.status} - {error_text}")
                        return None
            except Exception as e:
                print(f"Исключение при получении информации о пользователе: {e}")
                return None

