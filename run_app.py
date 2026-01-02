import sys
import subprocess
import threading
import time
import os

def install_requirements():
    """Auto-install dependencies if missing."""
    reqs = ["fastapi", "uvicorn", "psutil", "requests", "PySide6"]
    try:
        import fastapi
        import uvicorn
        import psutil
        import PySide6
    except ImportError:
        print("Installing necessary libraries (PySide6 backend)...")
        # Use --only-binary to avoid build issues if possible, or just standard install
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + reqs)

def run_server():
    try:
        import uvicorn
    except ImportError:
        return
        
    print("Starting backend engine...")
    # Hide banner to keep it clean
    sys.argv = [sys.argv[0]] # clean args for uvicorn
    uvicorn.run("backend.api:app", host="127.0.0.1", port=49152, log_level="error")

def main():
    # 1. Install deps logic
    install_requirements()
    
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtCore import QUrl, Qt
        from PySide6.QtGui import QIcon
    except ImportError:
        print("CRITICAL: PySide6 install failed or incomplete. Falling back to system browser mode not supported in this strict mode.")
        return

    # 2. Start Backend Server
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    # Wait a moment for server to spin up
    time.sleep(1.5)
    
    # 3. Launch App Window (Qt6)
    app = QApplication(sys.argv)
    app.setApplicationName("NetGuardian Pro")
    
    window = QMainWindow()
    window.setWindowTitle("NetGuardian Pro")
    window.resize(450, 850) # Mobile-like aspect ratio as requested
    
    # Center on screen (rough calculation)
    screen_geometry = app.primaryScreen().geometry()
    x = (screen_geometry.width() - window.width()) // 2
    y = (screen_geometry.height() - window.height()) // 2
    window.move(x, y)

    view = QWebEngineView()
    # Enable some dev settings if needed, or keep clean
    view.setUrl(QUrl("http://127.0.0.1:49152"))
    
    window.setCentralWidget(view)
    window.show()
    
    print("Application started. Close the window to exit.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
