"""
Простой скрипт для получения токена Яндекс.Диска
"""
import asyncio
import aiohttp

# Данные из config.py
CLIENT_ID = "abfde16472b543eeb696ef1123ecccab"
CLIENT_SECRET = "b416c596978f493890602d39c2e46da2"
REDIRECT_URI = "https://oauth.yandex.ru/verification_code"
TOKEN_URL = "https://oauth.yandex.ru/token"

print("=" * 60)
print("Получение токена Яндекс.Диска")
print("=" * 60)
print()
print("1. Перейдите по ссылке:")
print()
print(f"https://oauth.yandex.ru/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}")
print()
print("2. Авторизуйтесь и скопируйте код верификации")
print("3. Вставьте код ниже")
print()

code = input("Введите код: ").strip()

if not code:
    print("Код не введен!")
    exit(1)

async def get_token():
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(TOKEN_URL, data=data) as response:
            if response.status == 200:
                result = await response.json()
                token = result.get("access_token")
                if token:
                    print()
                    print("=" * 60)
                    print("✅ Токен получен!")
                    print("=" * 60)
                    print()
                    print("Скопируйте этот токен в config.py:")
                    print()
                    print(f'YANDEX_DISK_TOKEN = "{token}"')
                    print()
                else:
                    print("Ошибка: токен не найден в ответе")
            else:
                error = await response.text()
                print(f"Ошибка: {response.status}")
                print(error)

asyncio.run(get_token())


