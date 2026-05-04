import os
import asyncio
from dotenv import load_dotenv
from google import genai

async def test_gemini():
    """Простой скрипт для проверки Gemini API с использованием нового SDK."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Ошибка: GEMINI_API_KEY не найден в .env")
        return

    print(f"🔄 Проверка Google GenAI SDK с ключом: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        client = genai.Client(api_key=api_key)
        model_id = 'gemini-2.0-flash'
        
        prompt = "Составь список покупок в формате JSON из фразы: 'Купи 2 пакета молока и хлеб'"
        
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=prompt
        )
        print("\n✅ Ответ от Gemini:")
        print(response.text)
        
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
