# Команды для работы на сервере

## Получение токена Яндекс.Диска

### Вариант 1: Интерактивный режим

```bash
# На сервере
python get_token_server.py
```

Скрипт покажет ссылку для авторизации. После получения кода введите его в консоль.

### Вариант 2: С кодом как аргументом

```bash
python get_token_server.py <код_верификации>
```

### Вариант 3: Через curl (если нет Python на сервере)

```bash
# 1. Получите код верификации через браузер:
# https://oauth.yandex.ru/authorize?response_type=code&client_id=abfde16472b543eeb696ef1123ecccab&redirect_uri=https://oauth.yandex.ru/verification_code

# 2. Обменяйте код на токен:
curl -X POST https://oauth.yandex.ru/token \
  -d "grant_type=authorization_code" \
  -d "code=ВАШ_КОД" \
  -d "client_id=abfde16472b543eeb696ef1123ecccab" \
  -d "client_secret=b416c596978f493890602d39c2e46da2"
```

## Установка токена в config.py

После получения токена:

```bash
# Редактируем config.py
nano config.py

# Или через sed (замените YOUR_TOKEN на полученный токен)
sed -i 's/YOUR_YANDEX_DISK_TOKEN_HERE/YOUR_TOKEN/g' config.py
```

## Установка через переменные окружения (рекомендуется)

```bash
# Экспорт переменной
export YANDEX_DISK_TOKEN="ваш_токен_здесь"

# Для постоянного использования добавьте в ~/.bashrc или ~/.profile
echo 'export YANDEX_DISK_TOKEN="ваш_токен_здесь"' >> ~/.bashrc
source ~/.bashrc
```

## Быстрая команда для получения токена

```bash
# Полный процесс в одной команде (после получения кода)
python get_token_server.py <код> | grep -A 1 "Ваш токен:" | tail -1
```

## Проверка токена

```bash
# Проверка работы токена
curl -H "Authorization: OAuth YOUR_TOKEN" https://cloud-api.yandex.net/v1/disk
```

## Получение токена бота

Токен бота получается от @BotFather в Telegram:
1. Откройте @BotFather в Telegram
2. Отправьте `/mybots`
3. Выберите вашего бота
4. Выберите "API Token"
5. Скопируйте токен

## Безопасное хранение токенов

Рекомендуется использовать переменные окружения вместо хардкода в config.py:

```bash
# Создайте .env файл
cat > .env << EOF
BOT_TOKEN=ваш_токен_бота
YANDEX_DISK_TOKEN=ваш_токен_яндекс_диска
EOF

# Загрузите переменные
source .env
```


