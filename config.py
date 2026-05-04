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

# Настройки Webhook (для деплоя на PythonAnywhere)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST") # Пример: 'your-username.pythonanywhere.com'
WEBHOOK_PATH = f"/webhook/{TELEGRAM_TOKEN}"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

# Настройки веб-сервера
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# Проверка обязательных переменных
if not all([TELEGRAM_TOKEN, DEEPGRAM_API_KEY, GEMINI_API_KEY]):
    raise ValueError("Не все переменные окружения (TELEGRAM_TOKEN, DEEPGRAM_API_KEY, GEMINI_API_KEY) заданы в .env")
