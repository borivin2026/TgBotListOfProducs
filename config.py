import os
from dotenv import load_dotenv

load_dotenv()

# API Ключи
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Настройки
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "bot_database.db")
LOG_FILE = os.path.join(BASE_DIR, "logs", "bot.log")

# Проверка обязательных переменных
if not all([TELEGRAM_TOKEN, DEEPGRAM_API_KEY, GEMINI_API_KEY]):
    raise ValueError("Не все переменные окружения (TELEGRAM_TOKEN, DEEPGRAM_API_KEY, GEMINI_API_KEY) заданы в .env")
