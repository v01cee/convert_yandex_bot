from aiogram import Router
from .start import router as start_router
from .disk_handler import router as disk_handler_router

# Создание главного роутера
router = Router()

# Подключение всех роутеров
# Порядок важен: сначала команды, потом обработчик ссылок
router.include_router(start_router)
router.include_router(disk_handler_router)  # Обрабатывает ссылки на Яндекс.Диск

