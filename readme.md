# Keyboard Toggler

A lightweight tool to enable or disable keyboard input at will. This script uses a simple hotkey (`Ctrl + Win + K`) to toggle your keyboard on or off in real-time.

## Requirements

- **Python 3.x**  
- **PyQt5**  
- **pyWinhook**  
- **pythoncom**

## Installation

1. Clone or download this repository.  
2. Install dependencies:  
   ```powershell
   pip install pyqt5 pyWinhook
   ```
3. Run the script:  
   ```powershell
   python disablekeyboard.py
   ```

## Usage

- **Hotkey**: Press `Ctrl + Win + K` to toggle the keyboard.  
- **UI Button**: Click the button on the GUI to enable or disable the keyboard.  

When the keyboard is disabled, you won't be able to type until the hotkey or button is pressed again.
