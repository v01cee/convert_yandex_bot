"""
Модуль для конвертации видео в аудио
"""
import os
import subprocess
from pathlib import Path
from typing import Optional


class VideoConverter:
    """Класс для конвертации видео файлов в аудио"""
    
    def __init__(self, temp_dir: str = "temp"):
        """
        Инициализация конвертера
        
        Args:
            temp_dir: Директория для временных файлов
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def video_to_audio(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Конвертирует видео файл в аудио (WAV формат)
        
        Args:
            video_path: Путь к видео файлу
            output_path: Путь для сохранения аудио (если None, генерируется автоматически)
        
        Returns:
            Путь к созданному аудио файлу или None при ошибке
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            print(f"Видео файл не найден: {video_path}")
            return None
        
        # Генерируем имя выходного файла
        if output_path is None:
            output_path = self.temp_dir / f"{video_path.stem}.wav"
        else:
            output_path = Path(output_path)
        
        try:
            # Используем ffmpeg для конвертации
            # -i: входной файл
            # -vn: отключить видео
            # -acodec pcm_s16le: кодек для WAV
            # -ar 16000: частота дискретизации 16kHz (оптимально для Whisper)
            # -ac 1: моно канал
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",  # Без видео
                "-acodec", "pcm_s16le",  # WAV кодек
                "-ar", "16000",  # Частота дискретизации
                "-ac", "1",  # Моно
                "-y",  # Перезаписать если существует
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if output_path.exists():
                return str(output_path)
            else:
                print(f"Аудио файл не был создан: {output_path}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при конвертации видео: {e.stderr}")
            return None
        except FileNotFoundError:
            print("ffmpeg не найден. Установите ffmpeg для работы с видео.")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при конвертации: {e}")
            return None
    
    def cleanup(self, file_path: str):
        """
        Удаляет временный файл
        
        Args:
            file_path: Путь к файлу для удаления
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
        except Exception as e:
            print(f"Ошибка при удалении файла {file_path}: {e}")

