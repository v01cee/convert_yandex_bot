#!/bin/bash
# Скрипт для создания и настройки deploy key для GitHub

echo "=========================================="
echo "Настройка Deploy Key для GitHub"
echo "=========================================="
echo ""

# Генерируем SSH ключ
echo "1. Генерируем SSH ключ..."
ssh-keygen -t ed25519 -C "deploy-key-$(date +%Y%m%d)" -f ~/.ssh/github_deploy_key -N ""

echo ""
echo "2. Публичный ключ (скопируйте его):"
echo "=========================================="
cat ~/.ssh/github_deploy_key.pub
echo "=========================================="
echo ""

echo "3. Добавьте этот ключ в GitHub:"
echo "   - Перейдите: https://github.com/v01cee/convert_yandex_bot/settings/keys"
echo "   - Нажмите 'Add deploy key'"
echo "   - Вставьте публичный ключ выше"
echo "   - Название: 'Server Deploy Key'"
echo "   - Отметьте 'Allow write access' (если нужно)"
echo ""

echo "4. Настройка SSH config..."
cat >> ~/.ssh/config << EOF

# GitHub Deploy Key
Host github-deploy
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_deploy_key
    IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config

echo "5. Тестирование подключения..."
ssh -T github-deploy 2>&1 | head -3

echo ""
echo "=========================================="
echo "Готово! Теперь можно клонировать:"
echo "git clone git@github-deploy:v01cee/convert_yandex_bot.git"
echo "=========================================="

