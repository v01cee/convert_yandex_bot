"""
Модуль для конвертации видео в аудио
"""
import subprocess
from pathlib import Path
from typing import Optional


class VideoConverter:
    """Конвертирует видеофайлы в WAV-аудио для Whisper."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)

    def video_to_audio(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Конвертирует видео в WAV (16 kHz, моно).

        Returns:
            Путь к созданному аудио файлу или None при ошибке.
        """
        video_path = Path(video_path)

        if not video_path.exists():
            print(f"Видео файл не найден: {video_path}")
            return None

        if output_path is None:
            output_path = self.temp_dir / f"{video_path.stem}.wav"
        else:
            output_path = Path(output_path)

        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
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

    @staticmethod
    def cleanup(file_path: str) -> None:
        """Удаляет файл, игнорируя ошибки."""
        try:
            p = Path(file_path)
            if p.exists():
                p.unlink()
        except Exception as e:
            print(f"Ошибка при удалении файла {file_path}: {e}")
