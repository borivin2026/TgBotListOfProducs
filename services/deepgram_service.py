import os
from typing import Optional
from deepgram import AsyncDeepgramClient

from utils.logger import logger

class DeepgramService:
    """Сервис для взаимодействия с Deepgram API (Speech-to-Text)."""

    def __init__(self, api_key: str):
        self.client = AsyncDeepgramClient(api_key=api_key)


    async def transcribe_audio(self, audio_content: bytes) -> Optional[str]:
        """
        Распознает речь из байтового потока аудио.
        
        :param audio_content: Содержимое аудиофайла в байтах
        :return: Распознанный текст или None в случае ошибки
        """
        try:
            response = await self.client.listen.v1.media.transcribe_file(
                request=audio_content,
                model="nova-3",
                smart_format=True,
                language="ru",
            )

            
            transcript = response.results.channels[0].alternatives[0].transcript
            logger.info(f"Deepgram успешно распознал текст: {transcript[:50]}...")
            return transcript

        except Exception as e:
            logger.error(f"Ошибка при работе с Deepgram API: {e}", exc_info=True)
            return None

