"""
Обмен кода на токен Яндекс.Диска
"""
import asyncio
import aiohttp

# Данные из config.py
CLIENT_ID = "abfde16472b543eeb696ef1123ecccab"
CLIENT_SECRET = "b416c596978f493890602d39c2e46da2"
TOKEN_URL = "https://oauth.yandex.ru/token"

# Код верификации
CODE = "dd6ogac5pdnel6z4"

async def get_token():
    data = {
        "grant_type": "authorization_code",
        "code": CODE,
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
                    print("=" * 60)
                    print("Токен успешно получен!")
                    print("=" * 60)
                    print()
                    print("Ваш токен:")
                    print(token)
                    print()
                    print("Скопируйте этот токен и вставьте в config.py:")
                    print(f'YANDEX_DISK_TOKEN = "{token}"')
                    print()
                    return token
                else:
                    print("Ошибка: токен не найден в ответе")
                    print(await response.json())
            else:
                error = await response.text()
                print(f"Ошибка: {response.status}")
                print(error)

asyncio.run(get_token())

