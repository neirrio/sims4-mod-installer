#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервер для управления обновлениями Sims 4 Mod Installer
"""

from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime
import sqlite3
import hashlib

app = Flask(__name__)

# База данных для устройств и обновлений
DB_FILE = "devices.db"

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Таблица устройств
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            device_id TEXT NOT NULL,
            version TEXT NOT NULL,
            system_info TEXT,
            created_at TEXT NOT NULL,
            last_seen TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Таблица обновлений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            download_url TEXT NOT NULL,
            release_notes TEXT,
            mandatory BOOLEAN DEFAULT FALSE,
            created_at TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Таблица режима обслуживания
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            enabled BOOLEAN DEFAULT FALSE,
            message TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (id) REFERENCES maintenance (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def admin_panel():
    """Админ-панель"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Панель управления - Sims 4 Mod Installer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2 { color: #333; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; }
        .status-online { color: #28a745; }
        .status-offline { color: #dc3545; }
        .form-group { margin: 10px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        textarea { height: 100px; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { flex: 1; background: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 Панель управления Sims 4 Mod Installer</h1>
        
        <!-- Статистика -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalDevices">-</div>
                <div>Всего устройств</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="onlineDevices">-</div>
                <div>Онлайн</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="activeUpdates">-</div>
                <div>Активных обновлений</div>
            </div>
        </div>
        
        <!-- Режим обслуживания -->
        <div class="card">
            <h2>🔧 Режим обслуживания</h2>
            <div id="maintenanceStatus">
                <p>Загрузка...</p>
            </div>
            <div class="form-group">
                <label>Сообщение для пользователей:</label>
                <textarea id="maintenanceMessage" placeholder="В настоящее время проводятся технические работы..."></textarea>
            </div>
            <button class="btn btn-warning" onclick="toggleMaintenance()">Включить режим обслуживания</button>
            <button class="btn btn-success" onclick="disableMaintenance()">Отключить режим обслуживания</button>
        </div>
        
        <!-- Управление обновлениями -->
        <div class="card">
            <h2>📦 Управление обновлениями</h2>
            <div class="form-group">
                <label>Версия:</label>
                <input type="text" id="updateVersion" placeholder="2.2.0">
            </div>
            <div class="form-group">
                <label>URL для скачивания:</label>
                <input type="url" id="updateUrl" placeholder="https://example.com/update.zip">
            </div>
            <div class="form-group">
                <label>Заметки к выпуску:</label>
                <textarea id="updateNotes" placeholder="Исправлены ошибки, добавлены новые функции..."></textarea>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="updateMandatory"> Обязательное обновление
                </label>
            </div>
            <button class="btn btn-primary" onclick="createUpdate()">Создать обновление</button>
            
            <h3>Активные обновления</h3>
            <div id="updatesList">
                <p>Загрузка...</p>
            </div>
        </div>
        
        <!-- Устройства -->
        <div class="card">
            <h2>📱 Устройства</h2>
            <div id="devicesList">
                <p>Загрузка...</p>
            </div>
        </div>
    </div>

    <script>
        // Загрузка данных
        async function loadData() {
            try {
                // Загрузка статистики
                const statsResponse = await fetch('/api/stats');
                const stats = await statsResponse.json();
                document.getElementById('totalDevices').textContent = stats.total_devices;
                document.getElementById('onlineDevices').textContent = stats.online_devices;
                document.getElementById('activeUpdates').textContent = stats.active_updates;
                
                // Загрузка режима обслуживания
                const maintenanceResponse = await fetch('/api/maintenance');
                const maintenance = await maintenanceResponse.json();
                updateMaintenanceUI(maintenance);
                
                // Загрузка обновлений
                const updatesResponse = await fetch('/api/updates');
                const updates = await updatesResponse.json();
                updateUpdatesList(updates);
                
                // Загрузка устройств
                const devicesResponse = await fetch('/api/devices');
                const devices = await devicesResponse.json();
                updateDevicesList(devices);
                
            } catch (error) {
                console.error('Ошибка загрузки данных:', error);
            }
        }
        
        function updateMaintenanceUI(maintenance) {
            const statusDiv = document.getElementById('maintenanceStatus');
            const messageTextarea = document.getElementById('maintenanceMessage');
            
            if (maintenance.enabled) {
                statusDiv.innerHTML = `<p style="color: #dc3545;">🔴 Режим обслуживания ВКЛЮЧЕН</p>`;
                messageTextarea.value = maintenance.message || '';
            } else {
                statusDiv.innerHTML = `<p style="color: #28a745;">🟢 Режим обслуживания ОТКЛЮЧЕН</p>`;
                messageTextarea.value = '';
            }
        }
        
        function updateUpdatesList(updates) {
            const listDiv = document.getElementById('updatesList');
            if (updates.length === 0) {
                listDiv.innerHTML = '<p>Нет активных обновлений</p>';
                return;
            }
            
            let html = '<table><tr><th>Версия</th><th>Обязательное</th><th>Создано</th><th>Действия</th></tr>';
            updates.forEach(update => {
                const mandatory = update.mandatory ? 'Да' : 'Нет';
                const created = new Date(update.created_at).toLocaleString();
                html += `<tr>
                    <td>${update.version}</td>
                    <td>${mandatory}</td>
                    <td>${created}</td>
                    <td>
                        <button class="btn btn-danger" onclick="deleteUpdate(${update.id})">Удалить</button>
                    </td>
                </tr>`;
            });
            html += '</table>';
            listDiv.innerHTML = html;
        }
        
        function updateDevicesList(devices) {
            const listDiv = document.getElementById('devicesList');
            if (devices.length === 0) {
                listDiv.innerHTML = '<p>Нет подключенных устройств</p>';
                return;
            }
            
            let html = '<table><tr><th>Устройство</th><th>Версия</th><th>Последний визит</th><th>Статус</th></tr>';
            devices.forEach(device => {
                const lastSeen = device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Никогда';
                const status = device.status === 'active' ? 
                    '<span class="status-online">🟢 Онлайн</span>' : 
                    '<span class="status-offline">🔴 Офлайн</span>';
                
                html += `<tr>
                    <td>${device.device_id}</td>
                    <td>${device.version}</td>
                    <td>${lastSeen}</td>
                    <td>${status}</td>
                </tr>`;
            });
            html += '</table>';
            listDiv.innerHTML = html;
        }
        
        // Функции управления
        async function toggleMaintenance() {
            const message = document.getElementById('maintenanceMessage').value;
            try {
                const response = await fetch('/api/maintenance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: true, message: message })
                });
                if (response.ok) {
                    loadData();
                    alert('Режим обслуживания включен');
                }
            } catch (error) {
                alert('Ошибка: ' + error.message);
            }
        }
        
        async function disableMaintenance() {
            try {
                const response = await fetch('/api/maintenance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: false })
                });
                if (response.ok) {
                    loadData();
                    alert('Режим обслуживания отключен');
                }
            } catch (error) {
                alert('Ошибка: ' + error.message);
            }
        }
        
        async function createUpdate() {
            const version = document.getElementById('updateVersion').value;
            const url = document.getElementById('updateUrl').value;
            const notes = document.getElementById('updateNotes').value;
            const mandatory = document.getElementById('updateMandatory').checked;
            
            if (!version || !url) {
                alert('Заполните версию и URL');
                return;
            }
            
            try {
                const response = await fetch('/api/updates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        version: version,
                        download_url: url,
                        release_notes: notes,
                        mandatory: mandatory
                    })
                });
                if (response.ok) {
                    loadData();
                    alert('Обновление создано');
                    // Очистка формы
                    document.getElementById('updateVersion').value = '';
                    document.getElementById('updateUrl').value = '';
                    document.getElementById('updateNotes').value = '';
                    document.getElementById('updateMandatory').checked = false;
                }
            } catch (error) {
                alert('Ошибка: ' + error.message);
            }
        }
        
        async function deleteUpdate(id) {
            if (!confirm('Удалить это обновление?')) return;
            
            try {
                const response = await fetch(`/api/updates/${id}`, { method: 'DELETE' });
                if (response.ok) {
                    loadData();
                    alert('Обновление удалено');
                }
            } catch (error) {
                alert('Ошибка: ' + error.message);
            }
        }
        
        // Загрузка данных при загрузке страницы
        loadData();
        
        // Обновление данных каждые 30 секунд
        setInterval(loadData, 30000);
    </script>
