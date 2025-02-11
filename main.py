import random
import string
import asyncio
from datetime import datetime
import logging
import aiomysql
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram import Router

 # Токен бота
API_TOKEN = '7596820732:AAErcpw_U-hk64LuP60tOEvrYi6l7pNDeao'
bot = Bot(token=API_TOKEN)

 # Создаем Router и Dispatcher
router = Router()
dp = Dispatcher()

 # Настройка логирования
logging.basicConfig(level=logging.INFO)

 # Список доступных игр и опций
GAMES = ["Game1", "Game2", "Game3"]
SCRIPT_OPTIONS = ["Free скрипт", "VIP скрипт"]

 # Переменная для сохранения выбранной игры
selected_game = None

 # Основное меню
def main_menu():
     keyboard = ReplyKeyboardMarkup(
         keyboard=[[KeyboardButton(text=game)] for game in GAMES],
         resize_keyboard=True
     )
     return keyboard

 # Меню выбора скрипта с кнопкой "Назад"
def script_menu():
     keyboard = ReplyKeyboardMarkup(
         keyboard=[[KeyboardButton(text=option)] for option in SCRIPT_OPTIONS] + [[KeyboardButton(text="⬅ Назад")]],
         resize_keyboard=True
     )
     return keyboard

 # Меню обновления токена
def token_refresh_menu():
     keyboard = ReplyKeyboardMarkup(
         keyboard=[[KeyboardButton(text="Обновить токен")]],
         resize_keyboard=True
     )
     return keyboard

 # Генерация уникального токена
def generate_token():
     return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

 # Подключение к базе данных
async def get_db_pool():
     return await aiomysql.create_pool(
         host='FVH1.spaceweb.ru',
         port=3306,
         user='megopixapb',
         password='Rdfhnbhf1192602Q1',
         db='megopixapb',
         charset='utf8mb4'
     )

 # Команда /start
@router.message(Command("start"))
async def start(message: types.Message):
     await message.answer("🎮 Выберите интересующую игру:", reply_markup=main_menu())

 # Обработка выбора игры
@router.message(lambda message: message.text in GAMES)
async def game_selected(message: types.Message):
     global selected_game
     selected_game = message.text
     await message.answer(f"🛠 Вы выбрали {selected_game}.\n\n📜 Выберите вариант скрипта:", reply_markup=script_menu())

 # Обработка кнопки "Назад"
@router.message(lambda message: message.text == "⬅ Назад")
async def back_to_main(message: types.Message):
     global selected_game
     selected_game = None  # Сбрасываем выбранную игру
     await message.answer("🔙 Возвращаемся в главное меню.", reply_markup=main_menu())

 # Обработка выбора скрипта
@router.message(lambda message: message.text in SCRIPT_OPTIONS)
async def script_selected(message: types.Message):
     global selected_game
     if not selected_game:
         await message.answer("❌ Сначала выберите игру.")
         return

     pool = await get_db_pool()
     if pool is None:
         await message.answer("❌ Ошибка подключения к базе данных. Попробуйте позже.")
         return

     script_type = message.text
     tg_id = message.from_user.id

     async with pool.acquire() as conn:
         async with conn.cursor() as cursor:
             # Проверяем, есть ли активный токен для этой игры
             await cursor.execute(
                 "SELECT token FROM users WHERE tg_id = %s AND game = %s AND active_token = 1",
                 (tg_id, selected_game)
             )
             row = await cursor.fetchone()

             if row:
                 active_token = row[0]
                 await message.answer(f"✅ У вас уже есть активный токен для {selected_game}: {active_token}.")
                 return

             # Генерация нового токена
             token = generate_token()
             activation_date = datetime.now()

             try:
                 await cursor.execute(
                     """
                     INSERT INTO users (tg_id, username, game, free, vip, token, activation_date, active_token)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                     """,
                     (tg_id, message.from_user.username, selected_game,
                      script_type == "Free скрипт", script_type == "VIP скрипт",
                      token, activation_date)
                 )
                 await conn.commit()
                 await message.answer(f"✅ Токен для {selected_game} создан: {token}.",
                                      reply_markup=main_menu())
             except Exception as e:
                 logging.error(f"Ошибка при записи в базу данных: {e}")
                 await message.answer("❌ Ошибка при обработке запроса. Попробуйте позже.")
# ... (предыдущий код без изменений)

# Обработка команды /check_token
@router.message(Command("check_token"))
async def check_token(message: types.Message):
    # Проверяем, что сообщение пришло из группы
    if message.chat.type == "supergroup" or message.chat.type == "group":
        # Извлекаем токен из текста сообщения
        token = message.text.split(" ")[1] if len(message.text.split(" ")) > 1 else None

        if not token:
            await message.answer("invalid")
            return

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Проверяем наличие токена
                await cursor.execute("SELECT free, vip FROM users WHERE token = %s AND active_token = 1", (token,))
                row = await cursor.fetchone()

                if not row:
                    await message.answer("invalid")
                    return

                free, vip = row
                if free:
                    await message.answer("free")
                elif vip:
                    await message.answer("vip")
                else:
                    await message.answer("invalid")

                # Удаляем токен после использования
                await cursor.execute("UPDATE users SET active_token = 0 WHERE token = %s", (token,))
                await conn.commit()
    else:
        # Если сообщение пришло не из группы, игнорируем его
        await message.answer("Команда доступна только в группе.")

# Запуск бота
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
