#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический установщик модов для The Sims 4
Создан для быстрой и удобной установки модов без участия пользователя
"""

import os
import json
import requests
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import winreg
from urllib.parse import urlparse
import time
import tkinter.simpledialog as simpledialog
import webbrowser
from datetime import datetime
import hashlib
import uuid
import platform
import subprocess
import sys
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
try:
    import py7zr
    PY7Z_AVAILABLE = True
except ImportError:
    PY7Z_AVAILABLE = False
try:
    import rarfile
    RAR_AVAILABLE = True
except ImportError:
    RAR_AVAILABLE = False
import tempfile

class Sims4ModInstaller:
    def __init__(self):
        # Инициализация с поддержкой DnD
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        
        self.root.title("Sims 4 Auto Mod Installer")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        # Пути
        self.sims4_path = ""
        self.mods_path = ""
        self.download_folder = os.path.join(os.getcwd(), "downloads")
        
        # Создаем папку для загрузок
        os.makedirs(self.download_folder, exist_ok=True)
        
        # Настройки
        self.settings_file = "installer_settings.json"
        self.app_version = "2.1"
        self.app_name = "Sims 4 Auto Mod Installer"
        
        # GitHub настройки
        self.github_owner = "neirrio"  # Измените на ваш GitHub username
        self.github_repo = "sims4-mod-installer"  # Измените на ваш репозиторий
        self.github_api_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}"
        
        # Файлы для работы с обновлениями
        self.device_token_file = "device_token.json"
        self.maintenance_mode_file = "maintenance_mode.json"
        
        # Система обновлений
        self.update_check_interval = 300  # 5 минут
        self.current_update_info = None
        self.maintenance_mode = False
        
        # Генерация и загрузка токена устройства
        self.device_token = self.get_or_create_device_token()
        
        # Проверка режима обслуживания
        self.check_maintenance_mode()
        
        # Проверка обновлений при запуске
        self.check_for_updates()
        
        self.load_settings()
        
        # Создаем интерфейс
        self.create_gui()
        
        # Добавляем горячие клавиши
        self.root.bind('<Control-v>', lambda e: self.paste_from_clipboard())
        
        # Автоматический поиск игры
        threading.Thread(target=self.auto_find_sims4, daemon=True).start()
        
        # Запуск фоновых задач
        self.start_background_tasks()
    
    def get_or_create_device_token(self):
        """Генерация или загрузка уникального токена устройства"""
        try:
            if os.path.exists(self.device_token_file):
                with open(self.device_token_file, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                    return token_data.get('token')
            else:
                # Генерируем новый токен
                token_data = {
                    'token': str(uuid.uuid4()),
                    'device_id': self.get_device_id(),
                    'created_at': datetime.now().isoformat(),
                    'version': self.app_version,
                    'system_info': self.get_system_info()
                }
                
                with open(self.device_token_file, 'w', encoding='utf-8') as f:
                    json.dump(token_data, f, indent=2, ensure_ascii=False)
                
                # Отправляем информацию о новом устройстве на сервер
                self.register_device(token_data)
                
                return token_data['token']
        except Exception as e:
            print(f"Ошибка работы с токеном: {e}")
            return str(uuid.uuid4())  # Fallback
    
    def get_device_id(self):
        """Получение уникального ID устройства"""
        try:
            # Комбинируем несколько параметров для уникальности
            machine_name = platform.node()
            system_info = f"{platform.system()}-{platform.release()}"
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
            
            # Создаем хеш от комбинации
            unique_string = f"{machine_name}-{system_info}-{mac_address}"
            return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
        except:
            return str(uuid.uuid4())[:16]
    
    def get_system_info(self):
        """Сбор информации о системе"""
        try:
            return {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version()
            }
        except:
            return {'error': 'Failed to get system info'}
    
    def register_device(self, token_data):
        """Регистрация устройства через GitHub (опционально)"""
        try:
            # Отправляем статистику в GitHub Issue или через webhook
            # Это опциональная функция для сбора статистики
            
            # Создаем анонимную статистику
            stats_data = {
                'device_id': token_data['device_id'][:8] + '...',  # Только часть ID для приватности
                'version': token_data['version'],
                'system': token_data['system_info'].get('system', 'Unknown'),
                'timestamp': datetime.now().isoformat()
            }
            
            self.log_message(f"Устройство зарегистрировано: {stats_data['device_id']}")
            
        except Exception as e:
            self.log_message(f"Ошибка регистрации устройства: {e}")
    
    def check_maintenance_mode(self):
        """Проверка режима обслуживания через GitHub"""
        try:
            # Проверяем наличие файла maintenance.json в репозитории
            response = requests.get(
                f"{self.github_api_url}/contents/maintenance.json",
                headers={
                    'User-Agent': f'{self.app_name}/{self.app_version}',
                    'Accept': 'application/vnd.github.v3+json'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                # Файл существует - режим обслуживания включен
                import base64
                content = base64.b64decode(response.json()['content']).decode('utf-8')
                maintenance_data = json.loads(content)
                
                self.maintenance_mode = maintenance_data.get('enabled', False)
                
                # Сохраняем локально для офлайн работы
                with open(self.maintenance_mode_file, 'w', encoding='utf-8') as f:
                    json.dump(maintenance_data, f, indent=2, ensure_ascii=False)
                    
                if self.maintenance_mode:
                    self.log_message("Режим обслуживания включен")
                    
            elif response.status_code == 404:
                # Файл не найден - режим обслуживания выключен
                self.maintenance_mode = False
                # Удаляем локальный файл если существует
                if os.path.exists(self.maintenance_mode_file):
                    os.remove(self.maintenance_mode_file)
                    
        except Exception as e:
            # В случае ошибки сервера, проверяем локальный файл
            self.log_message(f"Ошибка проверки режима обслуживания: {e}")
            if os.path.exists(self.maintenance_mode_file):
                try:
                    with open(self.maintenance_mode_file, 'r', encoding='utf-8') as f:
                        maintenance_data = json.load(f)
                        self.maintenance_mode = maintenance_data.get('enabled', False)
                except:
                    pass
    
    def check_for_updates(self):
        """Проверка обновлений через GitHub Releases"""
        try:
            # Получаем последний релиз с GitHub
            response = requests.get(
                f"{self.github_api_url}/releases/latest",
                timeout=15,
                headers={
                    'User-Agent': f'{self.app_name}/{self.app_version}',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')
                
                # Сравниваем версии
                if self.compare_versions(latest_version, self.app_version) > 0:
                    # Доступно обновление
                    update_info = {
                        'update_available': True,
                        'version': latest_version,
                        'download_url': self.get_download_url(release_data),
                        'release_notes': release_data.get('body', 'Доступно новое обновление'),
                        'mandatory': self.is_mandatory_update(release_data),
                        'published_at': release_data.get('published_at', '')
                    }
                    
                    self.current_update_info = update_info
                    self.show_update_dialog(update_info)
                else:
                    self.log_message(f"Актуальная версия: {self.app_version}")
                    
            elif response.status_code == 404:
                self.log_message("Релизы не найдены на GitHub")
            else:
                self.log_message(f"Ошибка проверки обновлений: {response.status_code}")
                    
        except Exception as e:
            self.log_message(f"Ошибка проверки обновлений: {str(e)}")
    
    def compare_versions(self, version1, version2):
        """Сравнение версий (возвращает 1 если v1 > v2, 0 если равны, -1 если v1 < v2)"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Дополняем короткие версии нулями
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1
            return 0
        except:
            return -1  # В случае ошибки считаем что версия новее
    
    def get_download_url(self, release_data):
        """Получение URL для скачивания обновления"""
        try:
            # Ищем первый .zip файл в assets
            assets = release_data.get('assets', [])
            for asset in assets:
                if asset['name'].endswith('.zip'):
                    return asset['browser_download_url']
            
            # Если нет assets, используем source code
            return release_data.get('zipball_url', '')
        except:
            return ''
    
    def is_mandatory_update(self, release_data):
        """Проверка является ли обновление обязательным"""
        try:
            # Проверяем тег на наличие 'mandatory' или 'critical'
            tag_name = release_data.get('tag_name', '').lower()
            release_notes = release_data.get('body', '').lower()
            
            mandatory_keywords = ['mandatory', 'critical', 'security', 'urgent']
            
            return any(keyword in tag_name or keyword in release_notes 
                      for keyword in mandatory_keywords)
        except:
            return False
    
    def download_and_install_update(self, download_url, mandatory=False):
        """Скачивание и установка обновления с GitHub"""
        try:
            self.log_message("Скачивание обновления с GitHub...")
            
            # Скачиваем обновление
            update_file = os.path.join(self.download_folder, "update.zip")
            
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Показываем прогресс скачивания
                        if total_size > 0:
                            progress = (downloaded / total_size) * 50
                            if hasattr(self, 'progress_var'):
                                self.progress_var.set(progress)
            
            self.log_message(f"Обновление скачано: {downloaded / 1024 / 1024:.1f} MB")
            
            # Создаем скрипт обновления
            update_script = self.create_update_script(update_file)
            
            # Запускаем скрипт и закрываем программу
            subprocess.Popen([sys.executable, update_script], shell=True)
            
            if mandatory:
                self.root.destroy()
                sys.exit(0)
            else:
                self.root.withdraw()  # Скрываем окно на время обновления
                
        except Exception as e:
            self.log_message(f"Ошибка обновления: {e}")
            messagebox.showerror("Ошибка обновления", f"Не удалось установить обновление: {e}")
    
    def show_update_dialog(self, update_info):
        """Показ диалога обновления"""
        version = update_info.get('version', 'Unknown')
        notes = update_info.get('release_notes', 'Доступно новое обновление')
        mandatory = update_info.get('mandatory', False)
        download_url = update_info.get('download_url', '')
        
        title = "Обязательное обновление!" if mandatory else "Доступно обновление"
        message = f"Доступна версия {version}\n\n{notes}\n\n"
        
        if mandatory:
            message += "Это обновление является обязательным. Программа не будет работать до установки."
        else:
            message += "Установить обновление сейчас?"
        
        if mandatory:
            result = messagebox.showinfo(title, message)
            self.download_and_install_update(download_url, mandatory=True)
        else:
            result = messagebox.askyesno(title, message)
            if result:
                self.download_and_install_update(download_url, mandatory=False)
    
    def download_and_install_update(self, download_url, mandatory=False):
        """Скачивание и установка обновления"""
        try:
            self.log_message("Скачивание обновления...")
            
            # Скачиваем обновление
            update_file = os.path.join(self.download_folder, "update.zip")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.log_message("Обновление скачано, начинаю установку...")
            
            # Создаем скрипт обновления
            update_script = self.create_update_script(update_file)
            
            # Запускаем скрипт и закрываем программу
            subprocess.Popen([sys.executable, update_script], shell=True)
            
            if mandatory:
                self.root.destroy()
                sys.exit(0)
            else:
                self.root.withdraw()  # Скрываем окно на время обновления
                
        except Exception as e:
            self.log_message(f"Ошибка обновления: {e}")
            messagebox.showerror("Ошибка обновления", f"Не удалось установить обновление: {e}")
    
    def create_update_script(self, update_file):
        """Создание скрипта для обновления"""
        script_path = os.path.join(tempfile.gettempdir(), "update_script.py")
        
        script_content = f'''
import os
import sys
import time
import zipfile
import shutil
import subprocess

def main():
    try:
        print("Начинаю обновление...")
        
        # Ждем пока основная программа закроется
        time.sleep(2)
        
        # Распаковываем обновление
        with zipfile.ZipFile(r"{update_file}", 'r') as zip_ref:
            zip_ref.extractall(r"{os.getcwd()}")
        
        print("Обновление установлено")
        
        # Удаляем временные файлы
        try:
            os.remove(r"{update_file}")
            os.remove(__file__)
        except:
            pass
        
        # Перезапускаем программу
        subprocess.Popen([sys.executable, r"{os.path.abspath(__file__)}"])
        
    except Exception as e:
        print(f"Ошибка обновления: {{e}}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()
'''
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_path
    
    def show_maintenance_overlay(self):
        """Показ оверлея технических работ"""
        if self.maintenance_mode:
            # Создаем модальное окно с сообщением о технических работах
            maintenance_window = tk.Toplevel(self.root)
            maintenance_window.title("Технические работы")
            maintenance_window.geometry("400x200")
            maintenance_window.resizable(False, False)
            
            # Делаем окно модальным и поверх всех
            maintenance_window.transient(self.root)
            maintenance_window.grab_set()
            maintenance_window.attributes('-topmost', True)
            
            main_frame = ttk.Frame(maintenance_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(main_frame, text="🔧 Технические работы", 
                     font=("Arial", 16, "bold")).pack(pady=(0, 20))
            
            ttk.Label(main_frame, 
                     text="В настоящее время проводятся технические работы.\n\n" +
                          "Программа временно недоступна.\n" +
                          "Пожалуйста, попробуйте позже.",
                     justify=tk.CENTER).pack(pady=(0, 20))
            
            ttk.Button(main_frame, text="OK", 
                      command=maintenance_window.destroy).pack()
            
            # Блокируем основное окно
            self.root.withdraw()
            
            # Закрываем оверлей при закрытии
            maintenance_window.protocol("WM_DELETE_WINDOW", 
                                      lambda: self.close_maintenance_overlay(maintenance_window))
    
    def close_maintenance_overlay(self, maintenance_window):
        """Закрытие оверлея и проверка режима обслуживания"""
        maintenance_window.destroy()
        self.check_maintenance_mode()
        
        if not self.maintenance_mode:
            self.root.deiconify()
        else:
            # Если режим все еще активен, показываем оверлей снова
            self.root.after(1000, self.show_maintenance_overlay)
    
    def start_background_tasks(self):
        """Запуск фоновых задач"""
        # Проверка обновлений в фоне
        def update_checker():
            while True:
                try:
                    time.sleep(self.update_check_interval)
                    self.check_for_updates()
                    self.check_maintenance_mode()
                    
                    if self.maintenance_mode:
                        self.root.after(0, self.show_maintenance_overlay)
                        
                except Exception as e:
                    print(f"Ошибка в фоновой задаче: {e}")
        
        threading.Thread(target=update_checker, daemon=True).start()
    
    def create_gui(self):
        """Создание графического интерфейса"""
        
        # Основная рамка
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка веса колонок и строк
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Путь к игре
        ttk.Label(main_frame, text="Путь к The Sims 4:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.path_var = tk.StringVar(value=self.sims4_path or "Поиск...")
        self.path_entry = ttk.Entry(main_frame, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        
        ttk.Button(main_frame, text="Обзор...", command=self.browse_sims4).grid(row=0, column=2, pady=5)
        ttk.Button(main_frame, text="Найти авто", command=self.auto_find_sims4).grid(row=0, column=3, pady=5, padx=(5, 0))
        
        # Путь к модам
        ttk.Label(main_frame, text="Папка модов:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.mods_path_var = tk.StringVar(value=self.mods_path or "Будет определен автоматически")
        ttk.Entry(main_frame, textvariable=self.mods_path_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        
        # URL мода
        ttk.Label(main_frame, text="URL мода (прямая ссылка):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        
        # Кнопка вставки из буфера обмена
        ttk.Button(main_frame, text="Вставить", command=self.paste_from_clipboard).grid(row=2, column=2, pady=5, padx=(0, 5))
        
        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Скачать и установить", command=self.download_and_install).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Установить из файла", command=self.install_from_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить все моды", command=self.delete_all_mods).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить папку загрузок", command=self.cleanup_downloads).pack(side=tk.LEFT, padx=5)
        
        # Кнопки меню
        menu_frame = ttk.Frame(main_frame)
        menu_frame.grid(row=4, column=0, columnspan=4, pady=5)
        
        ttk.Button(menu_frame, text="О программе", command=self.show_about).pack(side=tk.LEFT, padx=5)
        ttk.Button(menu_frame, text="Настройки", command=self.show_settings).pack(side=tk.LEFT, padx=5)
        
        # Прогресс бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Статус
        self.status_var = tk.StringVar(value="Готов к работе")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=6, column=0, columnspan=4, pady=5)
        
        # Лог
        ttk.Label(main_frame, text="Лог операций:").grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.log_text.grid(row=8, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(8, weight=1)
        
        # Область для drag-and-drop
        drop_frame = ttk.LabelFrame(main_frame, text="Перетащите файлы модов сюда", padding="10")
        drop_frame.grid(row=9, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        # Создаем виджет для приема файлов
        if DND_AVAILABLE:
            self.drop_text = tk.Text(drop_frame, height=3, width=80, wrap=tk.WORD, state=tk.DISABLED,
                                   bg="lightgray", fg="black", font=("Arial", 10))
            self.drop_text.pack(fill=tk.BOTH, expand=True)
            self.drop_text.tag_configure("center", justify="center")
            
            # Включаем DnD
            self.drop_text.drop_target_register(DND_FILES)
            self.drop_text.dnd_bind('<<Drop>>', self.on_drop_files)
            
            # Добавляем обработку наведения
            self.drop_text.dnd_bind('<<DragEnter>>', self.on_drag_enter)
            self.drop_text.dnd_bind('<<DragLeave>>', self.on_drag_leave)
        else:
            self.drop_label = ttk.Label(drop_frame, 
                                       text="Поддерживаемые форматы: .package, .ts4script, .zip, .7z, .rar\n" +
                                            "Для установки файлов кликните здесь или используйте кнопку 'Установить из файла'",
                                       foreground="gray")
            self.drop_label.pack()
            self.drop_label.bind('<Button-1>', lambda e: self.select_files_for_drop())
        
        # Настройка drag-and-drop
        self.setup_drag_drop()
        
        # Автоматическая установка
        auto_frame = ttk.LabelFrame(main_frame, text="Автоматическая установка", padding="5")
        auto_frame.grid(row=10, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        self.auto_install_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(auto_frame, text="Включить автоматическую установку из списка URL", 
                       variable=self.auto_install_var).pack(anchor=tk.W)
        
        ttk.Button(auto_frame, text="Добавить URL в список", command=self.add_url_to_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(auto_frame, text="Показать список", command=self.show_url_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(auto_frame, text="Запустить автоустановку", command=self.start_auto_install).pack(side=tk.LEFT, padx=5)
    
    def setup_drag_drop(self):
        """Настройка drag-and-drop"""
        if DND_AVAILABLE:
            self.update_drop_text("Перетащите файлы модов сюда\n" +
                                "Поддерживаемые форматы: .package, .ts4script, .zip, .7z, .rar, .exe")
        else:
            # Альтернативный метод для систем без поддержки dnd
            if hasattr(self, 'drop_label'):
                self.drop_label.bind('<Button-1>', lambda e: self.select_files_for_drop())
    
    def update_drop_text(self, text):
        """Обновление текста в области drag-and-drop"""
        if hasattr(self, 'drop_text'):
            self.drop_text.config(state=tk.NORMAL)
            self.drop_text.delete(1.0, tk.END)
            self.drop_text.insert(tk.END, text)
            self.drop_text.tag_add("center", "1.0", "end")
            self.drop_text.config(state=tk.DISABLED)
    
    def on_drag_enter(self, event):
        """Обработка наведения мыши при перетаскивании"""
        self.update_drop_text("Отпустите файлы для установки...")
        self.drop_text.config(bg="lightgreen")
    
    def on_drag_leave(self, event):
        """Обработка ухода мыши при перетаскивании"""
        self.update_drop_text("Перетащите файлы модов сюда\n" +
                              "Поддерживаемые форматы: .package, .ts4script, .zip, .7z, .rar, .exe")
        self.drop_text.config(bg="lightgray")
    
    def on_drop_files(self, event):
        """Обработка перетаскивания файлов"""
        try:
            files = self.root.tk.splitlist(event.data)
            # Преобразование путей в правильный формат
            processed_files = []
            for file_path in files:
                # Удаляем фигурные скобки если есть
                if file_path.startswith('{') and file_path.endswith('}'):
                    file_path = file_path[1:-1]
                # Преобразуем в нормальный путь
                file_path = os.path.normpath(file_path)
                if os.path.exists(file_path):
                    processed_files.append(file_path)
            
            self.drop_text.config(bg="lightgray")
            self.process_dropped_files(processed_files)
        except Exception as e:
            self.log_message(f"Ошибка drag-and-drop: {str(e)}")
            self.update_drop_text("Ошибка! Попробуйте снова.")
    
    def select_files_for_drop(self):
        """Выбор файлов через диалог (альтернатива drag-and-drop)"""
        files = filedialog.askopenfilenames(
            title="Выберите файлы модов",
            filetypes=[
                ("Все поддерживаемые форматы", "*.package *.ts4script *.zip *.7z *.rar *.exe"),
                ("Моды Sims 4", "*.package *.ts4script"),
                ("Архивы", "*.zip *.7z *.rar"),
                ("Инсталляторы", "*.exe"),
                ("Все файлы", "*.*")
            ]
        )
        if files:
            self.process_dropped_files(list(files))
    
    def process_dropped_files(self, files):
        """Обработка перетянутых файлов"""
        if not self.mods_path:
            messagebox.showerror("Ошибка", "Папка модов не найдена!")
            return
        
        # Расширенный список поддерживаемых форматов
        supported_extensions = ('.package', '.ts4script', '.zip', '.7z', '.rar', '.exe')
        valid_files = []
        
        for file_path in files:
            if file_path.lower().endswith(supported_extensions):
                valid_files.append(file_path)
            else:
                self.log_message(f"Неподдерживаемый формат: {file_path}")
        
        if valid_files:
            self.log_message(f"Обработка {len(valid_files)} файлов...")
            threading.Thread(target=self._install_multiple_files_thread, args=(valid_files,), daemon=True).start()
        else:
            messagebox.showwarning("Внимание", "Нет поддерживаемых файлов для установки")
    
    def _install_multiple_files_thread(self, files):
        """Поток для установки нескольких файлов"""
        try:
            total_files = len(files)
            for i, file_path in enumerate(files):
                try:
                    self.status_var.set(f"Установка файла {i+1}/{total_files}")
                    self.progress_var.set((i / total_files) * 100)
                    
                    self.install_mod_file(file_path)
                    self.log_message(f"Файл {i+1}/{total_files} установлен: {os.path.basename(file_path)}")
                    
                except Exception as e:
                    self.log_message(f"Ошибка установки {file_path}: {str(e)}")
            
            self.progress_var.set(100)
            self.status_var.set("Установка завершена!")
            messagebox.showinfo("Готово", f"Установлено файлов: {total_files}")
            
        except Exception as e:
            self.log_message(f"Ошибка при установке файлов: {str(e)}")
            self.status_var.set(f"Ошибка: {str(e)}")
    
    def log_message(self, message):
        """Добавление сообщения в лог"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            if hasattr(self, 'log_text'):
                self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.log_text.see(tk.END)
                self.root.update_idletasks()
            else:
                # Если интерфейс еще не создан, выводим в консоль
                print(f"[{timestamp}] {message}")
        except Exception as e:
            # Если произошла ошибка, выводим в консоль
            print(f"[LOG ERROR] {message}")
    
    def show_about(self):
        """Показать окно 'О программе'"""
        about_window = tk.Toplevel(self.root)
        about_window.title("О программе")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Центрирование окна
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (about_window.winfo_screenheight() // 2) - (400 // 2)
        about_window.geometry(f"500x400+{x}+{y}")
        
        main_frame = ttk.Frame(about_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Название и версия
        title_label = ttk.Label(main_frame, text=self.app_name, font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        version_label = ttk.Label(main_frame, text=f"Версия: {self.app_version}", font=("Arial", 12))
        version_label.pack(pady=(0, 20))
        
        # Информация о программе
        info_text = """Автоматический установщик модов для The Sims 4

Создан для быстрой и удобной установки модов без участия пользователя.

Основные возможности:
• Настоящий drag-and-drop файлов
• Автоматический поиск игры и папки модов
• Скачивание модов по прямым ссылкам
• Установка из локальных файлов
• Расширенная поддержка архивов
• Автоматическая установка из списка URL
• Удаление всех модов одним кликом

Поддерживаемые форматы:
• .package - основные файлы модов
• .ts4script - скриптовые моды
• .zip - ZIP архивы
• .7z - 7-Zip архивы
• .rar - RAR архивы
• .exe - инсталляторы и SFX архивы"""
        
        info_label = ttk.Label(main_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(pady=(0, 20), anchor=tk.W)
        
        # Автор и дата
        author_label = ttk.Label(main_frame, text="© 2024 Sims 4 Mod Installer", font=("Arial", 10))
        author_label.pack(pady=(0, 10))
        
        # Кнопка закрытия
        ttk.Button(main_frame, text="Закрыть", command=about_window.destroy).pack(pady=10)
    
    def show_settings(self):
        """Показать окно настроек"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки")
        settings_window.geometry("600x500")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Центрирование окна
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (settings_window.winfo_screenheight() // 2) - (500 // 2)
        settings_window.geometry(f"600x500+{x}+{y}")
        
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Настройки путей
        path_frame = ttk.LabelFrame(main_frame, text="Пути", padding="10")
        path_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(path_frame, text="Путь к The Sims 4:").grid(row=0, column=0, sticky=tk.W, pady=5)
        sims4_var = tk.StringVar(value=self.sims4_path or "Не указан")
        ttk.Entry(path_frame, textvariable=sims4_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        ttk.Button(path_frame, text="Обзор...", command=lambda: self.browse_path_setting(sims4_var, "sims4")).grid(row=0, column=2, pady=5, padx=(5, 0))
        
        ttk.Label(path_frame, text="Папка модов:").grid(row=1, column=0, sticky=tk.W, pady=5)
        mods_var = tk.StringVar(value=self.mods_path or "Будет определен автоматически")
        ttk.Entry(path_frame, textvariable=mods_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        ttk.Button(path_frame, text="Обзор...", command=lambda: self.browse_path_setting(mods_var, "mods")).grid(row=1, column=2, pady=5, padx=(5, 0))
        
        path_frame.columnconfigure(1, weight=1)
        
        # Настройки скачивания
        download_frame = ttk.LabelFrame(main_frame, text="Настройки скачивания", padding="10")
        download_frame.pack(fill=tk.X, pady=(0, 20))
        
        timeout_var = tk.IntVar(value=getattr(self, 'download_timeout', 30))
        ttk.Label(download_frame, text="Таймаут скачивания (сек):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(download_frame, from_=10, to=300, textvariable=timeout_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        retry_var = tk.IntVar(value=getattr(self, 'max_retries', 3))
        ttk.Label(download_frame, text="Макс. попыток скачивания:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(download_frame, from_=1, to=10, textvariable=retry_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Настройки интерфейса
        ui_frame = ttk.LabelFrame(main_frame, text="Интерфейс", padding="10")
        ui_frame.pack(fill=tk.X, pady=(0, 20))
        
        auto_cleanup_var = tk.BooleanVar(value=getattr(self, 'auto_cleanup_downloads', False))
        ttk.Checkbutton(ui_frame, text="Автоматически очищать папку загрузок", variable=auto_cleanup_var).pack(anchor=tk.W, pady=5)
        
        confirm_delete_var = tk.BooleanVar(value=getattr(self, 'confirm_delete', True))
        ttk.Checkbutton(ui_frame, text="Подтверждать удаление модов", variable=confirm_delete_var).pack(anchor=tk.W, pady=5)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_settings():
            self.sims4_path = sims4_var.get()
            self.mods_path = mods_var.get()
            self.download_timeout = timeout_var.get()
            self.max_retries = retry_var.get()
            self.auto_cleanup_downloads = auto_cleanup_var.get()
            self.confirm_delete = confirm_delete_var.get()
            
            self.path_var.set(self.sims4_path)
            self.mods_path_var.set(self.mods_path)
            
            self.save_settings()
            messagebox.showinfo("Готово", "Настройки сохранены!")
            settings_window.destroy()
        
        ttk.Button(button_frame, text="Сохранить", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=settings_window.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Сбросить", command=lambda: self.reset_settings(settings_window)).pack(side=tk.RIGHT, padx=5)
    
    def browse_path_setting(self, var, path_type):
        """Выбор пути в настройках"""
        if path_type == "sims4":
            folder = filedialog.askdirectory(title="Выберите папку с The Sims 4")
        else:
            folder = filedialog.askdirectory(title="Выберите папку модов")
        
        if folder:
            var.set(folder)
    
    def reset_settings(self, window):
        """Сброс настроек"""
        if messagebox.askyesno("Сброс настроек", "Сбросить все настройки к значениям по умолчанию?"):
            self.sims4_path = ""
            self.mods_path = ""
            self.download_timeout = 30
            self.max_retries = 3
            self.auto_cleanup_downloads = False
            self.confirm_delete = True
            
            self.save_settings()
            window.destroy()
            messagebox.showinfo("Готово", "Настройки сброшены!")
    
    def paste_from_clipboard(self):
        """Вставка URL из буфера обмена"""
        try:
            # Пытаемся получить текст из буфера обмена
            clipboard_text = self.root.clipboard_get()
            
            # Проверяем что это URL
            if clipboard_text and (clipboard_text.startswith('http://') or clipboard_text.startswith('https://')):
                self.url_var.set(clipboard_text)
                self.log_message(f"URL вставлен из буфера обмена: {clipboard_text}")
                # Устанавливаем фокус на поле URL
                self.url_entry.focus()
            else:
                # Если это не URL, показываем диалог с возможностью вставить всё равно
                result = messagebox.askyesno(
                    "Проверка URL", 
                    f"Текст в буфере обмена не похож на URL:\n\n{clipboard_text[:100]}...\n\nВставить всё равно?",
                    icon='question'
                )
                if result:
                    self.url_var.set(clipboard_text)
                    self.log_message(f"Текст вставлен из буфера обмена: {clipboard_text[:100]}...")
                    self.url_entry.focus()
        except Exception as e:
            self.log_message(f"Ошибка при вставке из буфера обмена: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось вставить из буфера обмена: {str(e)}")
    
    def find_sims4_path(self):
        """Расширенный поиск The Sims 4 включая пиратские версии"""
        found_paths = []
        
        try:
            self.log_message("Начало расширенного поиска игры...")
            
            # 1. Поиск в реестре (официальные версии)
            registry_paths = [
                r"SOFTWARE\Maxis\The Sims 4",
                r"SOFTWARE\WOW6432Node\Maxis\The Sims 4",
                r"SOFTWARE\Electronic Arts\The Sims 4",
                r"SOFTWARE\WOW6432Node\Electronic Arts\The Sims 4",
                r"SOFTWARE\Origin\The Sims 4",
                r"SOFTWARE\WOW6432Node\Origin\The Sims 4"
            ]
            
            for reg_path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        install_dir = winreg.QueryValueEx(key, "Install Dir")[0]
                        if os.path.exists(install_dir):
                            found_paths.append(("Registry", install_dir))
                            self.log_message(f"Найдена игра в реестре: {install_dir}")
                except (WindowsError, FileNotFoundError):
                    continue
            
            # 2. Поиск в стандартных местах (официальные)
            standard_paths = [
                r"C:\Program Files (x86)\Origin Games\The Sims 4",
                r"C:\Program Files\Origin Games\The Sims 4",
                r"C:\Program Files (x86)\EA Games\The Sims 4",
                r"C:\Program Files\EA Games\The Sims 4",
                r"C:\Program Files (x86)\Steam\steamapps\common\The Sims 4",
                r"C:\Program Files\Steam\steamapps\common\The Sims 4"
            ]
            
            for path in standard_paths:
                if os.path.exists(path):
                    found_paths.append(("Official", path))
                    self.log_message(f"Найдена игра в стандартной папке: {path}")
            
            # 3. Поиск пиратских версий и лаунчеров
            pirate_paths = [
                # Игровые диски и папки
                r"C:\Games\The Sims 4",
                r"D:\Games\The Sims 4", 
                r"E:\Games\The Sims 4",
                r"F:\Games\The Sims 4",
                r"G:\Games\The Sims 4",
                
                # Прямые пути в корне дисков
                r"C:\The Sims 4",
                r"D:\The Sims 4",
                r"E:\The Sims 4", 
                r"F:\The Sims 4",
                r"G:\The Sims 4",
                
                # Популярные репаки
                r"C:\Games\Sims 4",
                r"D:\Games\Sims 4",
                r"E:\Games\Sims 4",
                r"F:\Games\Sims 4",
                r"G:\Games\Sims 4",
                
                # Модифицированные названия
                r"C:\Games\The.Sims.4",
                r"D:\Games\The.Sims.4",
                r"E:\Games\The.Sims.4",
                r"C:\Games\TS4",
                r"D:\Games\TS4",
                r"E:\Games\TS4",
                
                # Пиратские лаунчеры и сборки
                r"C:\Games\Sims 4 REPACK",
                r"D:\Games\Sims 4 REPACK",
                r"E:\Games\Sims 4 REPACK",
                r"C:\Games\The Sims 4 REPACK",
                r"D:\Games\The Sims 4 REPACK",
                r"C:\Games\Sims.4.by.[R.G.Mechanics]",
                r"D:\Games\Sims.4.by.[R.G.Mechanics]",
                r"C:\Games\The.Sims.4.by.[R.G.Mechanics]",
                r"D:\Games\The.Sims.4.by.[R.G.Mechanics]",
                r"C:\Games\Sims 4 [FitGirl]",
                r"D:\Games\Sims 4 [FitGirl]",
                r"E:\Games\Sims 4 [FitGirl]",
                r"C:\Games\The Sims 4 [FitGirl]",
                r"D:\Games\The Sims 4 [FitGirl]",
                r"C:\Games\Sims 4 [CODEX]",
                r"D:\Games\Sims 4 [CODEX]",
                r"E:\Games\Sims 4 [CODEX]",
                r"C:\Games\The Sims 4 [CODEX]",
                r"D:\Games\The Sims 4 [CODEX]",
                r"C:\Games\Sims 4 [CPY]",
                r"D:\Games\Sims 4 [CPY]",
                r"E:\Games\Sims 4 [CPY]",
                r"C:\Games\The Sims 4 [CPY]",
                r"D:\Games\The Sims 4 [CPY]",
                r"C:\Games\Sims 4 [SKIDROW]",
                r"D:\Games\Sims 4 [SKIDROW]",
                r"E:\Games\Sims 4 [SKIDROW]",
                r"C:\Games\The Sims 4 [SKIDROW]",
                r"D:\Games\The Sims 4 [SKIDROW]",
                
                # Лаунчеры пиратских сборок
                r"C:\Games\Sims4Launcher",
                r"D:\Games\Sims4Launcher",
                r"E:\Games\Sims4Launcher",
                r"C:\Games\TS4_Launcher",
                r"D:\Games\TS4_Launcher",
                r"E:\Games\TS4_Launcher",
                r"C:\Games\TheSims4Launcher",
                r"D:\Games\TheSims4Launcher",
                r"C:\Games\Sims4_Crack",
                r"D:\Games\Sims4_Crack",
                r"E:\Games\Sims4_Crack",
                
                # Папки загрузок и временные папки
                r"C:\Users\%USERNAME%\Downloads\The Sims 4",
                r"C:\Users\%USERNAME%\Desktop\The Sims 4",
                r"C:\Users\%USERNAME%\Downloads\Sims 4",
                r"C:\Users\%USERNAME%\Downloads\TS4",
                
                # Программные папки
                r"C:\Program Files\The Sims 4",
                r"C:\Program Files (x86)\The Sims 4",
                r"D:\Program Files\The Sims 4",
                r"D:\Program Files (x86)\The Sims 4",
                
                # TorGames и другие пиратские площадки
                r"C:\TorGames\The Sims 4",
                r"D:\TorGames\The Sims 4",
                r"E:\TorGames\The Sims 4",
                r"C:\Torgames\The Sims 4",
                r"D:\Torgames\The Sims 4",
                r"C:\Games\The Sims 4 [SteamRip]",
                r"D:\Games\The Sims 4 [SteamRip]",
                r"E:\Games\The Sims 4 [SteamRip]"
            ]
            
            # Заменяем переменную окружения
            username = os.path.expanduser("~").split("\\")[-1]
            for i, path in enumerate(pirate_paths):
                pirate_paths[i] = path.replace("%USERNAME%", username)
            
            for path in pirate_paths:
                if os.path.exists(path):
                    found_paths.append(("Pirate", path))
                    self.log_message(f"Найдена пиратская версия: {path}")
            
            # 4. Рекурсивный поиск по всем дискам
            self.log_message("Выполняю рекурсивный поиск по дискам...")
            drives = self._get_available_drives()
            
            for drive in drives:
                try:
                    found_path = self._recursive_search_sims4(drive + "\\", max_depth=3)
                    if found_path:
                        found_paths.append(("Deep Search", found_path))
                        self.log_message(f"Найдена рекурсивным поиском: {found_path}")
                except Exception as e:
                    self.log_message(f"Ошибка поиска на диске {drive}: {str(e)}")
                    continue
            
            # 5. Поиск лаунчеров по exe файлам
            self.log_message("Ищу пиратские лаунчеры...")
            launcher_paths = self._find_pirate_launchers(drives)
            for launcher_path in launcher_paths:
                found_paths.append(("Launcher", launcher_path))
                self.log_message(f"Найден лаунчер: {launcher_path}")
            
            # 6. Поиск по папкам с похожими названиями
            self.log_message("Ищу папки с похожими названиями...")
            common_folders = [
                "Games", "Игры", "Program Files", "Program Files (x86)",
                "Downloads", "Загрузки", "Desktop", "Рабочий стол",
                "TorGames", "Torgames", "Torrents", "Репаки"
            ]
            
            for drive in drives:
                for folder in common_folders:
                    folder_path = os.path.join(drive, folder)
                    if os.path.exists(folder_path):
                        found_path = self._search_in_directory(folder_path, "sims")
                        if found_path:
                            found_paths.append(("Folder Search", found_path))
                            self.log_message(f"Найдена в папке {folder}: {found_path}")
            
            # Возвращаем лучший найденный путь
            if found_paths:
                # Приоритет: Registry > Official > Pirate > Deep Search > Folder Search
                priority_order = {"Registry": 0, "Official": 1, "Pirate": 2, "Deep Search": 3, "Folder Search": 4}
                found_paths.sort(key=lambda x: priority_order.get(x[0], 99))
                
                best_path = found_paths[0][1]
                self.log_message(f"Выбран лучший путь: {best_path} (источник: {found_paths[0][0]})")
                
                # Если найдено несколько путей, сообщаем об этом
                if len(found_paths) > 1:
                    self.log_message(f"Всего найдено путей: {len(found_paths)}")
                    for source, path in found_paths[1:3]:  # Показываем еще 2 пути
                        self.log_message(f"  Также найдено: {path} ({source})")
                
                return best_path
            
            self.log_message("Игра не найдена. Укажите путь вручную.")
            return ""
            
        except Exception as e:
            self.log_message(f"Ошибка при поиске игры: {str(e)}")
            return ""
    
    def _get_available_drives(self):
        """Получение списка доступных дисков"""
        drives = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                drives.append(drive_path)
        return drives
    
    def _recursive_search_sims4(self, start_path, max_depth=3, current_depth=0):
        """Рекурсивный поиск папки The Sims 4"""
        if current_depth >= max_depth:
            return None
        
        try:
            items = os.listdir(start_path)
        except (PermissionError, OSError):
            return None
        
        for item in items:
            item_path = os.path.join(start_path, item)
            
            try:
                if os.path.isdir(item_path):
                    # Проверяем если это папка с игрой
                    if self._is_sims4_folder(item_path):
                        return item_path
                    
                    # Рекурсивный поиск
                    result = self._recursive_search_sims4(item_path, max_depth, current_depth + 1)
                    if result:
                        return result
            except (PermissionError, OSError):
                continue
        
        return None
    
    def _search_in_directory(self, directory, keyword):
        """Поиск папок с ключевым словом"""
        try:
            items = os.listdir(directory)
        except (PermissionError, OSError):
            return None
        
        for item in items:
            item_path = os.path.join(directory, item)
            
            try:
                if os.path.isdir(item_path):
                    # Проверяем название папки
                    if keyword.lower() in item.lower():
                        if self._is_sims4_folder(item_path):
                            return item_path
            except (PermissionError, OSError):
                continue
        
        return None
    
    def _find_pirate_launchers(self, drives):
        """Поиск пиратских лаунчеров по exe файлам"""
        launcher_paths = []
        
        # Имена exe файлов лаунчеров
        launcher_names = [
            "Sims4Launcher.exe",
            "TS4_Launcher.exe", 
            "TheSims4Launcher.exe",
            "Sims4.exe",
            "TS4.exe",
            "Launcher.exe",
            "Start.exe",
            "Sims4_Crack.exe",
            "Sims4-Repack.exe",
            "The Sims 4.exe",
            "TheSims4.exe",
            "TS4_x64.exe",
            "Sims4_x64.exe"
        ]
        
        # Популярные папки для лаунчеров
        launcher_folders = [
            "Games", "Игры", "TorGames", "Torgames", "Torrents", "Репаки",
            "Program Files", "Program Files (x86)", "Downloads", "Загрузки",
            "Desktop", "Рабочий стол"
        ]
        
        for drive in drives:
            # Поиск в корне диска
            for launcher_name in launcher_names:
                launcher_path = os.path.join(drive, launcher_name)
                if os.path.exists(launcher_path):
                    # Проверяем что это лаунчер Sims 4
                    if self._is_sims4_launcher(launcher_path):
                        launcher_paths.append(os.path.dirname(launcher_path))
            
            # Поиск в папках
            for folder in launcher_folders:
                folder_path = os.path.join(drive, folder)
                if os.path.exists(folder_path):
                    try:
                        items = os.listdir(folder_path)
                        for item in items:
                            item_path = os.path.join(folder_path, item)
                            if os.path.isfile(item_path) and item.endswith('.exe'):
                                if any(name.lower() in item.lower() for name in launcher_names):
                                    if self._is_sims4_launcher(item_path):
                                        launcher_paths.append(folder_path)
                                        break
                    except (PermissionError, OSError):
                        continue
        
        return launcher_paths
    
    def _is_sims4_launcher(self, exe_path):
        """Проверка что exe файл является лаунчером Sims 4"""
        try:
            # Проверяем размер файла (лаунчеры обычно не очень большие)
            file_size = os.path.getsize(exe_path)
            if file_size > 100 * 1024 * 1024:  # больше 100MB - скорее всего сама игра
                return False
            
            # Проверяем название файла
            filename = os.path.basename(exe_path).lower()
            launcher_keywords = [
                "sims4", "ts4", "sims 4", "the sims 4", "launcher", 
                "crack", "repack", "start"
            ]
            
            if not any(keyword in filename for keyword in launcher_keywords):
                return False
            
            # Проверяем папку на наличие файлов Sims 4
            folder_path = os.path.dirname(exe_path)
            return self._is_sims4_folder(folder_path)
            
        except Exception:
            return False
    
    def _is_sims4_folder(self, folder_path):
        """Расширенная проверка что папка содержит The Sims 4"""
        # Проверяем по исполняемым файлам
        exe_paths = [
            os.path.join(folder_path, "Game", "Bin", "TS4_x64.exe"),
            os.path.join(folder_path, "Game", "Bin", "TS4.exe"),
            os.path.join(folder_path, "TS4_x64.exe"),
            os.path.join(folder_path, "TS4.exe"),
            os.path.join(folder_path, "Bin", "TS4_x64.exe"),
            os.path.join(folder_path, "Bin", "TS4.exe"),
            os.path.join(folder_path, "Sims4.exe"),
            os.path.join(folder_path, "Sims4Launcher.exe"),
            os.path.join(folder_path, "TS4_Launcher.exe"),
            os.path.join(folder_path, "TheSims4Launcher.exe"),
            os.path.join(folder_path, "The Sims 4.exe"),
            os.path.join(folder_path, "Launcher.exe")
        ]
        
        for exe_path in exe_paths:
            if os.path.exists(exe_path):
                return True
        
        # Проверяем по характерным папкам (для пиратских версий)
        subfolders = [
            "Game", "Data", "Delta", "__Installer", "Bin", "Support", 
            "crack", "CODEX", "CPY", "SKIDROW", "REPACK", "FitGirl", "Mechanics"
        ]
        found_subfolders = 0
        
        try:
            items = os.listdir(folder_path)
            for item in items:
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    if item in subfolders:
                        found_subfolders += 1
                    # Проверяем папки с похожими названиями
                    elif any(keyword.lower() in item.lower() for keyword in ["game", "data", "bin", "support"]):
                        found_subfolders += 0.5
        except (PermissionError, OSError):
            pass
        
        # Если найдено 2 или более характерных папок
        if found_subfolders >= 2:
            return True
        
        # Дополнительная проверка по файлам
        try:
            items = os.listdir(folder_path)
            for item in items:
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    filename = item.lower()
                    # Проверяем по характерным файлам
                    if any(keyword in filename for keyword in [
                        "sims4", "ts4", "thecims", "gameplay", "startup"
                    ]) and filename.endswith('.exe'):
                        return True
                    # Проверяем по конфигурационным файлам
                    if filename in ["sims4.ini", "ts4.ini", "game.ini"] or \
                       filename.endswith(".dll") and "sims" in filename:
                        found_subfolders += 0.5
        except (PermissionError, OSError):
            pass
        
        return found_subfolders >= 2.5
    
    def find_documents_folder(self):
        """Поиск папки Documents"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                return winreg.QueryValueEx(key, "Personal")[0]
        except:
            return os.path.join(os.path.expanduser("~"), "Documents")
    
    def auto_find_sims4(self):
        """Автоматический поиск игры и папки модов"""
        self.status_var.set("Поиск игры...")
        
        sims4_path = self.find_sims4_path()
        if sims4_path:
            self.sims4_path = sims4_path
            self.path_var.set(sims4_path)
            
            # Поиск папки модов
            documents_path = self.find_documents_folder()
            mods_path = os.path.join(documents_path, "Electronic Arts", "The Sims 4", "Mods")
            
            if os.path.exists(mods_path):
                self.mods_path = mods_path
                self.mods_path_var.set(mods_path)
                self.log_message(f"Папка модов найдена: {mods_path}")
            else:
                # Создаем папку модов если ее нет
                try:
                    os.makedirs(mods_path, exist_ok=True)
                    self.mods_path = mods_path
                    self.mods_path_var.set(mods_path)
                    self.log_message(f"Папка модов создана: {mods_path}")
                except:
                    self.log_message("Не удалось создать папку модов")
            
            self.status_var.set("Игра найдена успешно!")
            self.save_settings()
        else:
            self.status_var.set("Игра не найдена. Укажите путь вручную.")
            self.log_message("Игра The Sims 4 не найдена. Пожалуйста, укажите путь вручную.")
    
    def browse_sims4(self):
        """Выбор папки с игрой"""
        folder = filedialog.askdirectory(title="Выберите папку с The Sims 4")
        if folder:
            self.sims4_path = folder
            self.path_var.set(folder)
            
            # Обновляем путь к модам
            documents_path = self.find_documents_folder()
            mods_path = os.path.join(documents_path, "Electronic Arts", "The Sims 4", "Mods")
            
            if not os.path.exists(mods_path):
                os.makedirs(mods_path, exist_ok=True)
            
            self.mods_path = mods_path
            self.mods_path_var.set(mods_path)
            self.save_settings()
            self.log_message(f"Выбран путь к игре: {folder}")
    
    def download_and_install(self):
        """Скачивание и установка мода"""
        if not self.mods_path:
            messagebox.showerror("Ошибка", "Папка модов не найдена!")
            return
        
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Ошибка", "Введите URL мода!")
            return
        
        # Запускаем в отдельном потоке
        threading.Thread(target=self._download_and_install_thread, args=(url,), daemon=True).start()
    
    def _download_and_install_thread(self, url):
        """Поток для скачивания и установки с улучшенной обработкой"""
        try:
            self.status_var.set("Скачивание мода...")
            self.progress_var.set(0)
            
            # Улучшенная обработка URL
            filename = self._extract_filename_from_url(url)
            download_path = os.path.join(self.download_folder, filename)
            
            self.log_message(f"Скачивание: {url}")
            
            # Настройки сессии
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Попытки скачивания с повторами
            max_retries = getattr(self, 'max_retries', 3)
            timeout = getattr(self, 'download_timeout', 30)
            
            for attempt in range(max_retries):
                try:
                    response = session.get(url, stream=True, timeout=timeout)
                    response.raise_for_status()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    self.log_message(f"Попытка {attempt + 1} не удалась, повторяю...")
                    time.sleep(2 ** attempt)  # Экспоненциальная задержка
            
            # Определение размера файла
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 50
                            self.progress_var.set(progress)
            
            self.log_message(f"Файл скачан: {download_path} ({downloaded / 1024 / 1024:.1f} MB)")
            
            # Установка
            self.status_var.set("Установка мода...")
            self.install_mod_file(download_path)
            
            # Автоочистка если включена
            if getattr(self, 'auto_cleanup_downloads', False):
                try:
                    os.remove(download_path)
                    self.log_message("Временный файл удален")
                except:
                    pass
            
            self.progress_var.set(100)
            self.status_var.set("Мод установлен успешно!")
            
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")
            self.status_var.set(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось установить мод: {str(e)}")
    
    def _extract_filename_from_url(self, url):
        """Извлечение имени файла из URL с улучшенной обработкой"""
        try:
            # Базовое извлечение из URL
            filename = os.path.basename(urlparse(url).path)
            
            if filename and '.' in filename:
                return filename
            
            # Если не получилось, пробуем получить из заголовков
            try:
                response = requests.head(url, timeout=10)
                content_disp = response.headers.get('content-disposition', '')
                if 'filename=' in content_disp:
                    filename = content_disp.split('filename=')[-1].strip('"')
                    if filename and '.' in filename:
                        return filename
            except:
                pass
            
            # Генерируем имя файла на основе домена
            domain = urlparse(url).netloc.replace('.', '_')
            timestamp = int(time.time())
            
            # Определяем расширение по URL или типу контента
            ext = '.zip'  # по умолчанию
            if url.lower().endswith(('.package', '.ts4script')):
                ext = os.path.splitext(url)[1]
            
            return f"mod_{domain}_{timestamp}{ext}"
            
        except Exception:
            return f"mod_{int(time.time())}.zip"
    
    def install_mod_file(self, file_path):
        """Установка мода из файла с поддержкой расширенных форматов"""
        try:
            self.log_message(f"Установка файла: {file_path}")
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.zip':
                self._install_zip_file(file_path)
            elif file_ext == '.7z':
                self._install_7z_file(file_path)
            elif file_ext == '.rar':
                self._install_rar_file(file_path)
            elif file_ext == '.exe':
                self._install_exe_file(file_path)
            elif file_ext in ('.package', '.ts4script'):
                self._install_direct_file(file_path)
            else:
                self.log_message(f"Неподдерживаемый формат файла: {file_ext}")
            
        except Exception as e:
            raise Exception(f"Ошибка установки: {str(e)}")
    
    def _install_zip_file(self, file_path):
        """Установка ZIP архива"""
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            temp_dir = os.path.join(self.download_folder, f"temp_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            zip_ref.extractall(temp_dir)
            self.log_message(f"ZIP архив распакован в: {temp_dir}")
            
            self._extract_mod_files_from_dir(temp_dir)
            shutil.rmtree(temp_dir)
    
    def _install_7z_file(self, file_path):
        """Установка 7Z архива"""
        if not PY7Z_AVAILABLE:
            raise Exception("Библиотека py7zr не установлена. Установите: pip install py7zr")
        
        try:
            temp_dir = os.path.join(self.download_folder, f"temp_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            with py7zr.SevenZipFile(file_path, mode='r') as archive:
                archive.extractall(temp_dir)
                self.log_message(f"7Z архив распакован в: {temp_dir}")
            
            self._extract_mod_files_from_dir(temp_dir)
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            raise Exception(f"Ошибка распаковки 7Z: {str(e)}")
    
    def _install_rar_file(self, file_path):
        """Установка RAR архива"""
        if not RAR_AVAILABLE:
            raise Exception("Библиотека rarfile не установлена. Установите: pip install rarfile")
        
        try:
            temp_dir = os.path.join(self.download_folder, f"temp_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            with rarfile.RarFile(file_path, 'r') as archive:
                archive.extractall(temp_dir)
                self.log_message(f"RAR архив распакован в: {temp_dir}")
            
            self._extract_mod_files_from_dir(temp_dir)
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            raise Exception(f"Ошибка распаковки RAR: {str(e)}")
    
    def _install_exe_file(self, file_path):
        """Обработка EXE инсталлятора"""
        try:
            # Проверяем, это может быть SFX архив
            if self._is_sfx_archive(file_path):
                self.log_message("Обнаружен SFX архив, пытаюсь распаковать...")
                self._try_extract_sfx(file_path)
            else:
                # Для обычных EXE предлагаем ручную установку
                result = messagebox.askyesno(
                    "Инсталлятор",
                    f"Файл {os.path.basename(file_path)} является инсталлятором.\n\n" +
                    "Рекомендуется запустить его вручную и выбрать папку модов:\n" +
                    f"{self.mods_path}\n\n" +
                    "Открыть папку модов?",
                    icon='question'
                )
                
                if result:
                    os.startfile(self.mods_path)
                    # Также пытаемся запустить инсталлятор
                    try:
                        os.startfile(file_path)
                        self.log_message(f"Запущен инсталлятор: {file_path}")
                    except:
                        pass
        
        except Exception as e:
            raise Exception(f"Ошибка обработки EXE: {str(e)}")
    
    def _install_direct_file(self, file_path):
        """Прямое копирование файла мода"""
        filename = os.path.basename(file_path)
        dst = os.path.join(self.mods_path, filename)
        
        # Если файл уже существует, добавляем номер
        counter = 1
        original_dst = dst
        while os.path.exists(dst):
            name, ext = os.path.splitext(original_dst)
            dst = f"{name}_{counter}{ext}"
            counter += 1
        
        shutil.copy2(file_path, dst)
        self.log_message(f"Файл установлен: {os.path.basename(dst)}")
        self.progress_var.set(75)
    
    def _extract_mod_files_from_dir(self, temp_dir):
        """Извлечение файлов модов из временной папки"""
        moved_files = []
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith(('.package', '.ts4script')):
                    src = os.path.join(root, file)
                    dst = os.path.join(self.mods_path, file)
                    
                    # Если файл уже существует, добавляем номер
                    counter = 1
                    original_dst = dst
                    while os.path.exists(dst):
                        name, ext = os.path.splitext(original_dst)
                        dst = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    shutil.move(src, dst)
                    moved_files.append(os.path.basename(dst))
                    self.log_message(f"Файл установлен: {os.path.basename(dst)}")
        
        if moved_files:
            self.progress_var.set(75)
            self.log_message(f"Установлено файлов: {len(moved_files)}")
        else:
            self.log_message("В архиве не найдено .package или .ts4script файлов")
    
    def _is_sfx_archive(self, file_path):
        """Проверка, является ли EXE файлом SFX архивом"""
        try:
            with open(file_path, 'rb') as f:
                # Сигнатуры SFX архивов
                sfx_signatures = [
                    b'PK',           # ZIP SFX
                    b'7z\xbc\xaf',  # 7Z SFX
                    b'Rar!',        # RAR SFX
                    b'MZ',          # PE EXE (может быть SFX)
                ]
                
                header = f.read(1024)
                for sig in sfx_signatures:
                    if header.startswith(sig):
                        return True
                        
                return False
        except:
            return False
    
    def _try_extract_sfx(self, file_path):
        """Попытка извлечь SFX архив"""
        try:
            temp_dir = os.path.join(self.download_folder, f"temp_sfx_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Пробуем 7z командной строки
            try:
                subprocess.run(['7z', 'x', file_path, f'-o{temp_dir}', '-y'], 
                             check=True, capture_output=True)
                self.log_message("SFX архив успешно извлечен через 7z")
                self._extract_mod_files_from_dir(temp_dir)
                shutil.rmtree(temp_dir)
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Пробуем распаковать как ZIP
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    self.log_message("SFX архив успешно извлечен как ZIP")
                    self._extract_mod_files_from_dir(temp_dir)
                    shutil.rmtree(temp_dir)
                    return
            except:
                pass
            
            # Если не получилось, предлагаем ручную установку
            raise Exception("Не удалось автоматически извлечь SFX архив")
            
        except Exception as e:
            messagebox.showwarning(
                "SFX Архив",
                f"Не удалось извлечь SFX архив автоматически.\n" +
                f"Пожалуйста, извлеките архив вручную в папку:\n" +
                f"{self.mods_path}\n\n" +
                f"Ошибка: {str(e)}"
            )
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def install_from_file(self):
        """Установка мода из локального файла"""
        if not self.mods_path:
            messagebox.showerror("Ошибка", "Папка модов не найдена!")
            return
        
        file_path = filedialog.askopenfilename(
            title="Выберите файл мода",
            filetypes=[
                ("Все поддерживаемые форматы", "*.package *.ts4script *.zip *.7z *.rar *.exe"),
                ("Моды Sims 4", "*.package *.ts4script"),
                ("Архивы", "*.zip *.7z *.rar"),
                ("Инсталляторы", "*.exe"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            threading.Thread(target=self._install_from_file_thread, args=(file_path,), daemon=True).start()
    
    def _install_from_file_thread(self, file_path):
        """Поток для установки из файла"""
        try:
            self.status_var.set("Установка мода...")
            self.progress_var.set(25)
            
            self.install_mod_file(file_path)
            
            self.progress_var.set(100)
            self.status_var.set("Мод установлен успешно!")
            
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")
            self.status_var.set(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось установить мод: {str(e)}")
    
    def delete_all_mods(self):
        """Удаление всех установленных модов с настройкой"""
        if not self.mods_path:
            messagebox.showerror("Ошибка", "Папка модов не найдена!")
            return
        
        # Проверяем настройку подтверждения
        if getattr(self, 'confirm_delete', True):
            # Подтверждение удаления
            result = messagebox.askyesno(
                "Подтверждение удаления",
                "ВНИМАНИЕ! Это действие удалит ВСЕ моды из папки Mods!\n\n"
                "Все файлы .package и .ts4script будут безвозвратно удалены.\n\n"
                "Продолжить удаление?",
                icon='warning'
            )
            
            if not result:
                return
            
            # Дополнительное подтверждение
            result2 = messagebox.askyesno(
                "Окончательное подтверждение",
                "Вы уверены? Это действие нельзя отменить!\n\n"
                "Удалить все моды?",
                icon='warning'
            )
            
            if not result2:
                return
        
        # Запускаем удаление в отдельном потоке
        threading.Thread(target=self._delete_all_mods_thread, daemon=True).start()
    
    def _delete_all_mods_thread(self):
        """Поток для удаления всех модов"""
        try:
            self.status_var.set("Удаление всех модов...")
            self.progress_var.set(10)
            self.log_message("Начало удаления всех модов...")
            
            if not os.path.exists(self.mods_path):
                self.log_message("Папка модов не существует")
                self.status_var.set("Папка модов не найдена")
                return
            
            deleted_count = 0
            error_count = 0
            
            # Проходим по всем файлам в папке модов и подпапках
            for root, dirs, files in os.walk(self.mods_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Удаляем только файлы модов
                    if file.lower().endswith(('.package', '.ts4script')):
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            self.log_message(f"Удален: {file}")
                            
                            # Обновляем прогресс
                            progress = min(10 + (deleted_count * 80 // max(deleted_count + 1, 1)), 90)
                            self.progress_var.set(progress)
                            
                        except Exception as e:
                            error_count += 1
                            self.log_message(f"Ошибка удаления {file}: {str(e)}")
            
            # Удаляем пустые папки
            self.progress_var.set(90)
            self.log_message("Удаление пустых папок...")
            
            for root, dirs, files in os.walk(self.mods_path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        # Проверяем что папка пустая
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            self.log_message(f"Удалена пустая папка: {dir_name}")
                    except:
                        pass  # Папка не пустая или ошибка удаления
            
            self.progress_var.set(100)
            
            # Показываем результат
            message = f"Удаление завершено!\n\n"
            message += f"Удалено файлов: {deleted_count}\n"
            if error_count > 0:
                message += f"Ошибок: {error_count}\n"
            
            self.log_message(f"Удаление завершено. Удалено: {deleted_count}, ошибок: {error_count}")
            self.status_var.set("Удаление завершено")
            
            messagebox.showinfo("Готово", message)
            
        except Exception as e:
            self.log_message(f"Критическая ошибка при удалении: {str(e)}")
            self.status_var.set(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось удалить моды: {str(e)}")
    
    def cleanup_downloads(self):
        """Очистка папки загрузок"""
        try:
            if os.path.exists(self.download_folder):
                shutil.rmtree(self.download_folder)
                os.makedirs(self.download_folder, exist_ok=True)
                self.log_message("Папка загрузок очищена")
                messagebox.showinfo("Готово", "Папка загрузок очищена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить папку: {str(e)}")
    
    def add_url_to_list(self):
        """Добавление URL в список автоустановки"""
        url = self.url_var.get().strip()
        if url:
            # Загрузка списка
            try:
                with open("auto_install_urls.json", "r", encoding="utf-8") as f:
                    urls = json.load(f)
            except:
                urls = []
            
            if url not in urls:
                urls.append(url)
                
                with open("auto_install_urls.json", "w", encoding="utf-8") as f:
                    json.dump(urls, f, indent=2, ensure_ascii=False)
                
                self.log_message(f"URL добавлен в список: {url}")
                messagebox.showinfo("Готово", "URL добавлен в список автоустановки")
            else:
                messagebox.showwarning("Внимание", "Этот URL уже есть в списке")
    
    def show_url_list(self):
        """Показать список URL для автоустановки"""
        try:
            with open("auto_install_urls.json", "r", encoding="utf-8") as f:
                urls = json.load(f)
            
            list_window = tk.Toplevel(self.root)
            list_window.title("Список автоустановки")
            list_window.geometry("600x400")
            
            listbox = tk.Listbox(list_window)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for url in urls:
                listbox.insert(tk.END, url)
            
            def remove_selected():
                selection = listbox.curselection()
                if selection:
                    index = selection[0]
                    urls.pop(index)
                    
                    with open("auto_install_urls.json", "w", encoding="utf-8") as f:
                        json.dump(urls, f, indent=2, ensure_ascii=False)
                    
                    listbox.delete(index)
                    self.log_message(f"URL удален из списка")
            
            ttk.Button(list_window, text="Удалить выбранный", command=remove_selected).pack(pady=5)
            
        except:
            messagebox.showinfo("Информация", "Список автоустановки пуст")
    
    def start_auto_install(self):
        """Запуск автоматической установки"""
        if not self.auto_install_var.get():
            messagebox.showwarning("Внимание", "Включите автоматическую установку")
            return
        
        if not self.mods_path:
            messagebox.showerror("Ошибка", "Папка модов не найдена!")
            return
        
        threading.Thread(target=self._auto_install_thread, daemon=True).start()
    
    def _auto_install_thread(self):
        """Поток автоустановки"""
        try:
            with open("auto_install_urls.json", "r", encoding="utf-8") as f:
                urls = json.load(f)
            
            self.log_message(f"Начало автоустановки ({len(urls)} модов)")
            
            for i, url in enumerate(urls):
                try:
                    self.status_var.set(f"Установка мода {i+1}/{len(urls)}")
                    self.log_message(f"Обработка URL {i+1}: {url}")
                    
                    # Скачивание и установка
                    self._download_and_install_thread(url)
                    
                    # Небольшая задержка между модами
                    time.sleep(2)
                    
                except Exception as e:
                    self.log_message(f"Ошибка при установке мода {i+1}: {str(e)}")
                    continue
            
            self.log_message("Автоустановка завершена")
            self.status_var.set("Автоустановка завершена")
            
        except Exception as e:
            self.log_message(f"Ошибка автоустановки: {str(e)}")
            self.status_var.set(f"Ошибка: {str(e)}")
    
    def save_settings(self):
        """Сохранение настроек"""
        settings = {
            "sims4_path": self.sims4_path,
            "mods_path": self.mods_path,
            "auto_install": self.auto_install_var.get(),
            "download_timeout": getattr(self, 'download_timeout', 30),
            "max_retries": getattr(self, 'max_retries', 3),
            "auto_cleanup_downloads": getattr(self, 'auto_cleanup_downloads', False),
            "confirm_delete": getattr(self, 'confirm_delete', True)
        }
        
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def load_settings(self):
        """Загрузка настроек"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.sims4_path = settings.get("sims4_path", "")
                    self.mods_path = settings.get("mods_path", "")
                    self.download_timeout = settings.get("download_timeout", 30)
                    self.max_retries = settings.get("max_retries", 3)
                    self.auto_cleanup_downloads = settings.get("auto_cleanup_downloads", False)
                    self.confirm_delete = settings.get("confirm_delete", True)
                    # auto_install будет установлен позже при создании GUI
        except:
            pass
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    app = Sims4ModInstaller()
    app.run()
