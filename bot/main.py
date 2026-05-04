import os
import sys
import asyncio

# Добавляем корневую директорию в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import TELEGRAM_TOKEN, DEEPGRAM_API_KEY, GEMINI_API_KEY
from database.manager import DatabaseManager
from services.deepgram_service import DeepgramService
from services.gemini_service import GeminiService
from utils.logger import logger

# Инициализация зависимостей
db = DatabaseManager()
deepgram = DeepgramService(DEEPGRAM_API_KEY)
gemini = GeminiService(GEMINI_API_KEY)

async def main():
    """Точка входа в приложение."""
    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров (импортируем здесь, чтобы избежать круговых импортов)
    from bot.handlers.common import router as common_router
    from bot.handlers.shopping import router as shopping_router
    from bot.handlers.receipts import router as receipt_router

    dp.include_router(common_router)
    dp.include_router(shopping_router)
    dp.include_router(receipt_router)

    # Инициализация БД
    await db.init_db()

    logger.info("Бот запущен и готов к приему сообщений...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
