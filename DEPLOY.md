# Инструкция по развертыванию на сервере

## Подготовка на сервере

### 1. Установка Docker

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

**CentOS/RHEL:**
```bash
sudo yum install -y docker docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

### 2. Клонирование проекта

```bash
git clone <your-repo-url>
cd convert_yandex_bot
```

### 3. Настройка конфигурации

Отредактируйте `config.py`:
```python
BOT_TOKEN = "ваш_токен_бота"
YANDEX_DISK_TOKEN = "ваш_токен_яндекс_диска"
ADMIN_IDS = [ваш_telegram_id]
```

## Развертывание

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Вариант 2: Docker напрямую

```bash
# Сборка образа
docker build -t yandex-disk-bot .

# Запуск контейнера
docker run -d \
  --name yandex-disk-bot \
  --restart unless-stopped \
  -v $(pwd)/config.py:/app/config.py:ro \
  -v $(pwd)/temp:/app/temp \
  yandex-disk-bot

# Просмотр логов
docker logs -f yandex-disk-bot
```

## Обновление

```bash
# Остановить контейнер
docker-compose down

# Обновить код (если через git)
git pull

# Пересобрать и запустить
docker-compose up -d --build
```

## Мониторинг

### Проверка статуса

```bash
docker ps | grep yandex-disk-bot
```

### Просмотр логов

```bash
docker-compose logs -f bot
```

### Использование ресурсов

```bash
docker stats yandex-disk-bot
```

## Резервное копирование

Важные файлы для бэкапа:
- `config.py` - конфигурация с токенами
- Логи (если настроено логирование в файл)

## Troubleshooting

### Бот не запускается

1. Проверьте логи:
```bash
docker-compose logs bot
```

2. Проверьте конфигурацию:
```bash
docker exec yandex-disk-bot cat config.py
```

3. Проверьте, что токены корректны

### Ошибки с Whisper

Модель Whisper загружается при первом использовании (~150MB). Убедитесь, что:
- Есть достаточно места на диске
- Есть доступ в интернет для загрузки модели

### Проблемы с FFmpeg

FFmpeg установлен в Docker образе. Если проблемы:
```bash
docker exec yandex-disk-bot ffmpeg -version
```

## Оптимизация

### Ограничение ресурсов

В `docker-compose.yml` можно добавить:
```yaml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Персистентное хранилище

Для сохранения моделей Whisper между перезапусками:
```yaml
volumes:
  - ./whisper_models:/root/.cache/whisper
```


