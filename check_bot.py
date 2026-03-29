import os
import asyncio
from aiogram import Bot

async def check():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        print("❌ Токен не найден в переменных окружения")
        return
    
    print(f"✅ Токен найден, длина: {len(token)} символов")
    print(f"Начало токена: {token[:10]}...")
    
    bot = Bot(token=token)
    
    try:
        me = await bot.get_me()
        print(f"\n✅ Бот успешно подключён!")
        print(f"   ID бота: {me.id}")
        print(f"   Username: @{me.username}")
        print(f"   Имя: {me.full_name}")
        print(f"\n👉 Это тот бот, который отвечает на твой токен")
    except Exception as e:
        print(f"\n❌ Ошибка подключения: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check())