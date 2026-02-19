"""
Скрипт для получения токена Яндекс.Диска на сервере
Использование: python get_token_server.py
"""
import asyncio
import aiohttp
import sys

# Данные из config.py
CLIENT_ID = "abfde16472b543eeb696ef1123ecccab"
CLIENT_SECRET = "b416c596978f493890602d39c2e46da2"
REDIRECT_URI = "https://oauth.yandex.ru/verification_code"
TOKEN_URL = "https://oauth.yandex.ru/token"

def print_auth_url():
    """Выводит URL для авторизации"""
    auth_url = f"https://oauth.yandex.ru/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    print("=" * 70)
    print("ПОЛУЧЕНИЕ ТОКЕНА ЯНДЕКС.ДИСКА")
    print("=" * 70)
    print()
    print("1. Перейдите по ссылке для авторизации:")
    print()
    print(auth_url)
    print()
    print("2. Авторизуйтесь и скопируйте код верификации")
    print("3. Запустите скрипт с кодом:")
    print()
    print(f"   python get_token_server.py <код>")
    print()
    print("Или введите код сейчас:")

async def get_token(code):
    """Получает токен по коду"""
    if not code:
        print("Ошибка: код не указан!")
        return None
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    
    print("Обмениваю код на токен...")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(TOKEN_URL, data=data) as response:
            if response.status == 200:
                result = await response.json()
                token = result.get("access_token")
                if token:
                    print()
                    print("=" * 70)
                    print("ТОКЕН УСПЕШНО ПОЛУЧЕН!")
                    print("=" * 70)
                    print()
                    print("Ваш токен:")
                    print(token)
                    print()
                    print("Добавьте в config.py:")
                    print(f'YANDEX_DISK_TOKEN = "{token}"')
                    print()
                    print("Или экспортируйте как переменную окружения:")
                    print(f'export YANDEX_DISK_TOKEN="{token}"')
                    print()
                    return token
                else:
                    print("Ошибка: токен не найден в ответе")
                    print(await response.json())
                    return None
            else:
                error = await response.text()
                print(f"Ошибка: {response.status}")
                print(error)
                return None

async def main():
    if len(sys.argv) > 1:
        # Код передан как аргумент
        code = sys.argv[1]
        await get_token(code)
    else:
        # Показываем инструкцию и запрашиваем код
        print_auth_url()
        code = input("Введите код: ").strip()
        if code:
            await get_token(code)
        else:
            print("Код не введен!")

if __name__ == "__main__":
    asyncio.run(main())


