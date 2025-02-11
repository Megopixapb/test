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
