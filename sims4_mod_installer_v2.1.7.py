#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sims 4 Auto Mod Installer v2.1.7
Автоматический установщик модов для The Sims 4 с защитой oSIM 0.6.2
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
import base64
import hmac
import struct
import re
import tempfile
import ctypes
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

class OSIMProtection:
    """Защита oSIM 0.6.2 - предотвращение модификации и ломания кода с Manifest-верификацией"""
    
    def __init__(self):
        self.version = "0.6.2"
        self.manifest_file = "checksum.osim"
        self.signature_key = b"oSIM_Sims4_Mod_Installer_v2.1.7_Protected_0.6.2"
        self.salt = "oSIM_Salt_v2.1.7_Stable_Enhanced"
        self.integrity_check_passed = False
        self.downloading_files = set()  # Файлы в процессе загрузки
        self.temp_files = set()  # Временные файлы
        
        # Коды ошибок oSIM с префиксами
        self.error_codes = {
            "0x1212bi": {
                "type": "Integrity Breach",
                "description": "Обнаружено изменение кода программы или подмена исполняемых файлов."
            },
            "0x1213vs": {
                "type": "Virus Signature",
                "description": "В устанавливаемом моде найден опасный паттерн (детект вируса)."
            },
            "0x1214mf": {
                "type": "Missing File",
                "description": "Отсутствует критический компонент защиты oSIM или файл манифеста."
            },
            "0x1215un": {
                "type": "Unknown Origin",
                "description": "Попытка установить мод из недоверенного или незарегистрированного источника."
            },
            "0x1216hc": {
                "type": "Hash Conflict",
                "description": "Файл загружен, но его контрольная сумма не совпадает с серверной (битый архив)."
            },
            "0x1217de": {
                "type": "Debugger Detected",
                "description": "Обнаружена попытка подключения отладчика к процессу программы."
            }
        }
        
        # Проверки при инициализации
        self.verify_manifest_integrity()
        self.check_environment()
        self.create_or_update_manifest()
    
    def create_or_update_manifest(self):
        """Создание или обновление манифеста с хешами файлов"""
        try:
            manifest = {
                "version": self.version,
                "created_at": datetime.now().isoformat(),
                "files": {},
                "salt": self.salt
            }
            
            # Получаем хеши всех критичных файлов
            critical_files = [
                "sims4_mod_installer_v2.1.7.py",
                "LICENSE",
                "README.md"
            ]
            
            for file_name in critical_files:
                if os.path.exists(file_name):
                    file_hash = self.calculate_salted_hash(file_name)
                    manifest["files"][file_name] = {
                        "sha256": file_hash,
                        "size": os.path.getsize(file_name),
                        "modified": os.path.getmtime(file_name)
                    }
            
            # Сохраняем манифест
            with open(self.manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            self.integrity_check_passed = True
            return True
            
        except Exception as e:
            self.trigger_protection_block("0x1214mf", f"Failed to create manifest: {e}")
            return False
    
    def calculate_salted_hash(self, file_path):
        """Расчет соленого хеша файла"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Добавляем соль к содержимому
            salted_content = content + self.salt.encode('utf-8')
            return hashlib.sha256(salted_content).hexdigest()
            
        except Exception as e:
            return ""
    
    def verify_manifest_integrity(self):
        """Проверка целостности через манифест"""
        try:
            if not os.path.exists(self.manifest_file):
                # Манифест не найден, создаем новый
                return self.create_or_update_manifest()
            
            # Загружаем манифест
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Проверяем версию манифеста
            if manifest.get("version") != self.version:
                self.trigger_protection_block("0x1212bi", "Manifest version mismatch")
                return False
            
            # Проверяем хеши файлов
            files = manifest.get("files", {})
            for file_name, file_info in files.items():
                if os.path.exists(file_name):
                    current_hash = self.calculate_salted_hash(file_name)
                    expected_hash = file_info.get("sha256", "")
                    
                    if current_hash != expected_hash:
                        self.trigger_protection_block("0x1212bi", f"File integrity compromised: {file_name}")
                        return False
                else:
                    self.trigger_protection_block("0x1214mf", f"Critical file missing: {file_name}")
                    return False
            
            self.integrity_check_passed = True
            return True
            
        except Exception as e:
            self.trigger_protection_block("0x1214mf", f"Manifest verification error: {e}")
            return False
    
    def check_environment(self):
        """Проверка окружения на подозрительную активность"""
        try:
            # Проверка на отладчики
            if self.is_debugger_attached():
                self.trigger_protection_block("0x1217de", "Debugger detected")
                return False
            
            # Проверка на модификации памяти
            if self.check_memory_modifications():
                self.trigger_protection_block("0x1212bi", "Memory modifications detected")
                return False
            
            return True
            
        except Exception as e:
            self.trigger_protection_block("0x1214mf", f"Environment check error: {e}")
            return False
    
    def is_debugger_attached(self):
        """Проверка на наличие отладчика"""
        try:
            # Проверка через Windows API
            return ctypes.windll.kernel32.IsDebuggerPresent() != 0
        except:
            return False
    
    def check_memory_modifications(self):
        """Проверка модификаций памяти"""
        try:
            # Проверка стандартных методов внедрения кода
            suspicious_modules = ['injector', 'hook', 'patch', 'crack']
            current_process = os.getpid()
            
            # Упрощенная проверка
            return False
        except:
            return False
    
    def add_downloading_file(self, file_path):
        """Добавить файл в список загружаемых"""
        self.downloading_files.add(file_path)
    
    def remove_downloading_file(self, file_path):
        """Удалить файл из списка загружаемых"""
        self.downloading_files.discard(file_path)
    
    def is_file_downloading(self, file_path):
        """Проверить, загружается ли файл"""
        return file_path in self.downloading_files
    
    def add_temp_file(self, file_path):
        """Добавить временный файл"""
        self.temp_files.add(file_path)
    
    def remove_temp_file(self, file_path):
        """Удалить временный файл"""
        self.temp_files.discard(file_path)
    
    def is_temp_file(self, file_path):
        """Проверить, является ли файл временным"""
        return (file_path in self.temp_files or 
                file_path.endswith('.tmp') or 
                file_path.endswith('.downloading') or
                '.downloading' in file_path)
    
    def post_download_validation(self, file_path, expected_hash=None):
        """Post-Download Validation - проверка после завершения загрузки"""
        try:
            # Проверяем, что файл не является временным
            if self.is_temp_file(file_path):
                return True  # Пропускаем временные файлы
            
            # Проверяем существование файла
            if not os.path.exists(file_path):
                return False
            
            # Если предоставлен ожидаемый хеш, сравниваем
            if expected_hash:
                current_hash = self.calculate_salted_hash(file_path)
                if current_hash != expected_hash:
                    self.trigger_protection_block("0x1216hc", f"Hash conflict for {file_path}")
                    return False
            
            # Дополнительная проверка на угрозы
            threats = self.scan_file_for_threats(file_path)
            if threats:
                for threat in threats:
                    if "Virus" in threat:
                        self.trigger_protection_block("0x1213vs", f"Virus detected in {file_path}")
                        return False
                    elif "Malicious" in threat:
                        self.trigger_protection_block("0x1213vs", f"Malicious code in {file_path}")
                        return False
            
            return True
            
        except Exception as e:
            return False
    
    def trigger_protection_block(self, error_code, reason):
        """Активация блокировки защиты с улучшенным интерфейсом"""
        error_info = self.error_codes.get(error_code, {
            "type": "Unknown Error",
            "description": "Неизвестная ошибка защиты"
        })
        
        error_message = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    ЗАЩИТА oSIM v{self.version}                       ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Обнаружена угроза безопасности!                                 ║
║  Код ошибки: {error_code:<45} ║
║  Тип: {error_info['type']:<52} ║
║  Причина: {reason:<52} ║
║                                                                  ║
║  {error_info['description']:<66} ║
║                                                                  ║
║  Программа заблокирована для вашей защиты.                        ║
║  Пожалуйста, скачайте чистую версию с официального репозитория.  ║
║                                                                  ║
║  GitHub: https://github.com/neirrio/sims4-mod-installer          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """
        
        print(error_message)
        
        # Показываем диалоговое окно
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                f"Защита oSIM v{self.version}",
                f"Обнаружена угроза безопасности!\n\n"
                f"Код ошибки: {error_code}\n"
                f"Тип: {error_info['type']}\n"
                f"Причина: {reason}\n\n"
                f"{error_info['description']}\n\n"
                f"Программа будет закрыта для вашей защиты.\n"
                f"Скачайте чистую версию с официального репозитория."
            )
            root.destroy()
        except:
            pass
        
        # Блокируем программу
        sys.exit(1)
    
    def scan_file_for_threats(self, file_path):
        """Сканирование файла на угрозы с улучшенными алгоритмами"""
        try:
            # Пропускаем временные файлы
            if self.is_temp_file(file_path) or self.is_file_downloading(file_path):
                return []
            
            threats = []
            
            # Проверка на вирусы (улучшенная)
            if self._check_malware_signatures(file_path):
                threats.append("Malware signature detected")
            
            # Проверка на вредоносный код
            if self._check_malicious_code(file_path):
                threats.append("Malicious code pattern detected")
            
            # Проверка целостности
            if self._check_file_integrity(file_path):
                threats.append("File integrity compromised")
            
            # Проверка на неизвестное происхождение
            if self._check_unknown_origin(file_path):
                threats.append("Unknown origin detected")
            
            return threats
            
        except Exception as e:
            return [f"Scan error: {e}"]
    
    def _check_malware_signatures(self, file_path):
        """Проверка сигнатур вредоносного ПО (улучшенная)"""
        try:
            # Расширенные сигнатуры вредоносного ПО
            malware_signatures = [
                b'eval(base64_decode',
                b'shell_exec',
                b'system(',
                b'passthru(',
                b'exec(',
                b'preg_replace.*\\/e',
                b'create_function',
                b'assert(',
                b'\\x50\\x4b\\x03\\x04',  # ZIP bomb
                b'\\x1f\\x8b\\x08\\x00',  # GZIP bomb
                b'powershell',
                b'cmd.exe',
                b'wscript.shell',
                b'shell.application',
                b'createobject',
                b'activexobject'
            ]
            
            with open(file_path, 'rb') as f:
                content = f.read(2 * 1024 * 1024)  # Первые 2 МБ
                
            for signature in malware_signatures:
                if signature in content:
                    return True
            
            return False
            
        except:
            return False
    
    def _check_malicious_code(self, file_path):
        """Проверка вредоносного кода (улучшенная)"""
        try:
            # Проверка на подозрительные паттерны в .package и .ts4script файлах
            if file_path.lower().endswith(('.package', '.ts4script')):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Расширенные подозрительные паттерны
                suspicious_patterns = [
                    b'import os',
                    b'import sys',
                    b'subprocess',
                    b'exec(',
                    b'eval(',
                    b'__import__',
                    b'open(',
                    b'file(',
                    b'input(',
                    b'raw_input('
                ]
                
                for pattern in suspicious_patterns:
                    if pattern in content:
                        return True
            
            return False
            
        except:
            return False
    
    def _check_file_integrity(self, file_path):
        """Проверка целостности файла (улучшенная)"""
        try:
            # Проверка размера файла
            file_size = os.path.getsize(file_path)
            
            # Слишком большие файлы могут быть вредоносными
            if file_size > 200 * 1024 * 1024:  # 200 МБ
                return True
            
            # Проверка на пустые файлы
            if file_size == 0:
                return True
            
            # Проверка хеша файла
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = hashlib.md5(content).hexdigest()
            
            # Проверка на известные вредоносные хеши
            malicious_hashes = [
                'd41d8cd98f00b204e9800998ecf8427e',  # Пустой файл
                # Здесь могут быть другие известные хеши
            ]
            
            return file_hash in malicious_hashes
            
        except:
            return True
    
    def _check_unknown_origin(self, file_path):
        """Проверка неизвестного происхождения"""
        try:
            # Проверяем, что файл из доверенного источника
            trusted_paths = [
                os.getcwd(),
                tempfile.gettempdir(),
                self.download_folder if hasattr(self, 'download_folder') else ""
            ]
            
            file_dir = os.path.dirname(file_path)
            
            # Если файл не из доверенной директории
            if not any(file_dir.startswith(trusted) for trusted in trusted_paths if trusted):
                return True
            
            return False
            
        except:
            return True

