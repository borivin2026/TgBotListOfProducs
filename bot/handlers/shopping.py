import io
from aiogram import Router, types, F, Bot, exceptions
from aiogram.types import BufferedInputFile, Voice
from database.manager import DatabaseManager
from services.deepgram_service import DeepgramService
from services.gemini_service import GeminiService
from services.csv_service import CSVService
from config import DEEPGRAM_API_KEY, GEMINI_API_KEY
from utils.logger import logger
from utils.helpers import escape_markdown, validate_file_size

router = Router()
db = DatabaseManager()
deepgram = DeepgramService(DEEPGRAM_API_KEY)
gemini = GeminiService(GEMINI_API_KEY)

async def process_list_update(message: types.Message, text: str):
    """Общая логика обновления списка (для голоса и текста)."""
    user_id = message.from_user.id
    
    # 1. Получаем текущий активный список -
    active_list = await db.get_active_list(user_id)
    if not active_list:
        list_id = await db.create_shopping_list(user_id)
        current_items = []
    else:
        list_id = active_list.id
        current_items = active_list.items

    # 2. Обрабатываем через Gemini
    try:
        status_msg = await message.answer("⏳ Анализирую список...")
    except exceptions.TelegramForbiddenError:
        logger.warning(f"Пользователь {user_id} заблокировал бота.")
        return

    try:
        updated_items = await gemini.parse_shopping_list(text, current_items)
        
        if not updated_items:
            await status_msg.edit_text("🤷‍♂️ Мне не удалось найти товары в вашем сообщении. Попробуйте сформулировать иначе.")
            return

        # 3. Сохраняем в БД
        await db.update_list_items(list_id, updated_items)
        
        # 4. Формируем ответ
        response_text = "📋 *Ваш список покупок:*\n\n"
        for item in updated_items:
            name = escape_markdown(item.name)
            qty = escape_markdown(item.quantity)
            response_text += f"• {name} — {qty}\n"
        
        # 5. Генерируем CSV
        csv_file = CSVService.generate_shopping_list_csv(updated_items)
        input_file = BufferedInputFile(csv_file.read(), filename="shopping_list.csv")
        
        await status_msg.delete()
        await message.answer_document(
            input_file,
            caption=response_text,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="✅ Принять как окончательный", callback_data=f"finalize_{list_id}")]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка: {e}", exc_info=True)
        error_msg = "❌ Произошла ошибка при обработке списка."
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            error_msg += "\n\nПревышены лимиты запросов (Quota exceeded). Пожалуйста, подождите минуту и попробуйте снова."
        else:
            error_msg += "\n\nПопробуйте повторить запрос позже."
        
        await status_msg.edit_text(error_msg)

@router.message(F.voice)
async def handle_voice(message: types.Message, bot: Bot):
    """Обработка голосовых сообщений."""
    voice = message.voice
    
    # Проверка длительности (макс 5 минут)
    if voice.duration > 300:
        await message.answer("⚠️ Голосовое сообщение слишком длинное. Пожалуйста, запишите сообщение длительностью не более 5 минут.")
        return
        
    # Проверка размера (макс 2МБ для голоса)
    if not validate_file_size(voice.file_size, max_mb=12):
        await message.answer("⚠️ Голосовое сообщение слишком большое. Пожалуйста, запишите более короткое сообщение (до 12 МБ).")
        return

    file_info = await bot.get_file(voice.file_id)
    
    # Скачиваем файл в память
    file_content = io.BytesIO()
    await bot.download_file(file_info.file_path, file_content)
    
    # Распознаем через Deepgram
    text = await deepgram.transcribe_audio(file_content.getvalue())
    
    if text:
        await process_list_update(message, text)
    else:
        await message.answer("❌ Не удалось распознать голос. Попробуйте еще раз или напишите текстом.")

@router.message(F.text & ~F.text.startswith('/'))
async def handle_text(message: types.Message):
    """Обработка текстовых сообщений (уточнения)."""
    await process_list_update(message, message.text)

@router.callback_query(F.data.startswith("finalize_"))
async def finalize_list_callback(callback: types.CallbackQuery):
    """Завершение списка по кнопке."""
    list_id = int(callback.data.split("_")[1])
    await db.finalize_list(list_id)
    await callback.answer("Список сохранен как окончательный!")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("🎯 Список покупок закрыт. Для нового списка просто отправьте голос или текст.")
