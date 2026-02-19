# Быстрый старт

## Логика работы бота (кратко)

1. **Получение ссылки** → Админ отправляет ссылку на папку Яндекс.Диска
2. **Проверка прав** → Бот проверяет, что отправил админ
3. **Поиск видео** → Рекурсивно ищет все видео файлы в папке
4. **Обработка каждого видео**:
   - Скачивание с Яндекс.Диска
   - Конвертация в аудио (FFmpeg)
   - Транскрибация в текст (Whisper)
   - Отправка текстового файла пользователю
5. **Очистка** → Удаление временных файлов

Подробная логика: см. `LOGIC.md`

## Развертывание на сервере

### Шаг 1: Подготовка

```bash
# На сервере
git clone <your-repo>
cd convert_yandex_bot
```

### Шаг 2: Настройка

Отредактируйте `config.py`:
- `BOT_TOKEN` - токен от @BotFather
- `YANDEX_DISK_TOKEN` - OAuth токен Яндекс.Диска
- `ADMIN_IDS` - ваш Telegram ID

### Шаг 3: Запуск

```bash
# Через Docker Compose (рекомендуется)
docker-compose up -d

# Или через Docker
docker build -t yandex-disk-bot .
docker run -d --name yandex-disk-bot --restart unless-stopped \
  -v $(pwd)/config.py:/app/config.py:ro \
  yandex-disk-bot
```

### Шаг 4: Проверка

```bash
# Логи
docker-compose logs -f

# Статус
docker ps | grep yandex-disk-bot
```

## Структура проекта

```
convert_yandex_bot/
├── main.py                 # Точка входа
├── config.py              # Конфигурация (токены, админы)
├── handlers/              # Обработчики сообщений
│   ├── start.py          # Базовые команды
│   └── disk_handler.py   # Обработка ссылок на Яндекс.Диск
├── yandex_disk.py         # Работа с API Яндекс.Диска
├── video_converter.py     # Конвертация видео в аудио
├── transcription.py       # Транскрибация через Whisper
├── Dockerfile             # Образ Docker
├── docker-compose.yml     # Compose конфигурация
└── requirements.txt       # Python зависимости
```

## Что включено в Docker образ

- Python 3.11
- FFmpeg (для конвертации видео)
- Все Python зависимости (aiogram, whisper, aiohttp)
- Код приложения

## Полезные команды

```bash
# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление
git pull
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f bot

# Вход в контейнер
docker exec -it yandex-disk-bot bash
```


