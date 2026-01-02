import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QSize

class HiddenWebApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NetGuardian Secure Core")
        self.resize(1100, 700)
        
        # Modern Dark Theme for the Container
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: white;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Web Engine Logic
        self.web = QWebEngineView()
        self.web.setContextMenuPolicy(Qt.NoContextMenu) # Disable right click context menu to hide web nature
        self.web.hide()

        # Main Button Container (Centering logic)
        self.btn_container = QFrame()
        self.btn_layout = QVBoxLayout(self.btn_container)
        
        self.button = QPushButton("SİSTEMİ BAŞLAT")
        self.button.setFixedSize(280, 280)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #58a6ff;
                font-size: 24px;
                font-weight: bold;
                border: 2px solid #30363d;
                border-radius: 140px; /* Fully circular */
                box-shadow: 0 0 20px rgba(88, 166, 255, 0.2);
            }
            QPushButton:hover {
                background-color: #1f2428;
                border-color: #58a6ff;
                box-shadow: 0 0 30px rgba(88, 166, 255, 0.4);
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #0d1117;
                border-color: #1f6feb;
            }
        """)
        self.button.clicked.connect(self.run_script)
        
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.button, 0, Qt.AlignCenter)
        self.btn_layout.addStretch()

        # Main Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.btn_container)
        self.main_layout.addWidget(self.web)
        
        self.setLayout(self.main_layout)

    def run_script(self):
        # Determine the path to the local HTML file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, "assets", "hidden_content.html")
        
        # Load Local HTML
        self.web.load(QUrl.fromLocalFile(html_path))
        
        # Smooth Transition Simulation (Switch widgets)
        self.btn_container.hide()
        self.web.show()

if __name__ == "__main__":
    # Ensure High DPI scaling support
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = HiddenWebApp()
    window.show()
    sys.exit(app.exec_())
