# Токен бота (получите у @BotFather в Telegram)
BOT_TOKEN = "8261154115:AAF3NzxCPtZ1aug3HXaIz_78Ixl01QlgSLE"

# Токен Яндекс.Диска админа (OAuth токен)
# Получите его через OAuth или через https://oauth.yandex.ru/
YANDEX_DISK_TOKEN = "y0__xDb7UQYkfg9IM-10roWfnoGZKDOa4XYme5MsDGhVEOfYdQ"

# ID администраторов бота (список Telegram user_id)
# Узнать свой ID можно у бота @userinfobot
ADMIN_IDS = [948113358]

# Yandex OAuth credentials (для получения токена, если нужно)
YANDEX_CLIENT_ID = "abfde16472b543eeb696ef1123ecccab"
YANDEX_CLIENT_SECRET = "b416c596978f493890602d39c2e46da2"
YANDEX_REDIRECT_URI = "https://oauth.yandex.ru/verification_code"

# Yandex OAuth URLs
YANDEX_OAUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_API_URL = "https://api-yandex.cloud/v1"

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    raise ValueError("BOT_TOKEN не установлен. Укажите токен бота в config.py")

if not YANDEX_DISK_TOKEN or YANDEX_DISK_TOKEN == "YOUR_YANDEX_DISK_TOKEN_HERE":
    raise ValueError("YANDEX_DISK_TOKEN не установлен. Укажите токен Яндекс.Диска в config.py")

