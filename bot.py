import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database import init_database, create_user


TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher ()

# ============================================================
# НАСТРОЙКИ
# ============================================================




# ============================================================
# СОЗДАЁМ БОТА
# ============================================================

dp = Dispatcher()


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
            KeyboardButton(text="👤 Профиль"),
        ],
    ],
    resize_keyboard=True,
)


# ============================================================
# КОМАНДА /START
# ============================================================

@dp.message(CommandStart())
async def start_handler(message: Message):
    user = await create_user(
        telegram_id=message.from_user.id,
        name=message.from_user.full_name,
    )

    await message.answer(
        "Привет! 👋\n\n"
        "Я помогу вам считать счета после походов "
        "в рестораны и кафе.\n\n"
        "Здесь можно будет:\n"
        "🍽 создавать посиделки\n"
        "🧾 добавлять блюда\n"
        "👥 распределять блюда между людьми\n"
        "💳 фиксировать оплату\n"
        "📷 хранить чеки\n"
        "💸 считать, кто кому сколько должен\n"
        "📚 смотреть историю прошлых походов\n\n"
        f"Рад видеть тебя, {user[2]}! 👋\n\n"
        "Выбирай действие ниже 👇",
        reply_markup=main_menu,
    )


# ============================================================
# НОВАЯ ПОСИДЕЛКА
# ============================================================

@dp.message(F.text == "🍽 Новая посиделка")
async def new_session_handler(message: Message):
    await message.answer(
        "🍽 Создаём новую посиделку!\n\n"
        "Эта функция пока находится в разработке.\n\n"
        "Скоро здесь мы добавим:\n"
        "📍 ресторан\n"
        "👥 участников\n"
        "🍔 блюда\n"
        "💰 цены\n"
        "💳 оплату\n"
        "📷 чек"
    )


# ============================================================
# ИСТОРИЯ
# ============================================================

@dp.message(F.text == "📚 История")
async def history_handler(message: Message):
    await message.answer(
        "📚 История посиделок\n\n"
        "Пока здесь пусто.\n\n"
        "После первой завершённой посиделки "
        "она появится здесь."
    )


# ============================================================
# МОИ ДОЛГИ
# ============================================================

@dp.message(F.text == "💸 Мои долги")
async def debts_handler(message: Message):
    await message.answer(
        "💸 Мои долги\n\n"
        "Пока долгов нет.\n\n"
        "После завершения посиделок здесь "
        "будет отображаться, кому и сколько "
        "ты должен."
    )


# ============================================================
# ПРОФИЛЬ
# ============================================================

@dp.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    user = message.from_user

    await message.answer(
        "👤 Твой профиль\n\n"
        f"Имя: {user.full_name}\n"
        f"Telegram ID: {user.id}\n\n"
        "Позже здесь появится статистика:\n"
        "🍽 количество посиделок\n"
        "💰 сколько потрачено\n"
        "💸 сколько должен\n"
        "💵 сколько должны тебе"
    )


# ============================================================
# ЗАПУСК
# ============================================================

async def main():
    await init_database()

    bot = Bot(token=TOKEN)

    try:
        print("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())