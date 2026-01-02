import socket
import threading
import time
from datetime import datetime

class HoneyPortService:
    def __init__(self):
        self.running = False
        self.sockets = []
        self.active_ports = []
        self.intrusions = []
        self.lock = threading.Lock()

    def start_honeypot(self, ports=[80, 443, 8080, 9999]):
        if self.running:
            return False, "Already running"
        
        self.running = True
        self.sockets = []
        self.active_ports = []
        
        status_msgs = []

        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
                s.listen(5)
                
                self.sockets.append(s)
                self.active_ports.append(port)
                
                # Start listener thread for this port
                t = threading.Thread(target=self._listen_loop, args=(s, port))
                t.daemon = True
                t.start()
                status_msgs.append(f"{port} (OK)")
            except Exception as e:
                # Often fails on 80/443 if not Admin or in use
                status_msgs.append(f"{port} (FAIL: {e})")

        if not self.active_ports:
            self.running = False
            return False, "Failed to bind any ports. Run as Admin for 80/443."
            
        print(f"[*] HoneyPort Armed on: {self.active_ports}")
        return True, f"HoneyPort Active: {', '.join(status_msgs)}"

    def stop_honeypot(self):
        self.running = False
        for s in self.sockets:
            try:
                s.close()
            except:
                pass
        self.sockets = []
        self.active_ports = []

    def _listen_loop(self, sock, port):
        print(f"[*] Trap active on port {port}")
        while self.running:
            try:
                sock.settimeout(1.0) # Check running flag every second
                try:
                    client, addr = sock.accept()
                except socket.timeout:
                    continue
                except:
                    break # Socket closed

                ip = addr[0]
                
                # Log Intrusion
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[!] HONEYPOT PORT {port} TRIGGERED by {ip}")
                
                with self.lock:
                    self.intrusions.insert(0, {
                        "ip": ip,
                        "time": timestamp,
                        "port": port,
                        "risk": "CRITICAL" if port in [80, 443] else "HIGH"
                    })
                    if len(self.intrusions) > 50:
                        self.intrusions.pop()

                # Send fake response based on port
                try:
                    msg = b"ACCESS DENIED\n"
                    if port in [80, 8080]:
                        msg = b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nSecurity Alert: IP Logged."
                    
                    client.send(msg)
                    time.sleep(0.1)
                    client.close()
                except:
                    pass
                    
                # Inject into Bettercap
                try:
                    from backend.bettercap_service import bettercap_runner
                    bettercap_runner.add_event("intrusion", f"TRAP: {ip} -> Port {port}")
                except:
                    pass

            except Exception as e:
                if self.running:
                    print(f"[-] Honeypot port {port} error: {e}")
                break

    def get_stats(self):
        with self.lock:
            return {
                "running": self.running,
                "port": self.active_ports if self.active_ports else [], # Backward compatibility key or just use ports
                "ports": self.active_ports,
                "intrusions": list(self.intrusions),
                "count": len(self.intrusions)
            }

honeypot_runner = HoneyPortService()
