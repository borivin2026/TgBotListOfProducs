import os
import asyncio
from dotenv import load_dotenv
from deepgram import AsyncDeepgramClient


async def test_deepgram(audio_path: str):
    """Проверка Deepgram API с локальным файлом (SDK v7)."""
    load_dotenv()
    api_key = os.getenv("DEEPGRAM_API_KEY")

    if not api_key:
        print("❌ Ошибка: DEEPGRAM_API_KEY не найден в .env")
        return

    if not os.path.exists(audio_path):
        print(f"❌ Файл не найден: {audio_path}")
        return

    try:
        deepgram = AsyncDeepgramClient(api_key=api_key)

        with open(audio_path, "rb") as file:
            buffer_data = file.read()

        print(f"🔄 Отправка файла {audio_path} в Deepgram (Async)...")

        response = await deepgram.listen.v1.media.transcribe_file(
            request=buffer_data,
            model="nova-3",
            smart_format=True,
            language="ru",
        )

        
        transcript = response.results.channels[0].alternatives[0].transcript
        print("\n✅ Распознанный текст:")
        print(transcript)

    except Exception as e:
        print(f"❌ Ошибка Deepgram: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Использование: python scripts/test_deepgram.py <путь_к_аудио_файлу>")
    else:
        asyncio.run(test_deepgram(sys.argv[1]))
