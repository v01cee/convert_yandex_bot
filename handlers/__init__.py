from aiogram import Router
from .start import router as start_router
from .disk_handler import router as disk_handler_router

# Создание главного роутера
router = Router()

# Подключение всех роутеров
# Порядок важен: сначала обработчик ссылок, потом команды
router.include_router(start_router)  # Команды /start и /help (должны быть первыми!)
router.include_router(disk_handler_router)  # Обрабатывает ссылки на Яндекс.Диск

