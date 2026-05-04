from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from database.manager import DatabaseManager
from models.entities import User as UserEntity

router = Router()
db = DatabaseManager()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Приветственное сообщение."""
    user = UserEntity(
        id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    await db.upsert_user(user)
    
    await message.answer(
        "👋 Привет! Я умный помощник для покупок.\n\n"
        "🎙 Отправь мне *голосовое сообщение* со списком товаров.\n"
        "📸 Или используй команду /receipt, чтобы оцифровать чек.\n"
        "✍️ Ты также можешь просто писать товары текстом."
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Сброс любого состояния."""
    await state.clear()
    await message.answer("❌ Действие отменено. Я снова готов принимать список покупок или чеки.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка."""
    await message.answer(
        "📝 *Как пользоваться:*\n"
        "1. Просто наговори список товаров голосом.\n"
        "2. Я пришлю таблицу и CSV-файл.\n"
        "3. Можно договорить уточнения (например, 'добавь еще хлеб').\n"
        "4. Команда /receipt — для распознавания фото чека.\n"
        "5. Команда /cancel — отмена текущего действия."
    )
