from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    """
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        "Я бот на aiogram. Готов к работе!"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help
    """
    await message.answer(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "📁 Работа с Яндекс.Диском:\n"
        "Отправьте ссылку на папку Яндекс.Диска, и бот найдет все видео файлы в ней!\n\n"
        "⚠️ Доступно только для администраторов."
    )


# Убрали echo_handler - он мешал обработке ссылок
# Теперь все сообщения обрабатываются в disk_handler