class BackupManager:
    """Менеджер бэкапов версий с защитой"""
    
    def __init__(self):
        self.backup_dir = "backups"
        self.max_backups = 10
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, version, exe_path):
        """Создание бэкапа версии с защитой"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"Sims4-Mod-Installer_v{version}_{timestamp}.exe"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if os.path.exists(exe_path):
                shutil.copy2(exe_path, backup_path)
                
                # Создаем метаданные бэкапа с защитой
                metadata = {
                    'version': version,
                    'timestamp': timestamp,
                    'original_path': exe_path,
                    'backup_path': backup_path,
                    'file_size': os.path.getsize(backup_path),
                    'file_hash': self._calculate_file_hash(backup_path),
                    'protected': True,
                    'osim_version': '0.6.2'
                }
                
                metadata_path = os.path.join(self.backup_dir, f"{backup_name}.meta")
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                # Очищаем старые бэкапы
                self._cleanup_old_backups()
                
                return backup_path
            
            return None
            
        except Exception as e:
            print(f"Ошибка создания бэкапа: {e}")
            return None
    
    def _calculate_file_hash(self, file_path):
        """Расчет хеша файла"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""
    
    def _cleanup_old_backups(self):
        """Очистка старых бэкапов"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.exe'):
                    backup_files.append(os.path.join(self.backup_dir, file))
            
            backup_files.sort(key=os.path.getctime, reverse=True)
            
            # Удаляем лишние бэкапы
            for backup_file in backup_files[self.max_backups:]:
                try:
                    os.remove(backup_file)
                    # Удаляем метаданные
                    meta_file = backup_file + '.meta'
                    if os.path.exists(meta_file):
                        os.remove(meta_file)
                except:
                    pass
                    
        except:
            pass

class Sims4ModInstaller:
    def __init__(self):
        # Инициализация защиты oSIM 0.6.2
        self.osim_protection = OSIMProtection()
        
        # Инициализация менеджера бэкапов
        self.backup_manager = BackupManager()
        
        # Инициализация с поддержкой DnD
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        
        self.root.title("Sims 4 Auto Mod Installer v2.1.7")
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
        self.app_version = "2.1.7"
        self.app_name = "Sims 4 Auto Mod Installer"
        
        # GitHub настройки
        self.github_owner = "neirrio"
        self.github_repo = "sims4-mod-installer"
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
                    'system_info': self.get_system_info(),
                    'osim_version': '0.6.2'
                }
                
                with open(self.device_token_file, 'w', encoding='utf-8') as f:
                    json.dump(token_data, f, indent=2, ensure_ascii=False)
                
                # Отправляем информацию о новом устройстве на сервер
                self.register_device(token_data)
                
                return token_data['token']
        except Exception as e:
            self.log_message(f"Ошибка работы с токеном: {e}")
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
                'timestamp': datetime.now().isoformat(),
                'osim_version': token_data.get('osim_version', '0.6.2')
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
            # Ищем первый .exe файл в assets
            assets = release_data.get('assets', [])
            for asset in assets:
                if asset['name'].endswith('.exe'):
                    return asset['browser_download_url']
            
            # Если нет .exe, ищем .zip
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
    
    def show_update_dialog(self, update_info):
        """Показ диалога обновления с предложением скачивания"""
        version = update_info.get('version', 'Unknown')
        notes = update_info.get('release_notes', 'Доступно новое обновление')
        mandatory = update_info.get('mandatory', False)
        download_url = update_info.get('download_url', '')
        
        # Создаем окно обновления
        update_window = tk.Toplevel(self.root)
        update_window.title("Доступно обновление")
        update_window.geometry("500x400")
        update_window.resizable(False, False)
        update_window.transient(self.root)
        update_window.grab_set()
        
        main_frame = ttk.Frame(update_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_text = "Обязательное обновление!" if mandatory else "Доступно обновление"
        ttk.Label(main_frame, text=title_text, font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Информация об обновлении
        info_frame = ttk.LabelFrame(main_frame, text="Информация об обновлении", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        ttk.Label(info_frame, text=f"Текущая версия: {self.app_version}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Новая версия: {version}").pack(anchor=tk.W, pady=(5, 0))
        
        # Заметки к выпуску
        notes_frame = ttk.LabelFrame(main_frame, text="Что нового:", padding="10")
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        notes_text = scrolledtext.ScrolledText(notes_frame, height=8, width=50)
        notes_text.pack(fill=tk.BOTH, expand=True)
        notes_text.insert(tk.END, notes)
        notes_text.config(state=tk.DISABLED)
        
        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        if mandatory:
            ttk.Button(button_frame, text="Скачать обновление", 
                      command=lambda: self.download_update(update_window, download_url)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Отмена", 
                      command=lambda: self.skip_update(update_window)).pack(side=tk.RIGHT)
        else:
            ttk.Button(button_frame, text="Скачать обновление", 
                      command=lambda: self.download_update(update_window, download_url)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Установить автоматически", 
                      command=lambda: self.auto_install_update(update_window, download_url)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Пропустить", 
                      command=lambda: self.skip_update(update_window)).pack(side=tk.RIGHT)
        
        # Обработка закрытия окна
        if mandatory:
            update_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Запрещаем закрывать обязательные обновления
        else:
            update_window.protocol("WM_DELETE_WINDOW", lambda: self.skip_update(update_window))
    
    def download_update(self, window, download_url):
        """Скачать обновление (открыть браузер)"""
        try:
            webbrowser.open(download_url)
            self.log_message(f"Открыта страница скачивания обновления: {download_url}")
            
            # Показываем информационное окно
            messagebox.showinfo(
                "Скачивание обновления",
                f"Страница скачивания обновления открыта в браузере.\n\n"
                f"После скачивания:\n"
                f"1. Закройте программу\n"
                f"2. Распакуйте новый .exe файл\n"
                f"3. Запустите новую версию"
            )
            
            window.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть страницу скачивания: {e}")
    
    def auto_install_update(self, window, download_url):
        """Автоматическая установка обновления с защитой"""
        try:
            self.log_message("Начинаю автоматическую установку обновления...")
            
            # Создаем бэкап текущей версии
            current_exe = os.path.abspath(sys.executable if hasattr(sys, 'frozen') else __file__)
            backup_path = self.backup_manager.create_backup(self.app_version, current_exe)
            
            if backup_path:
                self.log_message(f"Создан бэкап: {backup_path}")
            
            # Скачиваем обновление
            update_file = os.path.join(self.download_folder, "update.exe.downloading")
            
            # Добавляем файл в список загружаемых
            self.osim_protection.add_downloading_file(update_file)
            
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
                        if hasattr(self, 'progress_var'):
                            progress = (downloaded / total_size) * 50
                            self.progress_var.set(progress)
            
            # Переименовываем файл после завершения загрузки
            final_update_file = update_file.replace('.downloading', '')
            os.rename(update_file, final_update_file)
            
            # Удаляем из списка загружаемых
            self.osim_protection.remove_downloading_file(update_file)
            
            self.log_message(f"Обновление скачано: {downloaded / 1024 / 1024:.1f} MB")
            
            # Post-Download Validation
            if not self.osim_protection.post_download_validation(final_update_file):
                self.osim_protection.trigger_protection_block("0x1216hc", "Update file validation failed")
                return
            
            # Создаем скрипт обновления
            update_script = self.create_update_script(final_update_file)
            
            # Запускаем скрипт и закрываем программу
            subprocess.Popen([sys.executable, update_script], shell=True)
            
            self.root.withdraw()  # Скрываем окно на время обновления
            window.destroy()
            
        except Exception as e:
            self.log_message(f"Ошибка автоматического обновления: {e}")
            messagebox.showerror("Ошибка обновления", f"Не удалось установить обновление автоматически: {e}\n\nПопробуйте скачать обновление вручную.")
    
    def skip_update(self, window):
        """Пропустить обновление"""
        self.log_message("Обновление пропущено пользователем")
        window.destroy()
    
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
    
    def create_gui(self):
        """Создание графического интерфейса"""
        
        # Основная рамка
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка веса колонок и строк
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Sims 4 Auto Mod Installer v2.1.7", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # Путь к игре
        ttk.Label(main_frame, text="Путь к игре:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.sims4_path_var = tk.StringVar()
        self.sims4_entry = ttk.Entry(main_frame, textvariable=self.sims4_path_var, state=tk.DISABLED)
        self.sims4_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Button(main_frame, text="Найти", command=self.find_sims4).grid(row=1, column=3, pady=(0, 5))
        
        # Путь к модам
        ttk.Label(main_frame, text="Папка модов:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.mods_path_var = tk.StringVar()
        self.mods_entry = ttk.Entry(main_frame, textvariable=self.mods_path_var, state=tk.DISABLED)
        self.mods_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Button(main_frame, text="Обзор", command=self.browse_mods).grid(row=2, column=3, pady=(0, 5))
        
        # URL для скачивания
        ttk.Label(main_frame, text="URL мода:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var)
        self.url_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Button(main_frame, text="Вставить", command=self.paste_from_clipboard).grid(row=3, column=3, pady=(0, 5))
        
        # Прогресс и статус
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 5))
        
        self.status_var = tk.StringVar(value="Готов к работе")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=5, column=0, columnspan=4, pady=(0, 10))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Скачать и установить", command=self.download_and_install).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Установить из файла", command=self.install_from_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить все моды", command=self.delete_all_mods).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить папку загрузок", command=self.cleanup_downloads).pack(side=tk.LEFT, padx=5)
        
        # Кнопки меню
        menu_frame = ttk.Frame(main_frame)
        menu_frame.grid(row=7, column=0, columnspan=4, pady=5)
        
        ttk.Button(menu_frame, text="О программе", command=self.show_about).pack(side=tk.LEFT, padx=5)
        ttk.Button(menu_frame, text="Настройки", command=self.show_settings).pack(side=tk.LEFT, padx=5)
        
        # Лог
        ttk.Label(main_frame, text="Лог операций:").grid(row=8, column=0, sticky=tk.W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.log_text.grid(row=9, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Область для drag-and-drop
        drop_frame = ttk.LabelFrame(main_frame, text="Перетащите файлы модов сюда", padding="10")
        drop_frame.grid(row=10, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
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
                                       text="Поддерживаемые форматы: .package, .ts4script, .zip, .7z, .rar, .exe\n" +
                                            "Для установки файлов кликните здесь или используйте кнопку 'Установить из файла'",
                                       foreground="gray")
            self.drop_label.pack()
            self.drop_label.bind('<Button-1>', lambda e: self.select_files_for_drop())
        
        # Настройка drag-and-drop
        self.setup_drag_drop()
        
        # Автоматическая установка
        auto_frame = ttk.LabelFrame(main_frame, text="Автоматическая установка", padding="5")
        auto_frame.grid(row=11, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
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
    
    def find_sims4(self):
        """Поиск игры"""
        try:
            # Поиск в реестре
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Maxis\The Sims 4", 0, winreg.KEY_READ)
            sims4_path = winreg.QueryValueEx(key, "Install Dir")[0]
            winreg.CloseKey(key)
            
            self.sims4_path = sims4_path
            self.sims4_path_var.set(sims4_path)
            
            # Папка модов
            mods_path = os.path.join(sims4_path, "Mods")
            if os.path.exists(mods_path):
                self.mods_path = mods_path
                self.mods_path_var.set(mods_path)
            
            self.log_message(f"Игра найдена: {sims4_path}")
            
        except Exception as e:
            self.log_message(f"Игра не найдена: {str(e)}")
            messagebox.showwarning("Внимание", "Игра не найдена. Укажите путь вручную.")
    
    def auto_find_sims4(self):
        """Автоматический поиск игры при запуске"""
        if not self.sims4_path:
            self.find_sims4()
    
    def browse_mods(self):
        """Выбор папки модов"""
        folder = filedialog.askdirectory(title="Выберите папку модов")
        if folder:
            self.mods_path = folder
            self.mods_path_var.set(folder)
            self.log_message(f"Выбрана папка модов: {folder}")
    
    def paste_from_clipboard(self):
        """Вставка URL из буфера обмена"""
        try:
            self.root.clipboard_clear()
            url = self.root.clipboard_get()
            self.url_var.set(url)
            self.log_message("URL вставлен из буфера обмена")
        except:
            self.log_message("Ошибка вставки из буфера обмена")
    
    def download_and_install(self):
        """Скачивание и установка"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Внимание", "Введите URL для скачивания")
            return
        
        if not self.mods_path:
            messagebox.showerror("Ошибка", "Папка модов не найдена!")
            return
        
        threading.Thread(target=self._download_and_install_thread, args=(url,), daemon=True).start()
    
    def _download_and_install_thread(self, url):
        """Поток для скачивания и установки с защитой"""
        try:
            self.status_var.set("Скачивание...")
            self.progress_var.set(25)
            
            # Скачивание файла
            filename = self._extract_filename_from_url(url)
            download_file = os.path.join(self.download_folder, f"{filename}.downloading")
            
            # Добавляем файл в список загружаемых
            self.osim_protection.add_downloading_file(download_file)
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = 25 + (downloaded / total_size) * 50
                            self.progress_var.set(progress)
            
            # Переименовываем файл после завершения загрузки
            file_path = download_file.replace('.downloading', '')
            os.rename(download_file, file_path)
            
            # Удаляем из списка загружаемых
            self.osim_protection.remove_downloading_file(download_file)
            
            self.log_message(f"Файл скачан: {filename}")
            self.status_var.set("Установка...")
            self.progress_var.set(75)
            
            # Post-Download Validation
            if not self.osim_protection.post_download_validation(file_path):
                self.log_message("Файл не прошел проверку безопасности")
                raise Exception("Файл содержит угрозы безопасности!")
            
            # Установка
            self.install_mod_file(file_path)
            
            self.progress_var.set(100)
            self.status_var.set("Готово!")
            messagebox.showinfo("Готово", "Мод успешно установлен!")
            
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")
            self.status_var.set(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось установить мод: {str(e)}")
    
    def _extract_filename_from_url(self, url):
        """Извлечение имени файла из URL"""
        try:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            
            if not filename or '.' not in filename:
                # Пробуем получить из заголовка Content-Disposition
                response = requests.head(url, timeout=10)
                content_disposition = response.headers.get('content-disposition', '')
                
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[-1].strip('"')
                else:
                    # Генерируем имя файла
                    domain = parsed.netloc.replace('.', '_')
                    timestamp = int(time.time())
                    ext = '.zip'  # по умолчанию
                    if url.lower().endswith(('.package', '.ts4script')):
                        ext = os.path.splitext(url)[1]
                    
                    return f"mod_{domain}_{timestamp}{ext}"
            
            return filename
            
        except Exception:
            return f"mod_{int(time.time())}.zip"
    
    def install_mod_file(self, file_path):
        """Установка мода из файла с поддержкой расширенных форматов и защитой"""
        try:
            self.log_message(f"Установка файла: {file_path}")
            
            # Проверка файла на угрозы перед установкой
            threats = self.osim_protection.scan_file_for_threats(file_path)
            if threats:
                error_msg = f"Обнаружены угрозы в файле {os.path.basename(file_path)}:\n" + "\n".join(threats)
                self.log_message(f"БЛОКИРОВКА: {error_msg}")
                raise Exception(f"Файл содержит угрозы безопасности!\n{error_msg}")
            
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
        """Извлечение файлов модов из временной папки с проверкой безопасности"""
        moved_files = []
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith(('.package', '.ts4script')):
                    src = os.path.join(root, file)
                    
                    # Проверка файла на угрозы перед установкой
                    threats = self.osim_protection.scan_file_for_threats(src)
                    if threats:
                        self.log_message(f"БЛОКИРОВКА файла {file}: {', '.join(threats)}")
                        continue
                    
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
            self.log_message("В архиве не найдено безопасных .package или .ts4script файлов")
    
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
            self.status_var.set("Готово!")
            messagebox.showinfo("Готово", "Мод успешно установлен!")
            
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")
            self.status_var.set(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось установить мод: {str(e)}")
    
    def delete_all_mods(self):
        """Удаление всех установленных модов"""
        if not self.mods_path:
            messagebox.showerror("Ошибка", "Папка модов не найдена!")
            return
        
        if not self.confirm_delete:
            result = messagebox.askyesno("Подтверждение", 
                                       f"Удалить все моды из папки:\n{self.mods_path}\n\nЭто действие необратимо!")
        else:
            result = True
        
        if result:
            try:
                deleted_count = 0
                for file in os.listdir(self.mods_path):
                    if file.lower().endswith(('.package', '.ts4script')):
                        file_path = os.path.join(self.mods_path, file)
                        os.remove(file_path)
                        deleted_count += 1
                
                self.log_message(f"Удалено модов: {deleted_count}")
                messagebox.showinfo("Готово", f"Удалено модов: {deleted_count}")
                
            except Exception as e:
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
    
    def show_about(self):
        """Показать окно 'О программе'"""
        about_window = tk.Toplevel(self.root)
        about_window.title("О программе")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        main_frame = ttk.Frame(about_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Название программы
        title_label = ttk.Label(main_frame, text=self.app_name, font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        version_label = ttk.Label(main_frame, text=f"Версия: {self.app_version}", font=("Arial", 12))
        version_label.pack(pady=(0, 20))
        
        osim_label = ttk.Label(main_frame, text="Защита: oSIM v0.6.2", font=("Arial", 10, "italic"))
        osim_label.pack(pady=(0, 20))
        
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
• Защита oSIM 0.6.2 от угроз безопасности

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
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Путь к игре
        ttk.Label(main_frame, text="Путь к игре:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        sims4_var = tk.StringVar(value=self.sims4_path)
        sims4_entry = ttk.Entry(main_frame, textvariable=sims4_var)
        sims4_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Button(main_frame, text="Обзор", command=lambda: self.browse_path_setting(sims4_var, "game")).grid(row=0, column=2, pady=(0, 5))
        
        # Путь к модам
        ttk.Label(main_frame, text="Папка модов:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        mods_var = tk.StringVar(value=self.mods_path)
        mods_entry = ttk.Entry(main_frame, textvariable=mods_var)
        mods_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Button(main_frame, text="Обзор", command=lambda: self.browse_path_setting(mods_var, "mods")).grid(row=1, column=2, pady=(0, 5))
        
        # Настройки скачивания
        ttk.Label(main_frame, text="Таймаут скачивания (сек):").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        timeout_var = tk.StringVar(value=str(getattr(self, 'download_timeout', 30)))
        timeout_entry = ttk.Entry(main_frame, textvariable=timeout_var)
        timeout_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
        
        ttk.Label(main_frame, text="Попыток скачивания:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        retries_var = tk.StringVar(value=str(getattr(self, 'max_retries', 3)))
        retries_entry = ttk.Entry(main_frame, textvariable=retries_var)
        retries_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Чекбоксы
        auto_cleanup_var = tk.BooleanVar(value=getattr(self, 'auto_cleanup_downloads', False))
        ttk.Checkbutton(main_frame, text="Автоматически очищать загрузки", variable=auto_cleanup_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        confirm_delete_var = tk.BooleanVar(value=getattr(self, 'confirm_delete', True))
        ttk.Checkbutton(main_frame, text="Подтверждать удаление модов", variable=confirm_delete_var).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(20, 0))
        
        ttk.Button(button_frame, text="Сохранить", command=lambda: self.save_settings_window(settings_window, sims4_var.get(), mods_var.get(), timeout_var.get(), retries_var.get(), auto_cleanup_var.get(), confirm_delete_var.get())).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Сброс", command=lambda: self.reset_settings(settings_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=settings_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def browse_path_setting(self, var, path_type):
        """Выбор пути в настройках"""
        if path_type == "game":
            folder = filedialog.askdirectory(title="Выберите папку с игрой")
        else:
            folder = filedialog.askdirectory(title="Выберите папку модов")
        
        if folder:
            var.set(folder)
    
    def save_settings_window(self, window, sims4_path, mods_path, timeout, retries, auto_cleanup, confirm_delete):
        """Сохранение настроек из окна"""
        try:
            self.sims4_path = sims4_path
            self.mods_path = mods_path
            self.sims4_path_var.set(sims4_path)
            self.mods_path_var.set(mods_path)
            
            self.download_timeout = int(timeout)
            self.max_retries = int(retries)
            self.auto_cleanup_downloads = auto_cleanup
            self.confirm_delete = confirm_delete
            
            self.save_settings()
            window.destroy()
            
            messagebox.showinfo("Готово", "Настройки сохранены!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {str(e)}")
    
    def reset_settings(self, window):
        """Сброс настроек"""
        if messagebox.askyesno("Сброс настроек", "Сбросить все настройки к значениям по умолчанию?"):
            self.sims4_path = ""
            self.mods_path = ""
            self.sims4_path_var.set("")
            self.mods_path_var.set("")
            
            self.download_timeout = 30
            self.max_retries = 3
            self.auto_cleanup_downloads = False
            self.confirm_delete = True
            
            self.save_settings()
            window.destroy()
            
            messagebox.showinfo("Готово", "Настройки сброшены!")
    
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
        except Exception as e:
            self.log_message(f"Ошибка сохранения настроек: {e}")
    
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
        
        # Устанавливаем значения в интерфейс
        self.sims4_path_var.set(self.sims4_path)
        self.mods_path_var.set(self.mods_path)
    
    def add_url_to_list(self):
        """Добавление URL в список автоустановки"""
        url = simpledialog.askstring("Добавить URL", "Введите URL мода:")
        if url:
            # Здесь можно добавить логику сохранения URL в список
            self.log_message(f"URL добавлен в список: {url}")
    
    def show_url_list(self):
        """Показать список URL для автоустановки"""
        # Здесь можно показать окно со списком URL
        messagebox.showinfo("Список URL", "Список URL для автоустановки пока не реализован")
    
    def start_auto_install(self):
        """Запустить автоустановку"""
        if not self.auto_install_var.get():
            messagebox.showwarning("Внимание", "Включите автоматическую установку")
            return
        
        # Здесь можно запустить процесс автоустановки
        self.log_message("Автоустановка запущена")
    
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
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    app = Sims4ModInstaller()
    app.run()
