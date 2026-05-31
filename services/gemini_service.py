import os
import json
from google import genai
from google.genai import types
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.genai.errors import ServerError
from models.entities import ListItem, ReceiptItem
from utils.logger import logger

class ShoppingListResponse(BaseModel):
    items: List[ListItem]

class ReceiptResponse(BaseModel):
    items: List[ReceiptItem]
    total_sum: float
    date: str

class GeminiService:
    """Сервис для интеллектуальной обработки текста и изображений через Google Gemini (GenAI SDK)."""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # Приоритетный список моделей для фолбека
        self.model_pool = [
            'gemini-flash-lite-latest', 
            'gemini-2.0-flash',
            'gemini-1.5-flash'
        ]

    @retry(
        stop=stop_after_attempt(3), # Уменьшим количество попыток на одну модель
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(ServerError),
        reraise=True
    )
    async def _generate_content_single_attempt(self, model_id: str, **kwargs):
        """Попытка генерации контента для конкретной модели с короткими ретраями."""
        return await self.client.aio.models.generate_content(model=model_id, **kwargs)

    async def _generate_with_fallback(self, **kwargs):
        """Перебор моделей из пула при возникновении ошибок сервера (503)."""
        last_exception = None
        for model_id in self.model_pool:
            try:
                logger.info(f"Пробуем модель: {model_id}")
                return await self._generate_content_single_attempt(model_id=model_id, **kwargs)
            except ServerError as e:
                last_exception = e
                logger.warning(f"Модель {model_id} недоступна (503). Пробуем следующую...")
                continue
            except Exception as e:
                # Если ошибка не 503 (например, 400 Bad Request), то пробовать другие модели смысла мало
                logger.error(f"Критическая ошибка при вызове {model_id}: {e}")
                raise e
        
        if last_exception:
            raise last_exception
        raise Exception("Все модели из пула недоступны.")


    async def parse_shopping_list(self, text: str, current_items: List[ListItem] = []) -> List[ListItem]:
        """
        Преобразует текст в список товаров или обновляет существующий список.
        
        :param text: Новый текст от пользователя (распознанный голос или сообщение)
        :param current_items: Текущий список товаров (для учета контекста)
        :return: Обновленный список объектов ListItem
        """
        current_list_str = "\n".join([f"- {item.name}: {item.quantity}" for item in current_items])
        
        prompt = f"""
Ты — помощник по составлению списков покупок. 
Твоя задача: извлечь товары из нового сообщения и объединить их с текущим списком.

Текущий список:
{current_list_str if current_list_str else "Пусто"}

Новое сообщение:
"{text}"

Инструкции:
1. Если товар уже есть в списке и пользователь говорит "добавь еще", "купи еще" или просто называет его — обнови количество.
2. Если пользователь просит "удалить" или "убери" — удали товар.
3. Если пользователь просит "заменить" — замени товар или количество.
"""
        # Используем механизм фолбека (перебора моделей)
        response = await self._generate_with_fallback(
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ShoppingListResponse,
            )
        )
        
        # В новом SDK можно получить распарсенный объект напрямую через response.parsed
        if hasattr(response, 'parsed') and response.parsed:
            return response.parsed.items
        
        data = self._clean_json_response(response.text)
        
        new_items = []
        if data and "items" in data:
            for item_data in data["items"]:
                new_items.append(ListItem(
                    name=item_data.get("name", "Неизвестно"),
                    quantity=str(item_data.get("quantity", "1")),
                    note=item_data.get("note")
                ))
        
        return new_items if new_items else current_items

    async def analyze_receipt(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Анализирует фото чека и извлекает позиции.
        
        :param image_bytes: Байты изображения
        :return: Словарь с данными чека (items, total, date)
        """
        prompt = """
Проанализируй этот чек и извлеки информацию о ВСЕХ товарах без исключения. 
Для каждого товара определи:
1. Наименование (name)
2. Цена за единицу (price)
3. Количество (quantity)
4. Общая сумма по позиции (total)

Также найди общую сумму чека (total_sum) и дату (date).
Если какие-то данные нечеткие, постарайся распознать их максимально точно.
"""
        try:
            response = await self._generate_with_fallback(
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
                ],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=ReceiptResponse,
                )
            )
            
            if hasattr(response, 'parsed') and response.parsed:
                # Конвертируем Pydantic модель в словарь для совместимости с существующим кодом
                return response.parsed.model_dump()
            
            data = self._clean_json_response(response.text)
            return data if data else {}
        except Exception as e:
            logger.error(f"Ошибка Gemini при анализе чека: {e}", exc_info=True)
            return {}

    def _clean_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Очистка ответа от лишних символов и markdown (на случай если response_schema не отработал)."""
        try:
            # Убираем возможные ```json ... ```
            cleaned = text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception:
            logger.warning(f"Не удалось распарсить JSON из ответа Gemini: {text[:100]}...")
            return None
