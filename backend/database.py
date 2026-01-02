import sqlite3
import json
import os
from datetime import datetime

DB_PATH = 'netguardian.db'

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Devices table
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        ip TEXT,
        name TEXT,
        vendor TEXT,
        type TEXT,
        status TEXT,
        first_seen TEXT,
        last_seen TEXT,
        os TEXT
    )''')
    
    # Scan history/snapshots
    c.execute('''CREATE TABLE IF NOT EXISTS scan_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        device_count INTEGER,
        snapshot JSON
    )''')
    
    conn.commit()
    conn.close()

def upsert_device(device):
    conn = get_db()
    c = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if exists
    c.execute("SELECT * FROM devices WHERE mac=?", (device['mac'],))
    existing = c.fetchone()
    
    if existing:
        c.execute('''UPDATE devices SET 
            ip=?, name=?, vendor=?, status=?, last_seen=?, type=?, os=?
            WHERE mac=?''', 
            (device['ip'], device['name'], device['vendor'], 
             device['status'], now, device['type'], device.get('os', 'Unknown'), device['mac']))
    else:
        c.execute('''INSERT INTO devices 
            (mac, ip, name, vendor, type, status, first_seen, last_seen, os)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (device['mac'], device['ip'], device['name'], device['vendor'], 
             device['type'], device['status'], now, now, device.get('os', 'Unknown')))
    
    conn.commit()
    conn.close()

def get_all_devices():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM devices ORDER BY last_seen DESC")
    rows = c.fetchall()
    conn.close()
    
    devices = []
    for row in rows:
        d = dict(row)
        # Add 'id' field for frontend compatibility
        d['id'] = d['mac']
        # Map snake_case to camelCase for frontend
        d['lastSeen'] = d.get('last_seen', '')
        d['firstSeen'] = d.get('first_seen', '')
        devices.append(d)
    return devices

def update_online_status(active_macs):
    """Mark devices as offline if they are not in the active_macs list."""
    if not active_macs:
        return
        
    conn = get_db()
    c = conn.cursor()
    
    # Create placeholders for SQL query
    placeholders = ','.join('?' * len(active_macs))
    
    # Set online for active ones (redundant if upsert does it, but good for safety)
    # Actually upsert handles 'online'. We just need to handle 'offline'.
    
    # Set ALL others to offline
    query = f"UPDATE devices SET status='offline' WHERE mac NOT IN ({placeholders})"
    c.execute(query, active_macs)
    
    conn.commit()
    conn.close()

def set_all_offline():
    """Mark all as offline before scan"""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE devices SET status='offline'")
    conn.commit()
    conn.close()

init_db()
