from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from yandex_oauth import YandexOAuth
from storage import save_token

router = Router()
yandex_oauth = YandexOAuth()


class AuthStates(StatesGroup):
    """Состояния для процесса авторизации"""
    waiting_for_code = State()


@router.message(Command("yandex_auth"))
async def cmd_yandex_auth(message: Message, state: FSMContext):
    """
    Обработчик команды /yandex_auth
    Генерирует ссылку для авторизации через Yandex
    """
    auth_url = yandex_oauth.get_authorization_url(state=str(message.from_user.id))
    
    await message.answer(
        "Для авторизации через Yandex перейдите по ссылке:\n\n"
        f"<a href='{auth_url}'>Авторизоваться через Yandex</a>\n\n"
        "После авторизации вы получите код. Отправьте его мне командой /code <ваш_код>",
        parse_mode="HTML"
    )
    
    await state.set_state(AuthStates.waiting_for_code)


@router.message(Command("code"))
async def cmd_code(message: Message, state: FSMContext):
    """
    Обработчик команды /code <код>
    Обменивает код авторизации на токен
    """
    current_state = await state.get_state()
    
    if current_state != AuthStates.waiting_for_code:
        await message.answer(
            "Сначала запустите процесс авторизации командой /yandex_auth"
        )
        return
    
    # Извлекаем код из команды
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer("Использование: /code <ваш_код_авторизации>")
        return
    
    code = command_parts[1].strip()
    
    await message.answer("Обмениваю код на токен...")
    
    # Получаем токен
    token_data = await yandex_oauth.get_access_token(code)
    
    if token_data and "access_token" in token_data:
        access_token = token_data["access_token"]
        
        # Получаем информацию о пользователе
        user_info = await yandex_oauth.get_user_info(access_token)
        
        if user_info:
            await message.answer(
                f"✅ Авторизация успешна!\n\n"
                f"Имя: {user_info.get('first_name', 'Не указано')}\n"
                f"Фамилия: {user_info.get('last_name', 'Не указано')}\n"
                f"Email: {user_info.get('default_email', 'Не указан')}\n"
                f"Логин: {user_info.get('login', 'Не указан')}\n\n"
                f"Access Token: <code>{access_token[:20]}...</code>",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"✅ Токен получен, но не удалось получить информацию о пользователе.\n\n"
                f"Access Token: <code>{access_token[:20]}...</code>",
                parse_mode="HTML"
            )
        
        # Сохраняем токен в хранилище
        save_token(message.from_user.id, access_token)
        
        # Сохраняем токен в состояние (для совместимости)
        await state.update_data(access_token=access_token, user_info=user_info)
    else:
        await message.answer(
            "❌ Ошибка при получении токена. Проверьте правильность кода и попробуйте снова."
        )
    
    await state.clear()

