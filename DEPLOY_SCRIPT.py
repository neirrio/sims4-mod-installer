#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматической настройки и загрузки проекта на GitHub
"""

import os
import subprocess
import json
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Выполнение команды"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка команды: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        print(f"✅ Успешно: {cmd}")
        return True
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        return False

def setup_git_repo():
    """Настройка Git репозитория"""
    print("🔧 Настройка Git репозитория...")
    
    # Инициализация
    if not run_command("git init"):
        return False
    
    # Добавление всех файлов
    if not run_command("git add ."):
        return False
    
    # Первый коммит
    if not run_command('git commit -m "🚀 Initial release - Sims 4 Mod Installer v2.1 with GitHub updates"'):
        return False
    
    print("✅ Git репозиторий настроен")
    return True

def create_github_repo_instructions():
    """Создание инструкций по настройке GitHub"""
    instructions = """
# 🚀 Инструкции по настройке GitHub репозитория

## 1. Создание репозитория на GitHub

1. Зайдите на https://github.com
2. Нажмите "New repository"
3. Название: `sims4-mod-installer`
4. Описание: "🎮 Автоматический установщик модов для The Sims 4 с обновлениями через GitHub"
5. Поставьте галочку "Public" (бесплатно)
6. НЕ ставьте галочку "Add a README file" (у нас уже есть)
7. Нажмите "Create repository"

## 2. Подключение локального репозитория

После создания репозитория GitHub покажет команды. Выполните:

```bash
git remote add origin https://github.com/neirrio/sims4-mod-installer.git
git branch -M main
git push -u origin main
```

## 3. Создание первого релиза

```bash
git tag v2.1.0
git push origin v2.1.0
```

## 4. Настройка GitHub Actions (автоматически)

GitHub Actions начнут работать автоматически после первого пуша.

## 5. Проверка работы

1. Запустите программу: `python sims4_mod_installer.py`
2. Проверьте логи - должна появиться проверка обновлений
3. Создайте новый релиз для тестирования

## 🔧 Дополнительные настройки

### Режим технических работ:
Создайте файл `maintenance.json` в корне репозитория:
```json
{
  "enabled": true,
  "message": "Проводятся технические работы..."
}
```

### Новые версии:
```bash
git add .
git commit -m "New features"
git tag v2.2.0
git push origin main v2.2.0
```

### Обязательные обновления:
```bash
git tag v2.2.0-mandatory
git push origin v2.2.0-mandatory
```

---
Готово! 🎉 Ваша программа теперь поддерживает автоматические обновления!
"""
    
    with open("GITHUB_INSTRUCTIONS.md", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    print("📝 Создан файл GITHUB_INSTRUCTIONS.md с инструкциями")

def check_files():
    """Проверка необходимых файлов"""
    required_files = [
        "sims4_mod_installer.py",
        "requirements.txt",
        "README.md",
        "MEGA_UPDATE_GUIDE.md",
        "GITHUB_SETUP_GUIDE.md",
        "QUICK_START.md",
        "maintenance.json",
        ".github/workflows/release.yml"
    ]
    
    print("🔍 Проверка файлов...")
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    print("✅ Все файлы на месте")
    return True

def prepare_deployment():
    """Подготовка к развертыванию"""
    print("🚀 Подготовка к развертыванию на GitHub...")
    
    # Проверка файлов
    if not check_files():
        return False
    
    # Настройка Git
    if not setup_git_repo():
        return False
    
    # Создание инструкций
    create_github_repo_instructions()
    
    print("\n" + "="*50)
    print("🎉 Готово к развертыванию!")
    print("="*50)
    print("\n📋 Следующие шаги:")
    print("1. Создайте репозиторий на GitHub: sims4-mod-installer")
    print("2. Выполните команды:")
    print("   git remote add origin https://github.com/neirrio/sims4-mod-installer.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print("3. Создайте первый релиз:")
    print("   git tag v2.1.0")
    print("   git push origin v2.1.0")
    print("\n📖 Подробная инструкция в файле GITHUB_INSTRUCTIONS.md")
    print("🎯 После этого программа будет автоматически проверять обновления!")
    
    return True

if __name__ == "__main__":
    print("🎮 Sims 4 Mod Installer - GitHub Deployment")
    print("="*50)
    
    if prepare_deployment():
        print("\n✅ Подготовка завершена успешно!")
    else:
        print("\n❌ Ошибка при подготовке")
        sys.exit(1)
