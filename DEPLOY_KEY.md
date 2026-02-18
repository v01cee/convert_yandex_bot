# Настройка Deploy Key для GitHub

Deploy Key - это SSH ключ, который дает серверу доступ к репозиторию без использования вашего личного аккаунта.

## Быстрая настройка

### На сервере выполните:

```bash
# 1. Сделайте скрипт исполняемым
chmod +x setup_deploy_key.sh

# 2. Запустите скрипт
./setup_deploy_key.sh
```

## Ручная настройка

### Шаг 1: Генерация SSH ключа на сервере

```bash
# Генерируем ключ (без пароля для автоматизации)
ssh-keygen -t ed25519 -C "deploy-key" -f ~/.ssh/github_deploy_key -N ""
```

### Шаг 2: Получение публичного ключа

```bash
# Показываем публичный ключ
cat ~/.ssh/github_deploy_key.pub
```

Скопируйте весь вывод (начинается с `ssh-ed25519` или `ssh-rsa`)

### Шаг 3: Добавление ключа в GitHub

1. Перейдите: https://github.com/v01cee/convert_yandex_bot/settings/keys
2. Нажмите **"Add deploy key"**
3. **Title**: `Server Deploy Key` (или любое имя)
4. **Key**: Вставьте скопированный публичный ключ
5. **Allow write access**: Отметьте, если нужен push (обычно не нужно)
6. Нажмите **"Add key"**

### Шаг 4: Настройка SSH config

```bash
# Добавляем конфигурацию для GitHub
cat >> ~/.ssh/config << 'EOF'

Host github-deploy
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_deploy_key
    IdentitiesOnly yes
EOF

# Устанавливаем правильные права
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/github_deploy_key
chmod 644 ~/.ssh/github_deploy_key.pub
```

### Шаг 5: Тестирование

```bash
# Проверяем подключение
ssh -T github-deploy
```

Должно вывести: `Hi v01cee/convert_yandex_bot! You've successfully authenticated...`

### Шаг 6: Клонирование репозитория

```bash
# Клонируем используя deploy key
git clone git@github-deploy:v01cee/convert_yandex_bot.git
cd convert_yandex_bot
```

## Альтернатива: Использование токена (Personal Access Token)

Если не хотите использовать SSH:

```bash
# Клонируем через HTTPS с токеном
git clone https://<TOKEN>@github.com/v01cee/convert_yandex_bot.git
```

Где `<TOKEN>` - Personal Access Token из GitHub Settings → Developer settings → Personal access tokens

## Команды для работы с репозиторием

```bash
# Если уже клонирован через HTTPS, переключаем на SSH
cd convert_yandex_bot
git remote set-url origin git@github-deploy:v01cee/convert_yandex_bot.git

# Проверка
git remote -v
```

## Безопасность

- **Никогда не коммитьте приватный ключ** (`github_deploy_key`) в репозиторий
- Храните ключ только на сервере
- Используйте отдельный ключ для каждого сервера
- Регулярно ротируйте ключи

## Удаление deploy key

Если нужно удалить ключ:
1. GitHub → Settings → Deploy keys
2. Нажмите "Delete" рядом с нужным ключом

## Troubleshooting

### Ошибка: Permission denied (publickey)

```bash
# Проверьте права на файлы
ls -la ~/.ssh/github_deploy_key*

# Должно быть:
# -rw------- (600) для приватного ключа
# -rw-r--r-- (644) для публичного ключа
```

### Ошибка: Host key verification failed

```bash
# Добавляем GitHub в known_hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts
```

