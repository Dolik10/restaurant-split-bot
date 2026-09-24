import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from database import (
    init_database,
    create_user,
    get_user,
    get_all_restaurants,
    get_all_users,
    get_all_sessions,
    get_restaurant_by_name,
    create_session,
    add_session_member,
)


TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()


# ============================================================
# ТЕКУЩИЕ ПОСИДЕЛКИ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

active_sessions = {}
selected_participants = {}
active_item = {}


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🍽 Новая посиделка"),
            KeyboardButton(text="📚 История"),
        ],
        [
            KeyboardButton(text="💸 Мои долги"),
            KeyboardButton(text="🏪 Рестораны"),
        ],
        [
            KeyboardButton(text="👥 Друзья"),
            KeyboardButton(text="👤 Профиль"),
        ],
    ],
    resize_keyboard=True,
)


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def start_handler(message: Message):

    user = await create_user(
        telegram_id=message.from_user.id,
        name=message.from_user.full_name,
        username=message.from_user.username,
    )

    name = user[2]

    await message.answer(
        f"👋 Привет, {name}!\n\n"
        "Это наш бот для ресторанных счетов.\n\n"
        "Он поможет нам:\n\n"
        "🍽 записывать наши посиделки\n"
        "🍔 сохранять, кто что заказывал\n"
        "💰 учитывать стоимость каждой позиции\n"
        "💳 фиксировать, кто оплатил счёт\n"
        "📷 хранить фотографии чеков\n"
        "🧮 рассчитывать, кто кому сколько должен\n"
        "📚 сохранять историю прошлых походов\n\n"
        "Все данные сохраняются, поэтому к старым "
        "посиделкам можно вернуться в любой момент.\n\n"
        "👇 Выбирай нужное действие:",
        reply_markup=main_menu,
    )


# ============================================================
# НОВАЯ ПОСИДЕЛКА
# ============================================================

@dp.message(F.text == "🍽 Новая посиделка")
async def new_session_handler(message: Message):

    restaurants = await get_all_restaurants()

    keyboard = []

    for restaurant in restaurants:
        restaurant_name = restaurant[1]

        keyboard.append(
            [
                KeyboardButton(
                    text=f"🏪 {restaurant_name}"
                )
            ]
        )

    keyboard.append(
        [
            KeyboardButton(text="➕ Другое место")
        ]
    )

    keyboard.append(
        [
            KeyboardButton(text="🔙 Главное меню")
        ]
    )

    menu = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

    await message.answer(
        "🍽 Новая посиделка\n\n"
        "Выбери ресторан, в котором вы сейчас сидите:",
        reply_markup=menu,
    )
# ============================================================
# ВЫБОР / ОТМЕНА УЧАСТНИКА
# ============================================================

@dp.message(F.text.startswith("👤 "))
async def participant_selected_handler(message: Message):

    owner_id = message.from_user.id

    session_id = active_sessions.get(owner_id)

    if not session_id:
        await message.answer(
            "❌ Активная посиделка не найдена.",
            reply_markup=main_menu,
        )
        return

    participant_name = message.text[2:].strip()

    users = await get_all_users()

    participant = None

    for user in users:
        if user[2] == participant_name:
            participant = user
            break

    if not participant:
        await message.answer(
            "❌ Не удалось найти этого пользователя."
        )
        return

    participant_id = participant[0]

    participants = selected_participants.setdefault(
        owner_id,
        set(),
    )

    if participant_id in participants:

        participants.remove(participant_id)

        await message.answer(
            f"❌ {participant_name} убран из посиделки."
        )

    else:

        participants.add(participant_id)

        await message.answer(
            f"✅ {participant_name} добавлен в посиделку."
        )
# ============================================================
# ЗАВЕРШЕНИЕ ВЫБОРА УЧАСТНИКОВ
# ============================================================

