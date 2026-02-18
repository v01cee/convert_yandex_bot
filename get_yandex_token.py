"""
Скрипт для получения OAuth токена Яндекс.Диска
"""
import asyncio
from yandex_oauth import YandexOAuth

async def main():
    oauth = YandexOAuth()
    
    print("=" * 60)
    print("Получение токена Яндекс.Диска")
    print("=" * 60)
    print()
    print("1. Перейдите по следующей ссылке для авторизации:")
    print()
    
    auth_url = oauth.get_authorization_url()
    print(auth_url)
    print()
    print("2. После авторизации вы получите код верификации")
    print("3. Вставьте код ниже и нажмите Enter")
    print()
    
    code = input("Введите код верификации: ").strip()
    
    if not code:
        print("❌ Код не введен")
        return
    
    print()
    print("🔄 Обмениваю код на токен...")
    
    token_data = await oauth.get_access_token(code)
    
    if token_data and "access_token" in token_data:
        access_token = token_data["access_token"]
        print()
        print("=" * 60)
        print("✅ Токен успешно получен!")
        print("=" * 60)
        print()
        print("Ваш токен:")
        print(access_token)
        print()
        print("Скопируйте этот токен и вставьте в config.py:")
        print(f'YANDEX_DISK_TOKEN = "{access_token}"')
        print()
        
        # Получаем информацию о пользователе
        user_info = await oauth.get_user_info(access_token)
        if user_info:
            print("Информация о пользователе:")
            print(f"  Имя: {user_info.get('first_name', 'Не указано')}")
            print(f"  Фамилия: {user_info.get('last_name', 'Не указано')}")
            print(f"  Email: {user_info.get('default_email', 'Не указан')}")
            print(f"  Логин: {user_info.get('login', 'Не указан')}")
    else:
        print()
        print("❌ Ошибка при получении токена")
        print("Проверьте правильность кода и попробуйте снова")

if __name__ == "__main__":
    asyncio.run(main())


