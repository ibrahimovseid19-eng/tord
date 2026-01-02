import socket
import subprocess
import re
import platform
import threading
import time
import concurrent.futures
import os
from datetime import datetime
from backend.database import upsert_device, set_all_offline, get_db
import sqlite3

# Simple common vendor mapping for offline fallback
COMMON_VENDORS = {
    "BC:62:0E": "TP-Link",
    "44:F0:22": "Apple",
    "98:B9:59": "Dell",
    "52:54:00": "Tuya/Realtek",
    "12:34:56": "TestDevice"
}

def get_vendor(mac):
    # Normalize
    mac_clean = mac.upper().replace("-", ":")
    prefix = mac_clean[:8] # XX:XX:XX
    
    # Check simple list
    for k, v in COMMON_VENDORS.items():
        if mac_clean.startswith(k):
            return v
    
    # Try online API if available (optional)
    # Here we stick to offline as requested - returning generic if unknown
    return "Unknown Vendor"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_gateway():
    try:
        # Windows specific
        cmd = "ipconfig"
        output = subprocess.check_output(cmd, shell=True).decode('cp850', errors='ignore') # handling encoding
        
        # Simple parse for Default Gateway
        for line in output.split('\n'):
            if "Default Gateway" in line or "Varsayılan Ağ Geçidi" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    gw = parts[1].strip()
                    if gw and gw != "0.0.0.0" and "::" not in gw:
                        return gw
        return "Unknown"
    except:
        return "Unknown"

def ping_host(ip):
    # Optimized ping for network scanning
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
    # 200ms timeout for speed, enough for LAN
    timeout_val = '200' 
    
    # Hide window in Windows
    startupinfo = None
    if platform.system().lower() == 'windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    try:
        command = ['ping', param, '1', timeout_param, timeout_val, ip]
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo) == 0
    except:
        return False

def run_network_scan():
    """
    1. Determine Subnet
    2. Ping Sweep (thread pool)
    3. Read ARP Table
    4. Save to DB
    """
    local_ip = get_local_ip()
    if local_ip == "127.0.0.1":
        return []

    subnet_base = ".".join(local_ip.split(".")[:3])
    
    # 1. Ping Sweep to populate ARP
    # Using threads for speed - optimized for stability
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        futures = []
        for i in range(1, 255):
            futures.append(executor.submit(ping_host, f"{subnet_base}.{i}"))
        
        # Wait for completion to ensure ARP table is populated
        concurrent.futures.wait(futures, timeout=10) 

    # 2. Read ARP
    devices = []
    try:
        # -a displays all interfaces
        output = subprocess.check_output("arp -a", shell=True).decode('cp850', errors='ignore')
        
        # Helper to determine device type
        def guess_type(name, vendor):
            n = name.lower()
            v = vendor.lower()
            if "phone" in n or "apple" in v or "samsung" in v or "xiaomi" in v: return "phone"
            if "desktop" in n or "win" in n or "dell" in v or "msi" in v: return "desktop"
            if "laptop" in n or "macbook" in n: return "laptop"
            if "tv" in n or "lg" in v: return "iot"
            if "gateway" in n or "router" in n or "modem" in n: return "router"
            return "iot" # default fallback
                    
        # ... logic continues below as original processing ...

        for line in output.split('\n'):
            line = line.strip()
            # Regex for IP and MAC
            # 192.168.1.1       bc-62-0e-12-35-01     dynamic
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)\s+(\w+)', line)
            if match:
                ip, mac, type_ = match.groups()
                mac = mac.replace("-", ":").upper()
                
                # Filter multicast/broadcast/invalid
                if ip.startswith("224.") or ip == "255.255.255.255":
                    continue
                if not (ip.startswith("192.") or ip.startswith("10.") or ip.startswith("172.")):
                    continue
                    
                # Try hostname
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except:
                    hostname = f"Device-{ip.split('.')[-1]}"
                
                vendor = get_vendor(mac)
                dev_type = guess_type(hostname, vendor)
                
                device = {
                    "ip": ip,
                    "mac": mac,
                    "name": hostname,
                    "vendor": vendor,
                    "type": dev_type,
                    "status": "online",
                    "os": "Unknown"
                }
                
                # Save to DB
                upsert_device(device)
                
                # Check Rogue Status
                check_rogue_status(device)
                
                devices.append(device)
                
    except Exception as e:
        print(f"Error scanning: {e}")
    
    # Sync status: Mark devices not found in this scan as OFFLINE
    if devices:
        found_macs = [d['mac'] for d in devices]
        from backend.database import update_online_status
        update_online_status(found_macs)
        
    return devices

def check_rogue_status(device):
    """
    Check if device is known using backend.database logic (implied or direct).
    For now, we do a direct SQLite check here or assume upsert_device handles it?
    Actually, let's do a direct check to update the 'is_new' flag or alert.
    But since we don't have the DB connection here comfortably without import, 
    let's add this logic to database.py or do it here.
    """
    try:
        conn = sqlite3.connect("netguardian.db")
        c = conn.cursor()
        
        # Check if exists
        c.execute("SELECT first_seen FROM known_devices WHERE mac = ?", (device['mac'],))
        row = c.fetchone()
        
        now = datetime.now().isoformat()
        
        if row:
            # Known device, update last seen
            c.execute("UPDATE known_devices SET last_seen = ? WHERE mac = ?", (now, device['mac']))
        else:
            # New Rogue Device!
            msg = f"ROGUE DEVICE: {device['mac']} ({device['vendor']})"
            print(f"[!] {msg}")
            
            # Inject into GUI stream
            try:
                from backend.bettercap_service import bettercap_runner
                bettercap_runner.add_event("security", msg)
            except:
                pass
                
            c.execute("INSERT INTO known_devices (mac, first_seen, last_seen, vendor, is_trusted) VALUES (?, ?, ?, ?, 0)",
                      (device['mac'], now, now, device['vendor']))
        
        conn.commit()
        conn.close()
    except:
        pass

class NetworkScanner:
    def __init__(self):
        self.scanning = False
        
    def start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        
        # Run in background thread
        t = threading.Thread(target=self._scan_thread)
        t.daemon = True
        t.start()
        
    def _scan_thread(self):
        try:
            # First mark all as offline (optional, or rely on update)
            # set_all_offline() 
            # Actually, let's keep them and update status 'online' for found ones
            
            run_network_scan()
        finally:
            self.scanning = False

scanner = NetworkScanner()