</body>
</html>
    ''')

@app.route('/api/register', methods=['POST'])
def register_device():
    """Регистрация нового устройства"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновляем или создаем устройство
        cursor.execute('''
            INSERT OR REPLACE INTO devices 
            (token, device_id, version, system_info, created_at, last_seen, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        ''', (
            data['token'],
            data['device_id'],
            data['version'],
            json.dumps(data['system_info']),
            data['created_at'],
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Device registered'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/maintenance', methods=['GET', 'POST'])
def maintenance():
    """Управление режимом обслуживания"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Установка режима обслуживания
        data = request.get_json()
        enabled = data.get('enabled', False)
        message = data.get('message', 'Технические работы')
        
        cursor.execute('''
            INSERT OR REPLACE INTO maintenance (id, enabled, message, updated_at)
            VALUES (1, ?, ?, ?)
        ''', (enabled, message, datetime.now().isoformat()))
        
        conn.commit()
        
        # Уведомляем все активные устройства
        if enabled:
            cursor.execute('SELECT token FROM devices WHERE status = "active"')
            devices = cursor.fetchall()
            for device in devices:
                # Здесь можно добавить отправку push-уведомлений
                pass
    
    # Получение текущего режима
    cursor.execute('SELECT * FROM maintenance WHERE id = 1')
    maintenance = cursor.fetchone()
    
    conn.close()
    
    if maintenance:
        return jsonify({
            'enabled': maintenance['enabled'],
            'message': maintenance['message'],
            'updated_at': maintenance['updated_at']
        })
    else:
        return jsonify({'enabled': False, 'message': '', 'updated_at': ''})

@app.route('/api/check-update')
def check_update():
    """Проверка обновлений"""
    try:
        current_version = request.args.get('current_version')
        device_token = request.args.get('device_token')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновляем время последнего визита устройства
        cursor.execute('UPDATE devices SET last_seen = ? WHERE token = ?', 
                      (datetime.now().isoformat(), device_token))
        
        # Получаем последнее активное обновление
        cursor.execute('''
            SELECT * FROM updates 
            WHERE active = TRUE 
            ORDER BY created_at DESC 
            LIMIT 1
        ''')
        latest_update = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if latest_update:
            # Сравниваем версии
            update_available = current_version != latest_update['version']
            
            return jsonify({
                'update_available': update_available,
                'version': latest_update['version'],
                'download_url': latest_update['download_url'],
                'release_notes': latest_update['release_notes'],
                'mandatory': latest_update['mandatory']
            })
        else:
            return jsonify({'update_available': False})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/updates', methods=['GET', 'POST'])
def manage_updates():
    """Управление обновлениями"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Создание нового обновления
        data = request.get_json()
        
        cursor.execute('''
            INSERT INTO updates (version, download_url, release_notes, mandatory, created_at, active)
            VALUES (?, ?, ?, ?, ?, TRUE)
        ''', (
            data['version'],
            data['download_url'],
            data.get('release_notes', ''),
            data.get('mandatory', False),
            datetime.now().isoformat()
        ))
        
        conn.commit()
    
    # Получение списка обновлений
    cursor.execute('SELECT * FROM updates WHERE active = TRUE ORDER BY created_at DESC')
    updates = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify(updates)

@app.route('/api/updates/<int:update_id>', methods=['DELETE'])
def delete_update(update_id):
    """Удаление обновления"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE updates SET active = FALSE WHERE id = ?', (update_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/api/devices')
def get_devices():
    """Получение списка устройств"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM devices ORDER BY last_seen DESC')
    devices = [dict(row) for row in cursor.fetchall()]
    
    # Определяем статус устройств (онлайн если были последние 5 минут)
    five_minutes_ago = datetime.now().timestamp() - 300
    
    for device in devices:
        if device['last_seen']:
            last_seen_time = datetime.fromisoformat(device['last_seen']).timestamp()
            if last_seen_time > five_minutes_ago:
                device['status'] = 'active'
            else:
                device['status'] = 'offline'
        else:
            device['status'] = 'offline'
    
    conn.close()
    
    return jsonify(devices)

@app.route('/api/stats')
def get_stats():
    """Получение статистики"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Всего устройств
    cursor.execute('SELECT COUNT(*) as count FROM devices')
    total_devices = cursor.fetchone()['count']
    
    # Онлайн устройства (были последние 5 минут)
    five_minutes_ago = datetime.now().isoformat()
    cursor.execute('SELECT COUNT(*) as count FROM devices WHERE last_seen > ?', (five_minutes_ago,))
    online_devices = cursor.fetchone()['count']
    
    # Активные обновления
    cursor.execute('SELECT COUNT(*) as count FROM updates WHERE active = TRUE')
    active_updates = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_devices': total_devices,
        'online_devices': online_devices,
        'active_updates': active_updates
    })

if __name__ == '__main__':
    init_db()
    print("🚀 Сервер управления запущен на http://localhost:5000")
    print("📊 Админ-панель доступна на http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
