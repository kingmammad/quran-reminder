import sys
import json
import random
import requests
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QDialog, 
                             QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
                             QPushButton, QCheckBox, QComboBox, QWidget,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPalette


CONFIG_FILE = Path.home() / ".quran_reminder_config.json"
DEFAULT_CONFIG = {
    "interval_minutes": 60,
    "max_length": 250,
    "auto_start": True,
    "language": "both",
    "notification_duration": 25,
    "theme": "light"
}


class AyahFetcher(QThread):
    """Background thread for fetching Quranic verses"""
    ayah_fetched = pyqtSignal(str, str, str)

    def __init__(self, max_length):
        super().__init__()
        self.max_length = max_length
        self.total_ayahs = 6236
        self.api_url = "https://api.alquran.cloud/v1/ayah/{}/editions/quran-simple,fa.ansarian"

    def run(self):
        try:
            # Check internet connectivity first
            try:
                test_response = requests.get("https://www.google.com", timeout=3)
            except:
                # No internet, fail silently
                return
            
            while True:
                ayah_number = random.randint(1, self.total_ayahs)
                url = self.api_url.format(ayah_number)
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()["data"]
                
                arabic = data[0]["text"]
                persian = data[1]["text"]
                surah = data[0]["surah"]["number"]
                ayah = data[0]["numberInSurah"]
                reference = f"Quran {surah}:{ayah}"
                
                message = f"{arabic}\n\n{persian}\n— {reference}"
                
                if len(message) <= self.max_length:
                    self.ayah_fetched.emit(arabic, persian, reference)
                    break
                    
        except:
            # Fail silently - no error notifications
            pass