@dp.message(F.text == "✅ Готово")
async def participants_done_handler(message: Message):

    user_id = message.from_user.id

    session_id = active_sessions.get(user_id)

    if not session_id:
        await message.answer(
            "❌ Активная посиделка не найдена.",
            reply_markup=main_menu,
        )
        return

    participants = selected_participants.get(
        user_id,
        set(),
    )

    users = await get_all_users()

    names = []

    for participant in users:
        if participant[0] in participants:
            names.append(participant[2])

    text = (
        "👥 Участники посиделки\n\n"
    )

    for name in names:
        text += f"• {name}\n"

    text += (
        "\n"
        "✅ Состав участников сохранён.\n\n"
        "Следующим шагом добавим блюда и цены."
    )

    dishes_menu = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить блюдо"),
                KeyboardButton(text="📋 Все позиции"),
            ],
            [
                KeyboardButton(text="✅ Завершить посиделку"),
            ],
            [
                KeyboardButton(text="🔙 Главное меню"),
            ],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        text
        + "\n\n"
        + "🍽 Теперь добавим блюда и напитки.",
        reply_markup=dishes_menu,
    )
# ============================================================
# ДОБАВЛЕНИЕ БЛЮДА
# ============================================================

@dp.message(F.text == "➕ Добавить блюдо")
async def add_dish_handler(message: Message):

    if message.from_user.id not in active_sessions:
        await message.answer(
            "❌ Активная посиделка не найдена.",
            reply_markup=main_menu,
        )
        return

    await message.answer(
        "🍽 Добавляем позицию.\n\n"
        "Напиши название блюда или напитка.\n\n"
        "Например:\n"
        "Хачапури по-аджарски\n"
        "Кола\n"
        "Стейк"
    )
# ============================================================
# ПОЛУЧЕНИЕ НАЗВАНИЯ БЛЮДА
# ============================================================

@dp.message(
    F.text,
    lambda message: (
        message.from_user.id in active_sessions
        and message.from_user.id not in active_item
        and message.text not in [
            "➕ Добавить блюдо",
            "📋 Все позиции",
            "✅ Завершить посиделку",
            "🔙 Главное меню",
        ]
    )
)
async def dish_name_handler(message: Message):

    user_id = message.from_user.id

    active_item[user_id] = {
        "name": message.text.strip()
    }

    await message.answer(
        f"🍽 Позиция: {message.text.strip()}\n\n"
        "💰 Теперь напиши её стоимость в динарах.\n\n"
        "Например:\n"
        "850\n"
        "1250.50"
    )
    # ============================================================
# ПОЛУЧЕНИЕ ЦЕНЫ БЛЮДА
# ============================================================

@dp.message(
    F.text,
    lambda message: (
        message.from_user.id in active_item
        and "name" in active_item[message.from_user.id]
    )
)
async def dish_price_handler(message: Message):

    user_id = message.from_user.id

    try:
        price = float(
            message.text.replace(",", ".").strip()
        )

        if price <= 0:
            raise ValueError

    except ValueError:
        await message.answer(
            "❌ Не понял цену.\n\n"
            "Напиши только число, например:\n"
            "850\n"
            "1250.50"
        )
        return

    active_item[user_id]["price"] = price

    dish_name = active_item[user_id]["name"]

    await message.answer(
        f"🍽 {dish_name}\n"
        f"💰 Цена: {price:.2f} RSD\n\n"
        "👥 Теперь выбери, кто ел или пил эту позицию."
    )
# ============================================================
# РЕСТОРАНЫ
# ============================================================
# ============================================================
# ВЫБОР РЕСТОРАНА ДЛЯ НОВОЙ ПОСИДЕЛКИ
# ============================================================

@dp.message(F.text.startswith("🏪 "))
async def restaurant_selected_handler(message: Message):

    restaurant_name = message.text[2:].strip()

    restaurant = await get_restaurant_by_name(
        restaurant_name
    )

    if not restaurant:
        await message.answer(
            "❌ Не удалось найти этот ресторан.\n\n"
            "Попробуй выбрать его ещё раз."
        )
        return

    user = await get_user(
        message.from_user.id
    )

    if not user:
        user = await create_user(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            username=message.from_user.username,
        )

    user_id = user[0]

    session_id = await create_session(
        restaurant_id=restaurant[0],
        created_by=user_id,
        currency="RSD",
    )

    await add_session_member(
        session_id=session_id,
        user_id=user_id,
    )

    active_sessions[message.from_user.id] = session_id
    selected_participants[message.from_user.id] = {
        user_id
    }

    users = await get_all_users()

    keyboard = []

    for participant in users:
        participant_id = participant[0]
        participant_name = participant[2]

        if participant_id == user_id:
            continue

        keyboard.append(
            [
                KeyboardButton(
                    text=f"👤 {participant_name}"
                )
            ]
        )

    keyboard.append(
        [
            KeyboardButton(
                text="✅ Готово"
            )
        ]
    )

    keyboard.append(
        [
            KeyboardButton(
                text="🔙 Главное меню"
            )
        ]
    )

    participants_menu = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

    await message.answer(
        f"🍽 Посиделка создана!\n\n"
        f"🏪 {restaurant[1]}\n"
        f"📅 Сегодня\n\n"
        "👥 Теперь выбери всех, кто сидит с тобой.\n\n"
        "Нажимай на имена. Когда закончишь — "
        "нажми «✅ Готово».",
        reply_markup=participants_menu,
    )
