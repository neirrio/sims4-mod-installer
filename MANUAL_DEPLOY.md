# 🚀 Ручная настройка GitHub проекта

## 📋 Что нужно сделать:

### 1. Установка Git (если не установлен)

Скачайте и установите Git с официального сайта:
- https://git-scm.com/download/win

После установки перезагрузите компьютер.

### 2. Создание репозитория на GitHub

1. Зайдите на https://github.com и войдите в аккаунт
2. Нажмите зеленую кнопку "New" → "New repository"
3. **Repository name**: `sims4-mod-installer`
4. **Description**: `🎮 Автоматический установщик модов для The Sims 4 с обновлениями через GitHub`
5. Выберите **Public** (бесплатно)
6. **НЕ ставьте** галочку "Add a README file" (у нас уже есть)
7. **НЕ ставьте** галочку "Add .gitignore" 
8. **НЕ ставьте** галочку "Choose a license"
9. Нажмите "Create repository"

### 3. Настройка локального репозитория

Откройте командную строку (CMD) или PowerShell в папке проекта (`e:\digital`):

```bash
# Инициализация Git
git init

# Настройка пользователя (если первый раз)
git config --global user.name "neirrio"
git config --global user.email "your-email@example.com"

# Добавление всех файлов
git add .

# Первый коммит
git commit -m "🚀 Initial release - Sims 4 Mod Installer v2.1 with GitHub updates"

# Подключение к GitHub
git remote add origin https://github.com/neirrio/sims4-mod-installer.git

# Установка основной ветки
git branch -M main

# Отправка на GitHub
git push -u origin main
```

### 4. Создание первого релиза

В той же командной строке:

```bash
# Создание тега версии
git tag v2.1.0

# Отправка тега на GitHub
git push origin v2.1.0
```

### 5. Проверка работы

1. Запустите программу:
```bash
python sims4_mod_installer.py
```

2. В логах должно появиться:
```
[12:00:00] Устройство зарегистрировано: abc12345...
[12:00:01] Проверка обновлений...
[12:00:02] Актуальная версия: 2.1.0
```

3. Зайдите в ваш репозиторий на GitHub → Releases
   - Должен появиться релиз v2.1.0
   - GitHub Actions начнут сборку (может занять 5-10 минут)

## 🎯 Управление обновлениями

### Создание новой версии

```bash
# Внесите изменения в код
git add .
git commit -m "✨ Added new features"

# Создайте новый тег
git tag v2.2.0

# Отправьте всё на GitHub
git push origin main v2.2.0
```

### Обязательное обновление

```bash
# Тег с пометкой mandatory
git tag v2.2.0-mandatory
git push origin v2.2.0-mandatory
```

### Режим технических работ

Создайте файл `maintenance.json` в корне проекта:
```json
{
  "enabled": true,
  "message": "Проводятся технические работы. Программа временно недоступна.",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

Загрузите изменения:
```bash
git add maintenance.json
git commit -m "🔧 Enable maintenance mode"
git push origin main
```

Для отключения режима:
```json
{
  "enabled": false,
  "message": "",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

## 🔧 GitHub Actions

После первого пуша GitHub Actions автоматически:
- Соберут .exe файл
- Создадут ZIP архив
- Опубликуют релиз

Проверить статус можно в репозитории → Actions.

## 📊 Мониторинг

### Статистика GitHub
- Repository → Insights → Traffic
- Repository → Insights → Analytics

### Логи программы
- Запускаются в консоли при запуске
- Показывают процесс проверки обновлений
- Сообщают об ошибках

## 🐛 Поиск проблем

### Ошибка "git not found"
- Установите Git с https://git-scm.com
- Перезагрузите компьютер

### Ошибка "Permission denied"
- Проверьте права доступа к репозиторию
- Убедитесь что вы вошли в GitHub

### Ошибка "Repository not found"
- Проверьте имя репозитория
- Убедитесь что репозиторий публичный

### GitHub Actions не работает
- Проверьте файл `.github/workflows/release.yml`
- Убедитесь что YAML синтаксис корректен

## 🎉 Готово!

После выполнения этих шагов:

✅ Программа будет автоматически проверять обновления  
✅ Пользователи смогут устанавливать новые версии  
✅ Вы сможете управлять режимом обслуживания  
✅ GitHub Actions будут собирать дистрибутивы  

---

## 📞 Поддержка

Если возникнут проблемы:
1. Проверьте логи программы
2. Проверьте статус GitHub Actions
3. Создайте Issue в репозитории

**🎮 Ваш Sims 4 Mod Installer готов к работе с GitHub обновлениями!**
