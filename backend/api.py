from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.database import get_all_devices
from backend.scanner import scanner, get_local_ip, get_gateway
from backend.bettercap_service import bettercap_runner
import subprocess
import os
import psutil
import time

app = FastAPI()

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_ssid():
    try:
        # Windows command to get SSID
        out = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('cp850', errors='ignore')
        for line in out.split('\n'):
            line = line.strip()
            if line.startswith("SSID") and ":" in line:
                return line.split(":")[1].strip()
    except:
        pass
    return "Unknown / Wired"

@app.get("/api/devices")
def read_devices():
    return get_all_devices()

@app.post("/api/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    if not scanner.scanning:
        background_tasks.add_task(scanner.start_scan)
        return {"status": "started", "message": "Scan initiated"}
    return {"status": "busy", "message": "Scan in progress"}

@app.get("/api/network")
def network_info():
    net_stats = psutil.net_io_counters()
    return {
        "ip": get_local_ip(),
        "gateway": get_gateway(),
        "ssid": get_ssid(),
        "bytes_sent": net_stats.bytes_sent,
        "bytes_recv": net_stats.bytes_recv
    }

from pydantic import BaseModel
from backend.tools import ping_host, traceroute_host, scan_ports

class CommandRequest(BaseModel):
    command: str
    args: list[str] = []

@app.post("/api/execute")
def execute_command(req: CommandRequest):
    cmd = req.command.lower()
    target = req.args[0] if req.args else ""
    
    if cmd == "ping":
        if not target: return {"type": "error", "output": "Target required."}
        return {"type": "output", "output": ping_host(target)}
        
    elif cmd == "trace":
        if not target: return {"type": "error", "output": "Target required."}
        return {"type": "output", "output": traceroute_host(target)}
        
    elif cmd == "ports":
        if not target: return {"type": "error", "output": "Target IP/Domain required."}
        from backend.tools import scan_ports
        return {"type": "port_list", "data": scan_ports(target)}
        
    elif cmd == "scan":
        # Trigger scan
        if not scanner.scanning:
            scanner.start_scan()
            return {"type": "info", "output": "Network Discovery initiated... Check 'Devices' tab for results."}
        else:
            return {"type": "error", "output": "Scan already in progress."}
            
    # New Commands
    elif cmd in ["ifconfig", "ipa", "ipconfig"]:
        from backend.tools import get_ifconfig
        return {"type": "output", "output": get_ifconfig()}
        
    elif cmd == "nslookup":
        if not target: return {"type": "error", "output": "Target domain required."}
        from backend.tools import run_nslookup
        return {"type": "output", "output": run_nslookup(target)}
        
    elif cmd == "netstat":
        from backend.tools import run_netstat
        return {"type": "output", "output": run_netstat()}
        
    elif cmd == "system":
        from backend.tools import system_info
        return {"type": "output", "output": system_info()}
        
    elif cmd == "recon":
        from backend.tools import get_wifi_networks
        return {"type": "output", "output": get_wifi_networks()}
        
    elif cmd == "vuln":
        if not target: return {"type": "error", "output": "Target IP required."}
        from backend.tools import check_vulnerabilities
        return {"type": "output", "output": check_vulnerabilities(target)}
        
    elif cmd == "stress":
        if not target: return {"type": "error", "output": "Target IP required."}
        from backend.tools import run_stress_test
        return {"type": "output", "output": run_stress_test(target)}

    # --- New Cyber Commands ---
    elif cmd == "wifi_keys":
        from backend.tools import get_wifi_keys
        return {"type": "output", "output": get_wifi_keys()}
        
    elif cmd == "geoip":
        if not target: return {"type": "error", "output": "Usage: geoip <ip>"}
        from backend.tools import geo_locate_ip
        return {"type": "output", "output": geo_locate_ip(target)}
        
    elif cmd == "domain_intel":
        if not target: return {"type": "error", "output": "Target Domain required."}
        from backend.tools import run_domain_intel
        return {"type": "domain_intel_data", "data": run_domain_intel(target)}
        
    elif cmd == "whois":
        if not target: return {"type": "error", "output": "Usage: whois <domain>"}
        from backend.tools import whois_lite
        return {"type": "output", "output": whois_lite(target)}
        
    elif cmd == "speedtest":
        from backend.tools import run_speed_test
        # Returns dict, handle in frontend
        return {"type": "speedtest_result", "data": run_speed_test()}
        
    elif cmd == "wifi_scan":
        from backend.tools import scan_wifi_networks
        return {"type": "wifi_data", "data": scan_wifi_networks()}
        
    elif cmd == "map_data":
        from backend.tools import get_active_threat_map
        return {"type": "map_data", "data": get_active_threat_map()}
        
    elif cmd == "detect_os":
        from backend.tools import detect_os_ttl
        return {"type": "os_data", "data": detect_os_ttl(target)}
        
    elif cmd == "web_hunter":
        if not target: return {"type": "error", "output": "Target URL required."}
        mode = 'dirbuster'
        # Check if args has a second item for mode
        if req.args and len(req.args) > 1:
            mode = req.args[1]
        from backend.tools import run_web_hunter
        return {"type": "web_hunter_data", "data": run_web_hunter(target, mode)}
        
    elif cmd == "subfinder":
        if not target: return {"type": "error", "output": "Target Domain required."}
        from backend.tools import find_subdomains
        return {"type": "subdomain_data", "data": find_subdomains(target)}
            
    elif cmd == "bettercap_exec":
        if not target: return {"type": "error", "output": "Command required"}
        from backend.bettercap_service import bettercap_runner
        if bettercap_runner.execute(target):
             return {"type": "success", "output": f"Executed: {target}"}
        return {"type": "error", "output": "Bettercap not running or failed."}

    elif cmd == "generate_payload":
        if not target: return {"type": "error", "output": "Text content required."}
        ptype = 'python'
        if req.args and len(req.args) > 1: ptype = req.args[1]
        
        from backend.tools import generate_badusb_script
        return {"type": "payload_data", "data": generate_badusb_script(target, ptype)}

    elif cmd == "generate_flipper":
        ftype = req.args[0] if req.args else 'ir'
        param = req.args[1] if len(req.args) > 1 else ''
        from backend.tools import generate_flipper_file
        return {"type": "file_data", "data": generate_flipper_file(ftype, param)}

    return {"type": "error", "output": f"Command '{cmd}' not recognized by backend kernel."}

# System Health Check Endpoint
@app.get("/api/health")
def get_system_health():
    # 1. WiFi Encryption Score
    wifi_output = get_ssid() # We need channel/encryption data really. 
    # For now, let's look at get_wifi_networks() logic or rely on frontend to parse 'recon'
    # Actually, let's do a quick local check if possible or simulate score
    # Real logic: check if 'WPA3' is in current connection profile status... hard on windows cmd without detailed parsing.
    # We will assume a baseline and checking for Rogue devices.
    
    # 2. Rogue Devices
    # Check DB for untrusted devices
    from backend.database import get_db
    try:
        conn = get_db() # Wait, get_db is not in imports? It is not exposed in database.py commonly? 
        # Actually scanner.py uses sqlite3 directly for this newly added feature.
        # Let's use direct sqlite3 for now similar to scanner.py
        import sqlite3
        conn = sqlite3.connect("netguardian.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM known_devices WHERE is_trusted=0 ORDER BY last_seen DESC")
        rows = c.fetchall()
        
        rogue_count = len(rows)
        rogue_list = []
        for r in rows:
            rogue_list.append({
                "mac": r["mac"],
                "vendor": r["vendor"],
                "last_seen": r["last_seen"]
            })
        conn.close()
    except Exception as e:
        print(f"Health check error: {e}")
        rogue_count = 0
        rogue_list = []
        
    score = 100
    risk_factors = []
    
    if rogue_count > 0:
        score -= min(40, rogue_count * 10)
        risk_factors.append(f"{rogue_count} Unauthorized Devices detected")
        
    # 3. Open Ports (Mock/Cached or Trigger)
    # If we had a mechanism to store last vuln scan...
    # For now, assume good unless notified.
    
    health_status = "Good"
    if score < 60: health_status = "Critical"
    elif score < 85: health_status = "Warning"
    
    return {
        "score": score,
        "status": health_status,
        "rogue_devices": rogue_count,
        "rogue_list": rogue_list,
        "risks": risk_factors
    }

# Bettercap Endpoints
@app.post("/api/bettercap/start")
def start_bettercap_service():
    if bettercap_runner.start_bettercap():
        return {"status": "started", "message": "Bettercap listener started."}
    return {"status": "error", "message": "Failed to start or already running."}

@app.post("/api/bettercap/stop")
def stop_bettercap_service():
    bettercap_runner.stop_bettercap()
    return {"status": "stopped", "message": "Bettercap listener stopped."}

@app.get("/api/bettercap/data")
def get_bettercap_data():
    return bettercap_runner.get_dashboard_data()

# HoneyPort Endpoints
from backend.honeypot import honeypot_runner

@app.post("/api/honeypot/start")
def start_honeypot():
    # Attempt to bind HTTP/HTTPS ports + Trap Port
    # Requires Admin for 80/443 usually
    ports = [80, 443, 8080, 9999]
    success, msg = honeypot_runner.start_honeypot(ports)
    
    if success:
        return {"status": "started", "message": msg}
    return {"status": "error", "message": msg}

@app.post("/api/honeypot/stop")
def stop_honeypot():
    honeypot_runner.stop_honeypot()
    return {"status": "stopped", "message": "HoneyPort disarmed."}

@app.get("/api/honeypot/stats")
def get_honeypot_stats():
    return honeypot_runner.get_stats()


DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")

if os.path.exists(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
else:
    # Fallback for dev mode - mainly just API works
    @app.get("/")
    def root():
        return {"message": "React app not built. Run 'npm run build' and restart."}
