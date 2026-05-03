#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый сервер для демонстрации мега-обновления
"""

import json
import time
from datetime import datetime
import threading
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

class UpdateServerHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/api/maintenance':
            self.handle_maintenance_get()
        elif self.path.startswith('/api/check-update'):
            self.handle_check_update()
        elif self.path == '/api/devices':
            self.handle_devices()
        elif self.path == '/api/stats':
            self.handle_stats()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Обработка POST запросов"""
        if self.path == '/api/register':
            self.handle_register()
        elif self.path == '/api/maintenance':
            self.handle_maintenance_post()
        elif self.path == '/api/updates':
            self.handle_updates()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Обработка CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def handle_register(self):
        """Регистрация устройства"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            print(f"📱 Новое устройство зарегистрировано:")
            print(f"   Token: {data['token'][:8]}...")
            print(f"   Device ID: {data['device_id']}")
            print(f"   Version: {data['version']}")
            
            response = {'status': 'success', 'message': 'Device registered'}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_maintenance_get(self):
        """Получение режима обслуживания"""
        # Демонстрационный режим - выключен
        response = {
            'enabled': False,
            'message': 'Технические работы завершены',
            'updated_at': datetime.now().isoformat()
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_maintenance_post(self):
        """Установка режима обслуживания"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            enabled = data.get('enabled', False)
            message = data.get('message', 'Технические работы')
            
            print(f"🔧 Режим обслуживания: {'ВКЛЮЧЕН' if enabled else 'ВЫКЛЮЧЕН'}")
            if enabled:
                print(f"   Сообщение: {message}")
            
            response = {'status': 'success'}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_check_update(self):
        """Проверка обновлений"""
        try:
            # Демонстрационное обновление
            response = {
                'update_available': True,
                'version': '2.2.0',
                'download_url': 'http://localhost:8000/demo_update.zip',
                'release_notes': 'Демонстрационное обновление:\\n- Новые функции\\n- Исправления ошибок\\n- Улучшения производительности',
                'mandatory': False
            }
            
            print(f"📦 Запрос обновления: отправлена версия 2.2.0")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_devices(self):
        """Список устройств"""
        response = []
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_stats(self):
        """Статистика"""
        response = {
            'total_devices': 1,
            'online_devices': 1,
            'active_updates': 1
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_updates(self):
        """Управление обновлениями"""
        response = []
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Кастомное логирование"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def create_demo_update():
    """Создание демонстрационного файла обновления"""
    import zipfile
    import os
    
    # Создаем простое обновление
    with zipfile.ZipFile('demo_update.zip', 'w') as zf:
        zf.writestr('version.txt', '2.2.0')
        zf.writestr('update_info.txt', 'Демонстрационное обновление')
    
    print("📦 Создан демонстрационный файл обновления: demo_update.zip")

def start_file_server():
    """Запуск файлового сервера для обновлений"""
    import http.server
    
    class FileHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Отключаем логи файлового сервера
    
    try:
        with socketserver.TCPServer(("", 8000), FileHandler) as httpd:
            print("📁 Файловый сервер запущен на http://localhost:8000")
            httpd.serve_forever()
    except OSError as e:
        print(f"Файловый сервер уже запущен: {e}")

def main():
    """Основная функция"""
    print("🚀 Запуск тестового сервера для мега-обновления")
    print("=" * 50)
    
    # Создаем демонстрационное обновление
    create_demo_update()
    
    # Запускаем файловый сервер в отдельном потоке
    file_server_thread = threading.Thread(target=start_file_server, daemon=True)
    file_server_thread.start()
    
    # Небольшая задержка для запуска файлового сервера
    time.sleep(1)
    
    # Запускаем основной API сервер
    try:
        with socketserver.TCPServer(("", 5000), UpdateServerHandler) as httpd:
            print("🌐 API сервер запущен на http://localhost:5000")
            print("📊 Админ-панель: http://localhost:5000")
            print("=" * 50)
            print("📝 Для тестирования:")
            print("   1. Измените URL в sims4_mod_installer.py на http://localhost:5000/api")
            print("   2. Запустите sims4_mod_installer.py")
            print("   3. Программа автоматически проверит обновления")
            print("=" * 50)
            httpd.serve_forever()
    except OSError as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        print("Сервер уже запущен на порту 5000")

if __name__ == "__main__":
    main()