class BeautifulNotification(QWidget):
    """Beautiful compact notification with blur effect"""
    
    def __init__(self, arabic, persian, reference, duration, language="both", theme="light"):
        super().__init__()
        self.duration = duration
        self.language = language
        self.theme = theme
        self.init_ui(arabic, persian, reference)
        
    def init_ui(self, arabic, persian, reference):
        # Window flags for frameless, always on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Theme colors
        if self.theme == "dark":
            bg_color = "rgba(30, 30, 30, 0.92)"
            border_color = "rgba(39, 174, 96, 0.4)"
            title_color = "#ecf0f1"
            text_color = "#bdc3c7"
            text_secondary = "#95a5a6"
            accent_color = "#27ae60"
        else:  # light
            bg_color = "rgba(255, 255, 255, 0.85)"
            border_color = "rgba(39, 174, 96, 0.3)"
            title_color = "#2c3e50"
            text_color = "#2c3e50"
            text_secondary = "#34495e"
            accent_color = "#27ae60"
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Container widget with blur effect
        container = QWidget()
        container.setObjectName("container")
        container_layout = QVBoxLayout()
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(15, 12, 15, 12)
        
        # Header with icon, title and close button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel("📖")
        icon_label.setFont(QFont("Segoe UI Emoji", 16))
        header_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel("قرآن")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet(f"color: {title_color};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {text_secondary};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: #e74c3c;
            }}
        """)
        close_btn.clicked.connect(self.close_notification)
        header_layout.addWidget(close_btn)
        
        container_layout.addLayout(header_layout)
        
        # Arabic text (if needed)
        if self.language in ["both", "arabic"]:
            arabic_label = QLabel(arabic)
            arabic_label.setWordWrap(True)
            arabic_label.setAlignment(Qt.AlignRight)
            arabic_label.setFont(QFont("Traditional Arabic", 13))
            arabic_label.setStyleSheet(f"color: {text_color}; padding: 5px 0;")
            container_layout.addWidget(arabic_label)
        
        # Persian text (if needed)
        if self.language in ["both", "persian"]:
            persian_label = QLabel(persian)
            persian_label.setWordWrap(True)
            persian_label.setAlignment(Qt.AlignRight)
            persian_label.setFont(QFont("Segoe UI", 11))
            persian_label.setStyleSheet(f"color: {text_secondary}; padding: 5px 0;")
            container_layout.addWidget(persian_label)
        
        # Reference
        ref_label = QLabel(reference)
        ref_label.setAlignment(Qt.AlignCenter)
        ref_label.setFont(QFont("Segoe UI", 9))
        ref_label.setStyleSheet(f"color: {accent_color}; padding-top: 5px;")
        container_layout.addWidget(ref_label)
        
        container.setLayout(container_layout)
        
        # Blur/glass effect styling
        container.setStyleSheet(f"""
            #container {{
                background: {bg_color};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 3)
        container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        
        # Set compact size (like Telegram)
        self.setFixedWidth(350)
        self.adjustSize()
        
        # Position at bottom right
        self.position_notification()
        
        # Auto-close timer
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.close_notification)
        self.close_timer.start(self.duration * 1000)
        
        # Fade in animation
        self.setWindowOpacity(0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(0.98)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()
        
        # Slide in animation
        screen = QApplication.primaryScreen().geometry()
        start_pos = QPoint(screen.width() + 50, screen.height() - self.height() - 50)
        end_pos = QPoint(screen.width() - self.width() - 20, screen.height() - self.height() - 50)
        
        self.move(start_pos)
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(400)
        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(end_pos)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.slide_animation.start()
        
    def position_notification(self):
        """Position notification at bottom right of screen"""
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 50
        self.move(x, y)
    
    def close_notification(self):
        """Close with fade out animation"""
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(400)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out.finished.connect(self.close)
        self.fade_out.start()


class SettingsDialog(QDialog):
    """Settings dialog for configuring the reminder"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        
        # Theme-based styling
        if self.config.get("theme", "light") == "dark":
            self.setStyleSheet("""
                QDialog {
                    background: #2c3e50;
                }
                QLabel {
                    color: #ecf0f1;
                    font-size: 13px;
                }
                QSpinBox, QComboBox {
                    padding: 8px;
                    border: 2px solid #34495e;
                    border-radius: 6px;
                    background: #34495e;
                    color: #ecf0f1;
                    font-size: 13px;
                }
                QSpinBox:focus, QComboBox:focus {
                    border: 2px solid #27ae60;
                }
                QPushButton {
                    padding: 10px 20px;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QCheckBox {
                    color: #ecf0f1;
                    font-size: 13px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background: #f8f9fa;
                }
                QLabel {
                    color: #2c3e50;
                    font-size: 13px;
                }
                QSpinBox, QComboBox {
                    padding: 8px;
                    border: 2px solid #dce4ec;
                    border-radius: 6px;
                    background: white;
                    font-size: 13px;
                }
                QSpinBox:focus, QComboBox:focus {
                    border: 2px solid #27ae60;
                }
                QPushButton {
                    padding: 10px 20px;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QCheckBox {
                    color: #2c3e50;
                    font-size: 13px;
                }
            """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        

        
        # Theme setting
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light Mode", "Dark Mode"])
        theme_map = {"light": 0, "dark": 1}
        self.theme_combo.setCurrentIndex(theme_map.get(self.config.get("theme", "light"), 0))
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        # Interval setting
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Reminder Interval (minutes):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(self.config["interval_minutes"])
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)
        
        # Language setting
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Display Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Both Arabic & Persian", "Arabic Only", "Persian Only"])
        lang_map = {"both": 0, "arabic": 1, "persian": 2}
        self.lang_combo.setCurrentIndex(lang_map.get(self.config["language"], 0))
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)
        
        # Notification duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Notification Duration (seconds):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 60)
        self.duration_spin.setValue(self.config["notification_duration"])
        duration_layout.addWidget(self.duration_spin)
        layout.addLayout(duration_layout)
        
        # Max length
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Max Text Length:"))
        self.length_spin = QSpinBox()
        self.length_spin.setRange(100, 500)
        self.length_spin.setValue(self.config["max_length"])
        length_layout.addWidget(self.length_spin)
        layout.addLayout(length_layout)
        
        # Auto-start
        self.autostart_check = QCheckBox("Start reminders automatically on launch")
        layout.addWidget(self.autostart_check)
        self.autostart_check.setChecked(self.config["auto_start"])
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("background: #27ae60; color: white;")
        save_btn.clicked.connect(self.save_settings)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("background: #95a5a6; color: white;")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_settings(self):
        lang_map = {0: "both", 1: "arabic", 2: "persian"}
        theme_map = {0: "light", 1: "dark"}
        self.config["theme"] = theme_map[self.theme_combo.currentIndex()]
        self.config["interval_minutes"] = self.interval_spin.value()
        self.config["language"] = lang_map[self.lang_combo.currentIndex()]
        self.config["notification_duration"] = self.duration_spin.value()
        self.config["max_length"] = self.length_spin.value()
        self.config["auto_start"] = self.autostart_check.isChecked()
        self.accept()


class QuranReminderApp(QSystemTrayIcon):
    """Main application with system tray icon"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config = self.load_config()
        self.setIcon(self.create_icon())
        
        # Create menu
        self.menu = QMenu()
        
        self.show_now_action = self.menu.addAction("📖 Show Ayah Now")
        self.show_now_action.triggered.connect(self.show_ayah_now)
        
        self.menu.addSeparator()
        
        self.start_action = self.menu.addAction("▶️ Start Reminders")
        self.start_action.triggered.connect(lambda: self.start_reminders(False))
        
        self.stop_action = self.menu.addAction("⏸️ Pause Reminders")
        self.stop_action.triggered.connect(self.stop_reminders)
        self.stop_action.setEnabled(False)
        
        self.menu.addSeparator()
        
        self.settings_action = self.menu.addAction("⚙️ Settings")
        self.settings_action.triggered.connect(self.show_settings)
        
        self.menu.addSeparator()
        
        self.quit_action = self.menu.addAction("🚪 Quit")
        self.quit_action.triggered.connect(self.quit_app)
        
        self.setContextMenu(self.menu)
        
        # Timer for periodic reminders
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_and_show_ayah)
        
        # Current notification window
        self.current_notification = None
        
        self.show()
        
        # Auto-start if enabled (no notification)
        if self.config["auto_start"]:
            self.start_reminders(True)
    
    def create_icon(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QColor(39, 174, 96))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 32, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "ق")
        
        painter.end()
        return QIcon(pixmap)
    
    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def start_reminders(self, silent):
        """Start periodic reminders"""
        interval_ms = self.config["interval_minutes"] * 60 * 1000
        self.timer.start(interval_ms)
        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        
        if not silent:
            self.showMessage("Reminders Started", 
                            f"You will receive reminders every {self.config['interval_minutes']} minutes",
                            QSystemTrayIcon.Information, 3000)
    
    def stop_reminders(self, silent=False):
        """Stop periodic reminders"""
        self.timer.stop()
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        
        if not silent:
            self.showMessage("Reminders Paused", "Periodic reminders have been paused",
                            QSystemTrayIcon.Information, 3000)
    
    def show_ayah_now(self):
        """Fetch and show an ayah immediately"""
        self.fetch_and_show_ayah()
    
    def fetch_and_show_ayah(self):
        """Fetch ayah in background thread"""
        self.fetcher = AyahFetcher(self.config["max_length"])
        self.fetcher.ayah_fetched.connect(self.display_ayah)
        self.fetcher.start()
    
    def display_ayah(self, arabic, persian, reference):
        # Close previous notification if exists
        if self.current_notification:
            self.current_notification.close()
        
        # Create beautiful notification
        self.current_notification = BeautifulNotification(
            arabic, persian, reference, 
            self.config["notification_duration"],
            self.config["language"],
            self.config.get("theme", "light")
        )
        self.current_notification.show()
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.config)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.config
            self.save_config()
            
            if self.timer.isActive():
                self.stop_reminders(True)
                self.start_reminders(True)
    
    def quit_app(self):
        """Quit the application"""
        if self.current_notification:
            self.current_notification.close()
        self.hide()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    tray_app = QuranReminderApp()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()