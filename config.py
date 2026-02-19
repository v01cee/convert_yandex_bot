import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Токен бота (получите у @BotFather в Telegram)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Токен Яндекс.Диска админа (OAuth токен)
# Получите его через OAuth или через https://oauth.yandex.ru/
YANDEX_DISK_TOKEN = os.getenv("YANDEX_DISK_TOKEN")

# ID администраторов бота (список Telegram user_id через запятую)
# Узнать свой ID можно у бота @userinfobot
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip()] if ADMIN_IDS_STR else []

# Yandex OAuth credentials (для получения токена, если нужно)
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID", "abfde16472b543eeb696ef1123ecccab")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET", "b416c596978f493890602d39c2e46da2")
YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI", "https://oauth.yandex.ru/verification_code")

# Yandex OAuth URLs
YANDEX_OAUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_API_URL = "https://api-yandex.cloud/v1"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен. Укажите токен бота в .env файле")

if not YANDEX_DISK_TOKEN:
    raise ValueError("YANDEX_DISK_TOKEN не установлен. Укажите токен Яндекс.Диска в .env файле")

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS не установлен. Укажите ID администраторов в .env файле (через запятую)")

