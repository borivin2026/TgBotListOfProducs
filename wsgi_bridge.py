import sys
import os
import asyncio
from flask import Flask, request
from aiogram import types

# Динамическое определение пути к проекту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Импорт бота и диспетчера из основного файла
from bot.main import bot, dp
from config import TELEGRAM_TOKEN

app = Flask(__name__)

# Маршрут для приема вебхуков
# На PythonAnywhere URL будет: https://your-username.pythonanywhere.com/webhook/TOKEN
@app.route(f'/webhook/{TELEGRAM_TOKEN}', methods=['POST'])
def telegram_webhook():
    if request.method == 'POST':
        try:
            # Получаем JSON от Telegram
            update_data = request.get_json()
            if not update_data:
                return 'No data', 400
                
            # Преобразуем в объект Update aiogram
            update = types.Update(**update_data)
            
            # Запускаем обработку через Dispatcher
            # asyncio.run создает временный цикл для обработки одного сообщения
            asyncio.run(dp.feed_update(bot, update))
            
            return 'OK', 200
        except Exception as e:
            app.logger.error(f"Error processing update: {e}")
            return 'Error', 500
            
    return 'Forbidden', 403

if __name__ == '__main__':
    # Для локального тестирования моста
    print("Запуск Flask-моста для Webhook...")
    app.run(host='0.0.0.0', port=8080)
