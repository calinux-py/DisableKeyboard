# this could be written in powershell but fight me

import sys
import ctypes
import pyWinhook as hook
import pythoncom
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
import threading
import time

VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_K = 0x4B

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

class KeyboardManager(QObject):
    hotkey_triggered = pyqtSignal()
    status_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.hook = None
        self.hook_thread = None
        self.keyboard_blocked = False
        self.last_toggle_time = 0
        self.toggle_delay = 0.5

    def start_hook(self):
        if self.hook:
            return
        self.hook = hook.HookManager()
        self.hook.KeyDown = self.keyboard_event
        self.hook.HookKeyboard()
        self.hook_thread = threading.Thread(target=pythoncom.PumpMessages, daemon=True)
        self.hook_thread.start()
        self.status_update.emit("Keyboard hook started successfully.")

    def stop_hook(self):
        if self.hook:
            self.hook.UnhookKeyboard()
            self.hook = None
            self.status_update.emit("Keyboard hook stopped.")

    def is_key_pressed(self, *keys):
        return any(ctypes.windll.user32.GetKeyState(key) & 0x8000 for key in keys)

    def keyboard_event(self, event):
        current_time = time.time()
        if event.KeyID in {VK_LCONTROL, VK_RCONTROL, VK_LWIN, VK_RWIN}:
            return True

        if event.KeyID == VK_K:
            ctrl_pressed = self.is_key_pressed(VK_LCONTROL, VK_RCONTROL)
            win_pressed = self.is_key_pressed(VK_LWIN, VK_RWIN)

            if ctrl_pressed and win_pressed:
                if current_time - self.last_toggle_time > self.toggle_delay:
                    self.hotkey_triggered.emit()
                    self.last_toggle_time = current_time
                return False

        return not self.keyboard_blocked

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.keyboard_manager = KeyboardManager()
        self.init_ui()
        self.init_styles()
        self.update_button_text()
        self.keyboard_manager.hotkey_triggered.connect(self.toggle_keyboard)
        self.keyboard_manager.status_update.connect(self.update_status)
        self.keyboard_manager.start_hook()

    def init_ui(self):
        self.setWindowTitle("Keyboard Toggler")
        self.setGeometry(100, 100, 400, 300)
        central_widget = QWidget()
        layout = QVBoxLayout()

        title_label = QLabel("Keyboard Toggler")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title_label)

        self.button = QPushButton("Disable Keyboard")
        self.button.setMinimumHeight(50)
        self.button.clicked.connect(self.toggle_keyboard)
        layout.addWidget(self.button)

        instructions = QLabel("Hotkey: Ctrl + Win + K to toggle keyboard")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        layout.addWidget(self.status_log)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def init_styles(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)
        self.setStyleSheet("""
            QWidget {background-color: #353535; color: white; font-family: Arial;}
            QPushButton {
                background-color: #4a4a4a; color: white; border: 2px solid #6a6a6a;
                border-radius: 10px; padding: 10px;}
            QPushButton:hover {background-color: #5a5a5a;}
            QTextEdit {background-color: #252525; border: 1px solid #4a4a4a; border-radius: 5px;}
        """)

    def toggle_keyboard(self):
        self.keyboard_manager.keyboard_blocked = not self.keyboard_manager.keyboard_blocked
        self.update_button_text()
        status = "Keyboard disabled." if self.keyboard_manager.keyboard_blocked else "Keyboard enabled."
        self.update_status(status)

    def update_button_text(self):
        self.button.setText("Enable Keyboard" if self.keyboard_manager.keyboard_blocked else "Disable Keyboard")

    def update_status(self, message):
        self.status_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")

    def closeEvent(self, event):
        self.keyboard_manager.stop_hook()
        event.accept()

if __name__ == "__main__":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
