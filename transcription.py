"""
Модуль для транскрибации аудио через Whisper
"""
import whisper
from pathlib import Path
from typing import Optional
import os


class TranscriptionService:
    """Класс для транскрибации аудио файлов через Whisper"""
    
    def __init__(self, model_size: str = "base"):
        """
        Инициализация сервиса транскрибации
        
        Args:
            model_size: Размер модели Whisper (tiny, base, small, medium, large)
                       base - хороший баланс между скоростью и качеством
        """
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Загружает модель Whisper"""
        try:
            print(f"Загрузка модели Whisper: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            print("Модель загружена успешно")
        except Exception as e:
            print(f"Ошибка при загрузке модели Whisper: {e}")
            self.model = None
    
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Optional[str]:
        """
        Транскрибирует аудио файл в текст
        
        Args:
            audio_path: Путь к аудио файлу
            language: Язык аудио (None для автоопределения, "ru" для русского)
        
        Returns:
            Текст транскрибации или None при ошибке
        """
        if self.model is None:
            print("Модель Whisper не загружена")
            return None
        
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            print(f"Аудио файл не найден: {audio_path}")
            return None
        
        try:
            # Транскрибация
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                task="transcribe"
            )
            
            # Извлекаем текст
            text = result.get("text", "").strip()
            
            if not text:
                print("Транскрибация вернула пустой текст")
                return None
            
            return text
            
        except Exception as e:
            print(f"Ошибка при транскрибации: {e}")
            return None
    
    def transcribe_to_file(self, audio_path: str, output_path: str, language: Optional[str] = None) -> bool:
        """
        Транскрибирует аудио и сохраняет результат в файл
        
        Args:
            audio_path: Путь к аудио файлу
            output_path: Путь для сохранения текста
            language: Язык аудио
        
        Returns:
            True если успешно, False при ошибке
        """
        text = self.transcribe(audio_path, language)
        
        if text is None:
            return False
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            return True
        except Exception as e:
            print(f"Ошибка при сохранении транскрибации: {e}")
            return False

