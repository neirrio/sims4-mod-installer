# 📦 Установка Git на Windows

## 🚀 Способ 1: Официальный сайт (рекомендуется)

### 1. Скачайте Git
- Откройте браузер
- Перейдите на https://git-scm.com/download/win
- Скачайте автоматически предложенную версию (64-bit Git for Windows Setup)

### 2. Установите Git
1. Запустите скачанный файл `Git-*.exe`
2. Нажмите "Next" на всех шагах (настройки по умолчанию подойдут)
3. На шаге "Choosing the default editor" выберите "Notepad++" или "VS Code"
4. Нажмите "Install" и дождитесь завершения
5. Нажмите "Finish"

### 3. Проверка установки
1. Откройте новую командную строку (CMD) или PowerShell
2. Введите команду:
```bash
git --version
```
Если увидите версию (например, `git version 2.40.0`), всё установлено!

## 🔧 Способ 2: Через Winget (если установлен)

Откройте PowerShell и выполните:
```bash
winget install --id Git.Git -e --source winget
```

## 🔄 Способ 3: Через Chocolatey (если установлен)

```bash
choco install git
```

## ✅ После установки

1. **Перезагрузите компьютер** (важно!)
2. Откройте новую командную строку
3. Проверьте:
```bash
git --version
```

## 🎯 Настройка Git

После установки выполните в командной строке:

```bash
git config --global user.name "neirrio"
git config --global user.email "your-email@example.com"
```

Замените `your-email@example.com` на ваш реальный email.

## 🚨 Если не работает

### Проверка путей
1. Откройте PowerShell
2. Выполните:
```bash
echo $env:PATH
```
В пути должен быть `C:\Program Files\Git\cmd` или похожий.

### Ручное добавление в PATH
1. Win + R → `sysdm.cpl`
2. "Дополнительно" → "Переменные среды"
3. "Path" → "Изменить"
4. "Создать" → добавьте `C:\Program Files\Git\cmd`
5. Нажмите "ОК" везде

---

## 📋 Что делать после установки Git

1. Создайте репозиторий на GitHub: `sims4-mod-installer`
2. Откройте CMD в папке `e:\digital`
3. Выполните команды из `MANUAL_DEPLOY.md`

**Готово! После установки Git сможем загрузить ваш проект на GitHub.** 🎉