@dp.message(F.text == "🏪 Рестораны")
async def restaurants_handler(message: Message):

    restaurants = await get_all_restaurants()

    text = "🏪 Наши рестораны\n\n"

    if restaurants:
        for restaurant in restaurants:
            text += f"• {restaurant[1]}\n"
    else:
        text += "Пока нет сохранённых ресторанов.\n"

    text += (
        "\n"
        "Все посиделки одного ресторана "
        "будут храниться вместе."
    )

    await message.answer(
        text,
        reply_markup=main_menu,
    )


# ============================================================
# ИСТОРИЯ
# ============================================================

@dp.message(F.text == "📚 История")
async def history_handler(message: Message):

    sessions = await get_all_sessions()

    if not sessions:
        await message.answer(
            "📚 История пока пустая.\n\n"
            "Создай первую посиделку, "
            "и она появится здесь.",
            reply_markup=main_menu,
        )
        return

    text = "📚 История посиделок\n\n"

    for session in sessions:
        session_id = session[0]
        restaurant_name = session[1]
        date = session[2]
        currency = session[3]

        text += (
            f"🍽 #{session_id} — {restaurant_name}\n"
            f"📅 {date}\n"
            f"💱 {currency}\n\n"
        )

    await message.answer(
        text,
        reply_markup=main_menu,
    )


# ============================================================
# МОИ ДОЛГИ
# ============================================================

@dp.message(F.text == "💸 Мои долги")
async def debts_handler(message: Message):

    await message.answer(
        "💸 Мои долги\n\n"
        "Пока здесь пусто.\n\n"
        "Когда появятся реальные счета, "
        "здесь будет показано:\n\n"
        "➡️ кому ты должен\n"
        "➡️ кто должен тебе\n"
        "➡️ сколько нужно перевести.",
        reply_markup=main_menu,
    )


# ============================================================
# ДРУЗЬЯ
# ============================================================

@dp.message(F.text == "👥 Друзья")
async def friends_handler(message: Message):

    users = await get_all_users()

    text = "👥 Наша компания\n\n"

    if not users:
        text += "Пока никто не зарегистрирован."
    else:
        for user in users:
            name = user[2]

            if user[3]:
                username = f"@{user[3]}"
            else:
                username = "username не указан"

            text += (
                f"👤 {name}\n"
                f"   {username}\n\n"
            )

    await message.answer(
        text,
        reply_markup=main_menu,
    )


# ============================================================
# ПРОФИЛЬ
# ============================================================

@dp.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):

    user = await create_user(
        telegram_id=message.from_user.id,
        name=message.from_user.full_name,
        username=message.from_user.username,
    )

    name = user[2]
    username = user[3]

    if username:
        username_text = f"@{username}"
    else:
        username_text = "не указан"

    await message.answer(
        "👤 Твой профиль\n\n"
        f"Имя: {name}\n"
        f"Username: {username_text}\n\n"
        "Профиль используется для "
        "расчёта ресторанных счетов.",
        reply_markup=main_menu,
    )


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

@dp.message(F.text == "🔙 Главное меню")
async def back_to_main_menu(message: Message):

    await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu,
    )


# ============================================================
# НЕИЗВЕСТНОЕ СООБЩЕНИЕ
# ============================================================

@dp.message()
async def unknown_message_handler(message: Message):

    await message.answer(
        "Я пока не знаю, что делать с этим сообщением 😅\n\n"
        "Используй кнопки меню 👇",
        reply_markup=main_menu,
    )


# ============================================================
# ЗАПУСК
# ============================================================

async def main():

    await init_database()

    if not TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN. "
            "Проверь секрет Codespaces."
        )

    bot = Bot(token=TOKEN)

    try:
        print("Бот запущен!")

        await dp.start_polling(bot)

    finally:
        await bot.session.close()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    asyncio.run(main())