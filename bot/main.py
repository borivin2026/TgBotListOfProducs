import os
import sys
import asyncio

# Добавляем корневую директорию в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import (
    TELEGRAM_TOKEN, DEEPGRAM_API_KEY, GEMINI_API_KEY,
    WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
)
from database.manager import DatabaseManager
from services.deepgram_service import DeepgramService
from services.gemini_service import GeminiService
from utils.logger import logger

# 1. Инициализация Bot и Dispatcher на уровне модуля (для импорта в WSGI)
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher(storage=MemoryStorage())

# Инициализация сервисов
db = DatabaseManager()
deepgram = DeepgramService(DEEPGRAM_API_KEY)
gemini = GeminiService(GEMINI_API_KEY)

async def on_startup(bot: Bot):
    """Действия при запуске."""
    await db.init_db()
    if WEBHOOK_URL:
        logger.info(f"Установка Webhook: {WEBHOOK_URL}")
        await bot.set_webhook(WEBHOOK_URL)
    else:
        logger.info("Запуск в режиме Long Polling...")

def setup_handlers(dispatcher: Dispatcher):
    """Регистрация всех роутеров."""
    from bot.handlers.common import router as common_router
    from bot.handlers.shopping import router as shopping_router
    from bot.handlers.receipts import router as receipt_router

    dispatcher.include_router(common_router)
    dispatcher.include_router(shopping_router)
    dispatcher.include_router(receipt_router)
    
    # Регистрация функции запуска
    dispatcher.startup.register(on_startup)

# Сразу настраиваем хендлеры
setup_handlers(dp)

async def main_polling():
    """Точка входа для локального запуска (Long Polling)."""
    logger.info("Бот запущен...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

def setup_webhook_app():
    """Настройка aiohttp приложения для Webhook."""
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app

if __name__ == "__main__":
    if WEBHOOK_URL:
        # Режим Webhook (aiohttp)
        logger.info(f"Запуск веб-сервера на {WEBAPP_HOST}:{WEBAPP_PORT}")
        app = setup_webhook_app()
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
    else:
        # Режим Long Polling
        asyncio.run(main_polling())
