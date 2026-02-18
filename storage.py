"""
Простое хранилище для токенов пользователей
В продакшене лучше использовать БД (SQLite, PostgreSQL и т.д.)
"""
from typing import Dict, Optional

# Хранилище токенов: user_id -> access_token
user_tokens: Dict[int, str] = {}


def save_token(user_id: int, access_token: str):
    """Сохраняет токен пользователя"""
    user_tokens[user_id] = access_token


def get_token(user_id: int) -> Optional[str]:
    """Получает токен пользователя"""
    return user_tokens.get(user_id)


def has_token(user_id: int) -> bool:
    """Проверяет, есть ли токен у пользователя"""
    return user_id in user_tokens


def remove_token(user_id: int):
    """Удаляет токен пользователя"""
    if user_id in user_tokens:
        del user_tokens[user_id]

