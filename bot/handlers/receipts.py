import io
from aiogram import Router, types, F, Bot, exceptions
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.manager import DatabaseManager
from services.gemini_service import GeminiService
from services.csv_service import CSVService
from aiogram.types import BufferedInputFile
from models.entities import Receipt
from config import GEMINI_API_KEY
from utils.logger import logger
from utils.helpers import escape_markdown, validate_file_size
from datetime import datetime

router = Router()
db = DatabaseManager()
gemini = GeminiService(GEMINI_API_KEY)

class ReceiptStates(StatesGroup):
    waiting_for_photo = State()

@router.message(Command("receipt"))
async def cmd_receipt(message: types.Message, state: FSMContext):
    """Вход в режим распознавания чека."""
    await state.set_state(ReceiptStates.waiting_for_photo)
    await message.answer(
        "📸 Отправьте фото чека (как фото или как файл) для распознавания.\n"
        "Или отправьте /cancel для отмены."
    )

@router.message(ReceiptStates.waiting_for_photo, F.photo | (F.document & F.document.mime_type.startswith('image/')))
async def handle_receipt_image(message: types.Message, bot: Bot, state: FSMContext):
    """Обработка фото или файла изображения чека."""
    user_id = message.from_user.id
    try:
        status_msg = await message.answer("🔍 Распознаю товары в чеке... Это может занять несколько секунд.")
    except exceptions.TelegramForbiddenError:
        logger.warning(f"Пользователь {user_id} заблокировал бота.")
        return
    
    if message.photo:
        photo = message.photo[-1]
        if not validate_file_size(photo.file_size, max_mb=5):
            await status_msg.edit_text("⚠️ Изображение слишком большое. Пожалуйста, отправьте фото размером до 5 МБ.")
            return
        file_id = photo.file_id
    else:
        if not validate_file_size(message.document.file_size, max_mb=5):
            await status_msg.edit_text("⚠️ Файл слишком большой. Пожалуйста, отправьте файл размером до 5 МБ.")
            return
        file_id = message.document.file_id

    file_info = await bot.get_file(file_id)
    
    # Скачиваем файл
    file_content = io.BytesIO()
    if file_info.file_path:
        await bot.download_file(file_info.file_path, file_content)
    else:
        logger.error(f"Не удалось скачать файл {file_info.file_id}")
        await message.answer("Произошла ошибка при загрузке файла")
        return

    # Анализируем через Gemini Vision
    data = await gemini.analyze_receipt(file_content.getvalue())
    
    if data:
        # Сохраняем в БД
        receipt = Receipt(
            user_id=message.from_user.id,
            items=[], # Модели элементов можно добавить при необходимости
            total_sum=data.get("total_sum", 0.0),
            date=datetime.now(), # Можно парсить из data["date"], если нужно
            raw_json=str(data)
        )
        await db.save_receipt(receipt)
        
        # Формируем ответ
        response_text = "✅ *Чек распознан!*\n\n"
        items_list = data.get("items", [])
        for i, item in enumerate(items_list, 1):
            name = escape_markdown(str(item.get('name', 'Неизвестно')))
            total = escape_markdown(str(item.get('total', '0')))
            response_text += f"{i}. {name} — {total} руб.\n"
            
        total_sum = escape_markdown(str(data.get('total_sum', '0')))
        response_text += f"\n💰 *Итого: {total_sum} руб.*"
        
        # Генерируем CSV
        csv_file = CSVService.generate_receipt_csv(items_list)
        input_file = BufferedInputFile(csv_file.read(), filename=f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        await status_msg.delete()
        await message.answer(response_text)
        await message.answer_document(
            input_file,
            caption="📊 Полный список в формате CSV"
        )
        await state.clear()
    else:
        await status_msg.edit_text("❌ Не удалось распознать чек. Попробуйте сделать более четкое фото или нажмите /cancel.")

@router.message(ReceiptStates.waiting_for_photo)
async def handle_wrong_receipt_input(message: types.Message):
    """Если прислали не фото в режиме чека."""
    await message.answer("Пожалуйста, отправьте фото чека (как изображение или файл) или команду /cancel.")
