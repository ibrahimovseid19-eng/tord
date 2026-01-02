import subprocess
import threading
import re
import time
import json
import sqlite3
import os
from datetime import datetime
from queue import Queue

# Database Setup for Logs
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "netguardian.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bettercap_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, 
                  device_ip TEXT, 
                  device_mac TEXT, 
                  platform TEXT, 
                  protocol TEXT, 
                  traffic_type TEXT,
                  details TEXT)''')
    
    # Table for Rogue Device Detection
    c.execute('''CREATE TABLE IF NOT EXISTS known_devices 
                 (mac TEXT PRIMARY KEY, 
                  first_seen TEXT, 
                  last_seen TEXT, 
                  vendor TEXT,
                  is_trusted INTEGER DEFAULT 0)''')
    
    conn.commit()
    conn.close()

init_db()


import shutil

class BettercapService:
    def __init__(self):
        self.process = None
        self.running = False
        self.output_queue = Queue()
        self.events_buffer = []
        self.lock = threading.Lock()
        
        # Real-time state
        self.devices = {}
        self.traffic_stats = {
            "YouTube": 0, "Instagram": 0, "Facebook": 0, "Twitter": 0, "WhatsApp": 0, "Other": 0
        }
        self.session_start = None

    def _find_binary(self):
        # 1. Check PATH
        path = shutil.which("bettercap")
        if path: return path
        
        # 2. Check current directory
        cwd_path = os.path.join(os.getcwd(), "bettercap.exe")
        if os.path.exists(cwd_path): return cwd_path
        
        # 3. Check backend directory
        backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bettercap.exe")
        if os.path.exists(backend_path): return backend_path
        
        return None

    def start_bettercap(self, interface=None):
        if self.running:
            return False
            
        binary = self._find_binary()
        if not binary:
            print("[-] CRITICAL: 'bettercap' binary not found in PATH or local directory.")
            print("[-] Please download Bettercap Windows binary and place 'bettercap.exe' in this folder.")
            return False

        # Enable local sniffing to see own traffic
        # 'net.show' will print the interface it selected so we can debug
        cmd = [
            binary, 
            "-no-colors", 
            "-eval", 
            "net.show; set net.sniff.local true; set net.sniff.verbose true; set net.sniff.output true; net.probe on; net.sniff on"
        ]
        
        try:
            # shell=False to avoid wrapping, direct execution
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merge stderr to see errors
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.running = True
            self.session_start = datetime.now()
            
            # Start reader thread
            t = threading.Thread(target=self._reader_loop)
            t.daemon = True
            t.start()
            return True
        except Exception as e:
            print(f"[-] Failed to start bettercap: {e}")
            return False

    def stop_bettercap(self):
        if self.process and self.running:
            self.running = False
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except:
                self.process.kill()
            self.process = None

    def _reader_loop(self):
        print("[*] Bettercap Listener Started...")
        while self.running and self.process:
            line = self.process.stdout.readline()
            if not line:
                break
            
            # 1. Show in Terminal (Synchronous Output)
            print(line.strip()) 
            
            # 2. Parse & Store
            self._parse_line(line)

    def _parse_line(self, line):
        # Clean ANSI codes if any (though -no-colors should handle it)
        clean_line = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', line).strip()
        
        timestamp = datetime.now().isoformat()
        
        # Regex Patterns
        # [net.sniff.sni] snippet:192.168.1.15 : 443 > 172.217.16.142 : 443 example.com
        # [net.sniff.dns] answer: example.com -> 1.2.3.4
        # [endpoint.new] endpoint 192.168.1.25 detected as ...
        
        # Detect New Endpoint
        if "endpoint.new" in clean_line or "endpoint.lost" in clean_line:
            # Example: [endpoint.new] endpoint 192.168.1.50 detected as 00:11:22:33:44:55 (Apple)
            # Rough parse
            try:
                parts = clean_line.split()
                # Iterate to find MAC-like and IP-like strings
                ip = None
                mac = None
                vendor = "Unknown"
                
                for p in parts:
                    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", p):
                       ip = p
                    elif re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", p):
                       mac = p
                
                if "(" in clean_line and ")" in clean_line:
                    vendor = clean_line.split("(")[1].split(")")[0]

                if ip or mac:
                    self.add_event("device", f"Device Activity: {ip or mac} ({vendor})")
                    if ip:
                        self.devices[ip] = {"mac": mac, "vendor": vendor, "last_seen": timestamp}
            except:
                pass

        # Detect Traffic (SNI/DNS)
        elif "net.sniff.sni" in clean_line or "net.sniff.dns" in clean_line or "https" in clean_line.lower():
            # Try to extract domain
            domain = None
            src_ip = "Unknown"
            
            # Basic domain extraction logic
            # Look for typical domain patterns
            domain_match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,})', clean_line)
            if domain_match:
                domain = domain_match.group(1)
            
            if domain:
                platform = self._identify_platform(domain)
                traffic_type = self._categorize_traffic(platform)
                
                # Update Stats
                # Update Stats
                with self.lock:
                    if platform != "Unknown":
                        self.traffic_stats[platform] = self.traffic_stats.get(platform, 0) + 1
                    else:
                        self.traffic_stats["Other"] = self.traffic_stats.get("Other", 0) + 1
                    
                self._log_to_db(src_ip, "Unknown", platform or "Web", "HTTPS/DNS", traffic_type, domain)
                
                if platform != "Unknown":
                    self.add_event("traffic", f"Visited: {platform} ({domain})")
                else:
                    self.add_event("traffic", f"Visited: {domain}")

    def _identify_platform(self, domain):
        d = domain.lower()
        if "youtube" in d or "googlevideo" in d: return "YouTube"
        if "instagram" in d or "cdninstagram" in d: return "Instagram"
        if "facebook" in d or "fbcdn" in d: return "Facebook"
        if "twitter" in d or "t.co" in d or "x.com" in d: return "Twitter"
        if "whatsapp" in d: return "WhatsApp"
        return "Unknown"

    def _categorize_traffic(self, platform):
        if platform == "YouTube": return "Video"
        if platform in ["Instagram", "Facebook", "Twitter"]: return "Social Media"
        if platform == "WhatsApp": return "Messaging"
        return "General"

    def add_event(self, event_type, message):
        event = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": event_type,
            "message": message
        }
        with self.lock:
            self.events_buffer.append(event)
            # Keep buffer small
            if len(self.events_buffer) > 50:
                self.events_buffer.pop(0)

    def _log_to_db(self, ip, mac, platform, protocol, t_type, details):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO bettercap_logs (timestamp, device_ip, device_mac, platform, protocol, traffic_type, details) VALUES (?,?,?,?,?,?,?)",
                      (datetime.now().isoformat(), ip, mac, platform, protocol, t_type, details))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")

    def execute(self, command):
        """Send a command to the running Bettercap process."""
        if self.running and self.process and self.process.stdin:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
                return True
            except Exception as e:
                print(f"[-] Command failed: {e}")
                return False
        return False

    def get_dashboard_data(self):
        with self.lock:
            return {
                "running": self.running,
                "events": list(self.events_buffer),
                "stats": self.traffic_stats.copy(),
                "devices": len(self.devices)
            }

# Singleton
bettercap_runner = BettercapService()
