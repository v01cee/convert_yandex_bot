"""
Тестовый скрипт для проверки работы бота
"""
import asyncio
from config import BOT_TOKEN, YANDEX_DISK_TOKEN, ADMIN_IDS
from yandex_disk import YandexDisk

async def test():
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ БОТА")
    print("=" * 60)
    print()
    
    # Проверка конфигурации
    print("1. Проверка конфигурации...")
    print(f"   BOT_TOKEN: {'OK' if BOT_TOKEN and BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'NOT SET'}")
    print(f"   YANDEX_DISK_TOKEN: {'OK' if YANDEX_DISK_TOKEN and YANDEX_DISK_TOKEN != 'YOUR_YANDEX_DISK_TOKEN_HERE' else 'NOT SET'}")
    print(f"   ADMIN_IDS: {ADMIN_IDS}")
    print()
    
    # Проверка импортов
    print("2. Проверка импортов...")
    try:
        import whisper
        print("   OK - Whisper импортирован")
    except Exception as e:
        print(f"   ERROR - Ошибка импорта Whisper: {e}")
    
    try:
        from video_converter import VideoConverter
        print("   OK - VideoConverter импортирован")
    except Exception as e:
        print(f"   ERROR - Ошибка импорта VideoConverter: {e}")
    
    try:
        from transcription import TranscriptionService
        print("   OK - TranscriptionService импортирован")
    except Exception as e:
        print(f"   ERROR - Ошибка импорта TranscriptionService: {e}")
    print()
    
    # Проверка подключения к Яндекс.Диску
    print("3. Проверка подключения к Яндекс.Диску...")
    try:
        disk = YandexDisk(YANDEX_DISK_TOKEN)
        # Пробуем получить информацию о диске
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://cloud-api.yandex.net/v1/disk",
                headers={"Authorization": f"OAuth {YANDEX_DISK_TOKEN}"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   OK - Подключение успешно")
                    print(f"   Диск: {data.get('user', {}).get('display_name', 'Неизвестно')}")
                else:
                    print(f"   ERROR - Ошибка подключения: {response.status}")
    except Exception as e:
        print(f"   ERROR - Ошибка: {e}")
    print()
    
    # Проверка ffmpeg
    print("4. Проверка ffmpeg...")
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   OK - {version_line}")
        else:
            print("   ERROR - ffmpeg не найден в PATH")
    except FileNotFoundError:
        print("   ERROR - ffmpeg не установлен")
        print("   Установите ffmpeg: https://ffmpeg.org/download.html")
    except Exception as e:
        print(f"   ERROR - Ошибка: {e}")
    print()
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test())

