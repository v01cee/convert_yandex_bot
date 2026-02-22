"""
Модуль для транскрибации аудио через Whisper
"""
import whisper
from pathlib import Path
from typing import Optional


class TranscriptionService:
    """Транскрибирует аудиофайлы в текст через OpenAI Whisper."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self._load_model()

    def _load_model(self):
        """Загружает модель Whisper (один раз при старте)."""
        try:
            print(f"Загрузка модели Whisper: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            print("Модель загружена успешно")
        except Exception as e:
            print(f"Ошибка при загрузке модели Whisper: {e}")
            self.model = None

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Optional[str]:
        """
        Транскрибирует аудиофайл в текст.

        Args:
            audio_path: путь к WAV-файлу
            language: код языка ("ru", "en", …) или None для автоопределения

        Returns:
            Строка с текстом или None при ошибке.
        """
        if self.model is None:
            print("Модель Whisper не загружена")
            return None

        audio_path = Path(audio_path)
        if not audio_path.exists():
            print(f"Аудио файл не найден: {audio_path}")
            return None

        try:
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                task="transcribe",
            )
            text = result.get("text", "").strip()
            if not text:
                print("Транскрибация вернула пустой текст")
                return None
            return text
        except Exception as e:
            print(f"Ошибка при транскрибации: {e}")
            return None
