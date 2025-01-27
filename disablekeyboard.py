# this could be written in powershell but fight me

import sys
import ctypes
import pyWinhook as hook
import pythoncom
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
import threading
import time
import base64
from io import BytesIO

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

        self.setWindowIcon(self.get_embedded_icon())

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

    def get_embedded_icon(self):
        icon_base64 = """
        iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAACAASURBVHic7d1tcFzXfd/x37l3FyCeCAIgCBCUSAGkRFvUY0JbthxXD7Yky6nbZKbR1G6Uxk3U2LWjyUOTTDqTREmn6TjJNKkTO/HYEztxJp4qnTaJE8eSbT2kjmTZkmNbpCxaFEjxCSABEiSegd17T1+AsCAKAHexd/fcc+/3804aAvvH3v2f87vnnntXAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACki3FdQKMNfMK2NtuZq02sXhnbKUmy5oKVzpTm21468QtmznGJAADUXeYDwJ6P2uZyYepeI/PDkt4uae86/9zK6pCM/tHG9guFuOOLhx80Cw0qFQCAhslsABj6xNxOReWft9JPStqywV8zIdlPB7bwBy9/qPV4guUBAOBU5gLA0CfOdSoqPmSlD0kqJvRrF2XtH4ZR6bcOP9gzmdDvBADAmUwFgME/mb5Lsf0zSdvr9BKnTGx+YvjD7V+p0+8HAKAhAtcFJMJaM/SxqYcU2y+qfpO/JA3YwD561cenfl3WZio8AQDyxf9J7GEbDo5P/4mkn27wK3/qyNb2D+g+EzX4dQEAqJnfKwDWGkeTvyT99OD49Oduf8gWHLw2AAA18ToADH18+jfkZvJf9mNH+6b/XA/b0GENAABUzdtLALs+NnVHYPQlSWmYfP9q15n29z3xkCm7LgQAgEp4GQCGPnGu00bF76q+G/6qYo0+d7Sn/X72BAAAfODnJYCo+JBSNPlLkrF6L3sCAAC+8G4FYOgTczttVD6s5B7ykyhWAgAAPvBvBSAq/7xSOvlLrAQAAPzg1QrAvodt0+z49Iikbte1VICNgQCA1PJqBWD67NQPy4/JX+IWQQBAinkVAAJr3u26hmpwOQAAkFZeBQBJ/8J1ARvASgAAIHW82QMw8Anb2hxNT8ujmi/BngAAQGp4swLQHM3skb+Tv8RKAAAgRbwJALLqd11CrdgTAABIC28CgJFtd11DQn7slW3Tf0kIAAC45E0AiAJrXdeQIEIAAMApbwJAEAczrmtIGCEAAOCMNwFARqOuS6gDNgYCAJzwJgAshG2HJWXpMoAkNgYCANzwJgCc+hkzK+l7ruuoE1YCAAAN5U0AkCQZ/aPrEuqFlQAAQCN5FQBsZP/edQ11xkoAAKAhvAoAbds6/kHSWdd11BMrAQCARvAqABy8zyxK9s9c19EA3CIIAKgrrwKAJIXlwu9LWnRdRwNwOQAAUDfeBYDDD7aekOwfua6jEbgcAACoF+8CgCSF5dJvSjrluo4GYSUAAJA4LwPA4Qd7Jq3Rv5MUua6lEVgJAAAkzcsAIElHP9jxhJV+y3UdDcRKAAAgMcZ1AbUa/NjUH8row67raKC/2nWm/X1PPGTKrgsBAPjL2xWAZUd623/OGn3OdR0NxEoAAKBm3gcA3Weioz3t90v2L1yX0ijsCQAA1Mr7SwDf97ANB8enPiOZH3ddSgNxOQAAsCHZCQASIQAAgAplKwBIhAAAACqQvQAgEQIAALiMbAYAiRAAAMA6shsAJEIAAABryHYAkAgBAACsIvsBQCIEAABwiXwEAIkQAADACvkJABIhAACAi/IVACRCAAAAymMAkAgBAIDcy2cAkAgBAIBcy28AkAgBAIDcyncAkAgBAIBcIgBIhAAAQO4QAJYRAgAAOUIAWIkQAADICQLApQgBAIAcIACshhAAAMg4AsBaCAEAgAwjAKyHEAAAyCgCwOUQAgAAGUQAqAQhAACQMQSAShECAAAZQgCoRg5DwLa24Olfe0vzR5uKilzXAiC/wkDT5djOFAI7bU18PmpuPn1Pv5lxXZfPCABVeGx4fu+8De786DcWf+7QOXuN63oa5Qf7Qz1wY1EBnxYAqWKPS+Z7kjlkTPxtxfET79y96Xuuq/IFQ/o6Hhm1beFM9CMy8buszJ2SBiQpttKnny/pmVP5OSkmBADwgZVOGNnHZYMvzreEf/2eATPruqa0Yji/xEPWBm8bLt8qY+6X7Hsldaz27wgBAJB6c0b6u0jmsxcGwy/cZ0x+BuwKMJRf9OyztjjRHb1Xsv9F0t5KfoYQAAC+MMPWxB8tl4t/8u6rzYLratIg98P440fsprItPSDplyRzZbU/TwgAAJ/YV4zV75ybL37qvn1m0XU1LuV6CP/y0dIdNtbHJL2xlt9DCAAA77wko5+9a7D4iOtCXMnl8P2V43aHLZV/30o/ltTvJAQAgIeM/Vxkir/4rqvMiOtSGi13Q/ejw+V/ZWQ/Lak76d9NCAAAL10wMj/9zqHC/3ZdSCPlZth+9llbPN9V/q/W6JdVx7+bEAAAXrJW+sPzc4VfysvegFwM2Y8fsf1lW/68pP2NeD1CAAB46+k4LvzIPXvMGdeF1Fvmh+tHjs4NBnHhEUlXN/J1CQEA4CszHMXle961Z9Nh15XUU6aH6kcOL1wXBMEjuvgEv0YjBACAt0atsffePdj0LdeF1Etmh+kvHV28WbF5XFKnyzoIAQDgrfNG8W3vHGr+jutC6iFwXUA9fOWl+d2KzRfkePKXpMBI77++qFsGQtelNMxzo5E++e2SYuu6EgCoyRar4IuPHJ0bdF1IPWQuAHzhJdsbh+EXJPW7rmUZIQAAvLU9sMUvfXnY9rkuJGmZCgAPH7RNxbD895JS91W9hAAA8JS1u63K//fZZ23RdSlJylQA2NJS/l1Jb3Jdx1oIAQDgrbdOdJd/23URScrMNq0vv1z+l9bYv5UHfxMbAwHAS1bG/Ohdg4W/cV1IEjIxHF98tv/zVupyXUulCAEA4KWzUVC4PgvfHZCJSwAXv9jHm8lf4nIAAHiqJ7Sl33NdRBK8Pxf78nDpLis96rqOjWIlAAD8E8d6xz17io+5rqMWXg/BDx+0TV0t5e9I2uu6lloQAgDAO98rRYUb3n21WXBdyEZ5fQmgq6X0M/J88pe4HAAAHrqmUCi933URtfD2/OvZZ21xorv0kmR2ua4lKawEAIBP7LGuc8U9+/ebkutKNsLbFYDz3aWfyNLkL7ESAAB+MTvP90Tvc13FRnkZAB6yNrAyv+K6jnogBACAP6y1v/qQtV7OpV4W/UPD5TslXe26jnohBACAN/beerT8dtdFbISXAcAae7/rGuqNEAAAnrDGyznJu61Xj4zatmC2PCqp3XUtjcDGQABIvcn5TYXt7xkws64LqYZ3KwBmNvpR5WTyl1gJAAAPbG5ZiN7juohqeRcAAsX3uK6h0QgBAJBuVvJubvIuAFhr7nBdgwuEAABIMRu/w3UJ1fIqADw2PL9XRjtc1+EKIQAA0srs/MpL87tdV1ENrwJAbILbXdfgGiEAANIpDoM7XddQDa8CgFVwo+sa0oAQAABpFNzguoJqeBUAjKz3X/yTFEIAAKSL9WyO8ioA2Nj/b/5LEiEAANLDt5NUbwLAI6O2TUYDrutIG0IAAKSFufLzp2yr6yoq5U0AsNML2+XhkwsbgRAAAKlgmhbn+1wXUSlvAkBYCDpc15BmhAAAcC+M/ZmrvAkAcWy8eVNdIQQAgFvWBptd11ApbwKAsSY3z/+vBSEAANwJQn9OVr0JAIGRNxsrXCMEAIAbNlab6xoq5U0AiNkAWBVCAAA0nk9zlTcBANUjBAAA1kIAyDhCAABgNQSAHCAEAAAuRQDICUIAAGAlAkCOEAIAAMsIADlDCAAASASAXCIEAAAIADlFCACAfCMA5BghAADyiwCQc4QAAMgnAgAIAQCQQwQASCIEAEDeEADwfYQAAMgPAgBegxAAAPlAAMDrEAIAIPsIAFgVIQAAso0AgDURAgAguwgAWBchAACyiQCAyyIEAED2FFwXgMaKrDS9aDVflsoXZ7dCYLSpILU3GYVm9Z9bDgGS9MypqFHlOvXc6NLf+cCNRQVrvC+SJCvNlKTZslXZWpUjqSk0KgRSe1FqLqz3w1jLQtlquiSVY2kxsiqEUsEYtRWl1oKReFurttH+RzYRADIuttLIVKzRWaszM7EmS5LWOqs10uai1NsWqL/NaKA9eM3ERwh49f+fm7c6NRXr9IzVxLxVtM5KQXNo1Ntq1NdmdEWH0SYCwarmylYnp6xGZ63GZ6wW1nlTQyN1bTLqazfa0Raoq4X3dDVJ9j+yhwCQUbNlq0NnYx29YLW43uy0kpUmF6XJxVgvT0hNYazBTqNreoKlMy7lOwT81A1FHZ2MdfhcpAsLlf/8QmR1YsrqxJT0zVFpe3ugN/QE6m1ldJWkMzNWh87FGpmJZSv8qEZWGp+zGp+zOjgWq7PJaE93oKEtTFpS/fof2UIAyJhSbHVgLNbhibjm69eLkdWhc1YvTcS6uivQvt5QxSC/IeDUdKw3dgcyNYyFVtKp6VinpmP1tRnd3Beqszmfg+v5BatvjkYam619o8WFRavnRiO9cDbWjdsC7dwc5PIKQSP6H9lBAMiQ0elYz4zEmi8nu3MtttKhc7GOTVm9eXuo/jaTyxAwMm0VxbGu21pbCFh2esbq0eGy3tgbaF9PmMjv9IGVdGAs0nfH4zVXozdqrmT1tZORjkzEumUgVEsxJ2+qGtv/yAbyXAYsD6hPnogSb/6V5kpWTx4v6+DY0sCdx7sDzsxaHRivfKn6cmJJB8diPXG8rIU6Hru0WIisHn+lrBfqMPmvdHrW6pEjyawupJ2r/of/CACes1b6xqmyDo7Ha2/uSfQFpQPjkZ4dKctaQkBiv3PG6ivHypotZXdonSlZPXa03LBJeSGyeuJYWSem4oa8nguu+x9+IwB4zEp6drSsIxca34nD562+PhKxEpDgWz+1ID3+SllzGVwJWIisnjxW1uRiY183ttJTJyOdnMxeCEhL/8NfBACPHRyLNHzeXQsevRDrhbGlgZUQkIzpkvTV49G6txX6JoqlJ49Fmmrw5L/MWunpkUgT8xl6U5Wu/oefCACeOjNr9cJZ98134Gyk0ZmlQYgQkIxz81bfGs3OxspvnnY/+Uax9E8nospviUu5NPY//EMA8FAplp4+GaXjGpyVvj4SqXRxLCIEJOPw+Vij0+4H+Fqdmo41fD4df8dMyerbp/0PVmnuf/iFAOCh58fqu9u3WnMlq4Njrw6shIBkPHc68vq7CKJY+ueUTbhHLliNe35nQNr7H/4gAHhmtmz18kT64vZLE7HmVuxgJwTUbnpROpKSs+eNGD4fa9rRdf+1WC1NoL7ypf/hBwKAZ148W/sTvuph+WEhKxECavfCWT93WltJL55L30QlLR0jX1cBfOp/pB8BwCOxlY5NprD7Lzpywb5ucCIE1Ga2JC/3AoxMx6l+psGRC/6tAvjY/0g3AoBHRqbiVD8tbjGyq05WhIDavOLgPu9avZLiiUqSjk+u/w2OaeRr/yO9CAAeGfFg2XJkjVuCCAEbNzpj/boMYKXT0+muuBTLu8sAPvc/0okA4JGxmfSn6zOza9dICNiYhchqcsGfgfX8gtWCB6fXY3Pp76eVfO9/pA8BwBNRLE2WXFdxeVOLWndplRCwMec9CwA+OL/guoLKZaX/kS4EAE9Ml2xjvuyjRtZerHUdhIDqTS16cPAv8qXW6QV/zlaz1P9IDwKAJ+Y92rS8UMGZCiGgOpW8p2mx6Mlndb7sz/faZ63/kQ4EAE+UPVpXK1d4LxAhoHI+nVSVPJmsSh7ds5bF/od7BAA4RQgAADcIAJ4ohP4sVxaC6molBFxe0Z/Dr6Inh7FY5efUpSz3P9whAHhikyeDqiQ1F6v/GULA+jbynrrS7Mkh3FTwZwkm6/0PNwgAnmhvMjIeBGtjpPYNnq4SAta2ucmDg39Rhye1tjf7M/zlof/ReP50QM6FRurwIFlvblqqdaMIAavrbPZnUO3c5EetW5pdV1C5vPQ/GosA4JFtbek/XL2ttddICHit5tBos08BoNmo2YNZYFtL+vtppbz0PxqHo+WRvrb0D6rb25OpkRDwqv52o/Qf+VcZSf0p/6wWA6Otremu8VJ56n80BgHAIwPtgZoL6W2wptCoP8GzFELAkqs2p/eYr2XXlnTXfOXmpc+XT/LW/6g/jpZHAiPtSvFkMNhpEh9U8x4CWotSn4eDan9boLYUbwYb2uLf5ymP/Y/68m9kybm9PUEqmyww0t7u+nyc8hwC3tgderH7+1JG0ht60jm89LUa9bR4+KYqn/2P+uGIeaa1YHR1V/oO2zXdgVrqeMaX1xDwlWORfH2y6uCWQO1p27lupBu2+fsZymv/oz7S90nCZe3rDVPVbK0Fo3299R9U8xgCnhuN9Mlvl7wMAaGRfqA/XcdqqDNQt6dn/8vy2v9IHgHAQ8VAumV7SpaGjfSmgVCN2ptECPDL9vZAu1NyxtpelG7qS0cttchz/yNZ/ndDTvW1Ge3rcT8JXr81bPgtX4QAv9y8LVSX47PuMJBu3VHw6vn/68lz/yM5BACPXdsbaGiLu0M4tCXQtVvdvD4hwB9hIN12ZajNTW5e3xjpLQPuQ0jS8tz/SAZHz2NG0v7+UEMO7rke2hJov+Pru4QAfzSHRrftLKijwY/fDY30toFQV3Rkb6jLe/+jdtnripwxRtq/vaDrtoZqxOPijJGu7w31ppRcgyQE+KO1aPSOnQVta9CScUthKXTs2JzdYS7v/Y/aFFwXgNoZSft6A21tNXpmJNJcqT4zQ2vB6JYdobal7BGqyyFAkp45FTmupjGeG136Ox+4sZjK+8LX0lwwuv3Kgg6ejfTdsVhxnV6nv83ozQOhWnKwOy3v/Y+NIwBkSF+b0b1DBR0ci/TSRJzYGWJopKu7A+3rTe9uX0KA42KqYIx03dZQV24O9M2RSGdmk5uwWotGN/YG2tmZ3bP+teS5/7ExBICMKQbSTX2h9nYHOnQu1tFJq4XyxkaC5tDoqk6jvZ485IMQ4LiYKnU2Gd2xq6CxWasXz8YamY610Tmrs9nomu5AV3Wm80l5jZLn/kf1CAAZ1VI0uqkv1A3bpNHpWCMzVmdmY00tas3vnTdG6miStrUG2t6+9MUevg2mhADHxWxAb6tRb2uohSjQ8Smr09NW43NW8+tMXGEgdW8y6msNtKPDaMsmD//wOspr/6M6BICMC4w00BFooEOSQsVWmlqUFiKrcrQ0EhTCpe9v72jy7xvSVkMIcFzMBjWHRnu2GO3ZsvTfi5HVdEkqRdJibFUwUiEwai0uLfV7+mc2VB77H5UjAORMYKTOZmlp61B2u50Q4LiYBDSFRt3fv7kjA39QCuSl/1GZ/O2UQW5wiyAArI0AgEwjBADA6ggAyDxCAAC8HgEAuUAIAIDXIgAgNwgBAPAqAgByhRAAAEsIAMgdQgAAEACQU4QAAHlHAEBuEQIA5BkBALlGCACQVwQA5B4hAEAeEQAAEQIA5A8BALiIEAAgTwgAwAqEAAB5QQAALkEIAJAHBABgFYQAAFlHAADWQAgAkGUEAGAdhAAAWUUAAC6DEAAgiwquC0BjRVaaXrSaL0vli6N7ITDaVJDam4xC47jAlFoOAZL0zKnIcTWN8dzo0t/5wI1FBQ4+Fwtlq+mSVI6lxciqEEoFY9RWlFoLRuKzWjX6HysRADIuttLIVKzRWaszM7EmS5LWOqsz0uai1NsWqL/NaKA9cDLwpxUhoL6vNVe2OjllNTprNT5jtRCtvfwQGqlrk1Ffu9GOtkBdLXxQV0P/Yz0EgIyaLVsdOhvr6AWrxXUG0tew0uSiNLkY6+UJqSmMNdhpdE1PsHTGlXOxlYYvxBpol/rbjEZn8rE+Xu8QcGbG6tC5WCMzsWyFb2lkpfE5q/E5q4NjsTqbjPZ0BxrawqQl0f+oDAEgY0qx1YGxWIcn4pqv3y5GVofOWb00EevqrkD7ekMVc7hrxEp65UKs74zFmistvanXbg0kxYSAGpxfsPrmaKSx2drfwwuLVs+NRnrhbKwbtwXauTnI5RUC+h/VIABkyOh0rGdGYs2Xk52UYisdOhfr2JTVm7eH6m/Lz9A6V7J6ZiTS6UsmeiNCwEZZSQfGIn13PF5zNXqj5kpWXzsZ6chErFsGQrUU8/NZpf9RLfJcBiwPqE+eiBJv/pXmSlZPHi/r4FjyA3canZ6xeuTI6yf/ZcshIE8DYq13ByxEVo+/UtYLdZj8Vzo9u3TsklhdSDv6HxtFAPCctdI3TpV1cDxee3NPoi8oHRiP9OxIueLrtT46MRXrH4+X192IJhECqjFTsnrsaLlhk/JCZPXEsbJOTMUNeT0X6H/UggDgMSvp2dGyjlxofCcOn7f6+kiUyTOBU9OxnjoRVTzBEQIubyGyevJYWZOL9a3rUrGVnjoZ6eRk9kIA/Y9aEQA8dnAs0vB5dy149EKsF8ayNbCenbN66mT1AxshYG1RLD15LNJUgyf/ZdZKT49EmpjP1nRF/6NWBABPnZm1euGs++Y7cDbKzCa4xcjq6VNlRRt8WwkBq/vmafeTbxRL/3QiqvyWuJSj/5EEAoCHSrH09MkoHdfgrPT1kUgl92NRzb51JtZMjWephIDXOjUda/h8Oj4cMyWrb5/2/wFO9D+SQgDw0PNj9d3tW625ktXBMb8H1rFZq6MJTVSEgCVRLP1zyibcIxesxj2/M4D+R1IIAJ6ZLVu9PJG+uP3SxKsPyfHR82PJbmgiBEjD52NNO7ruvxarpWPtK/ofSSIAeObFs7U/4aselh8W4qPxOVuXW9PyHAIiK72Y0s/DmVl/VwHofySJAOCR2ErHJlPY/RcduWBTOThdTj2vUec1BPzRc4uaWUzvh+HIBf9WAeh/JI0A4JGRqVgLKbr2d6nFyGp02q+zgCiWTtT5HvE8hoCD47EOjFf+5T6NdnzSyrcbAuh/JI0A4JERD5YtRzy7JWh8zjZkB3MeQ8CZWZvaEFCK5d1lAPofSSMAeGRsJv3p+sxs+mtcqZH1EgLSZWzOr88q/Y+kEQA8EcXSZMl1FZc3tSivllbPLzT29QgB6dHoY18L+h/1QADwxHTJNubLPmpk7cVaPTG12PgzFkJAOkwv+HO2Sv+jHggAnpj3aNPyggdnKssWym4mYUKAe/OOjv1G0P+oBwKAJ8oerauVPboXyGWthAC3Sj59Tul/1AEBAHCIEADAFQKAJwqhPxNEIaDWahAC3Cim4NhXiv5HPRAAPLEpdF1B5ZqLriuoXHMhHaehhIDG25SSY18J+h/1QADwRHuTkfFgbjBGai96UOhFHU3paQFCQGO1N6fn2F8O/Y968KcDci40UocHyXpz01KtvtjS7LqC1yIENE7ajv166H/UAwHAI9va0n+4elvTX+NKaXxPCQGNsa0lfcd+PWn8rF7Kt/7PO46WR/o8mBC2t6e/xpW2bjIqprALCAH1VQyMtrb69d7S/0haCoc+rGWgPVBzIb0N1hQa9XtwlrJSGEg7NqfzPV0OATdu8+s9rUWjQsCVmyXfNqvT/0gaR8sjgZF2pXSykqTBTuPdoCpJu7ekd4t1W1H6wE1NumUgvTUmrREhYCjFx3wt9D+SRgDwzN6eIJVNFhhpb7efH6etLUa9KV0OvrYnVBhI77++SAhISF+rUU9LOo/35dD/SBJHzDOtBaOru9J32K7pDtTi8e0/N2wLlbbqO5qkwS1LxzowhIBEmKVj7Sv6H0lK3ycJl7WvN0xVs7UWjPb1+juoSkurAFd1puc9laQf6C+85myPEFC7oc5A3Z6e/S+j/5EUAoCHioF0y/YwHQ8GMdKbBkKleG9SxW7qC9Xe5LqKJXu6Vr8DgBCwce1F6aY+/4c8+h9J8b8bcqqvzWhfj/tJ4PqtYWZuVWsKjd66o6DQcVf0tBjd3Lf2sSUEVC8MpFt3FLx6/v966H8kgQDgsWt7Aw1tcXcIh7YEunZrtj5C3ZuMbt3hbj9Ae1H6oSvCy270IgRUzhjpLQOhujxf+r8U/Y9acfQ8ZiTt7w81tKXxA9vQlkD7+7M5+Qy0B7r1irDhjzTtbJbuuKqgTRWupxICLi800tsGQl3Rkb2hjv5HrbLXFTljjLR/e0HXbQ3ViNNWY6Tre0O9KS3XIOvkio5At+2sfDKuVV+r0Z27Cmqt8vUIAWtrKRjdtrOgHZuzO8zR/6hFdjsjR4ykfb2Bbr+yUNfdwa0Fo9t3FnKz7NfbanTPYFjXR7AGkq7bGuq2nQU1bXDJgRDwev1tRncNhql9vkOS6H9sVMF1AUhOX5vRvUMFHRyL9NJErDihW6dCI13dHWhfb/52+266OOi9MhnrO6djzZaTuym9v83o5r6CNifwrXTLIUCSnjkV1f4LPbAcAq7bGnz/bLS1aHRjb6CdnfmbpOh/VIsAkDHFYOl2tr3dgQ6di3V00mphg5NWc7h0b/xeHvKhXZsDXdkR6Mj5WC9NxLqwsLH3NJDU3xHojT2Btia8KS3PIeBtO0Lt7Ql0VWc6n5TXKPQ/qkEAyKiWotFNfaFu2CaNTscambE6MxtralFrLpsas/T0uW2tgba3L32xR54H00sFRtrdFWh3V6CJeauT07HOzFidm7eK4rV/rqVgtLXFqK/N6IrNRs113F2Y1xBwbMrqniE+r8vof1SCAJBxgZEGOgINdEhSqNhKU4vSQmRVjpZGgkK4NCl1NPn3DWmudG0y6toUSlslK2m2ZDVbksqxVdlKTYFRMZQ6ilKxwbcT5DEEPDe69Hc+cGORz/AK9D/WQwDImcAs3W62tHWIbk+CkdRWNGorLv+Xe4QAx8WkFP2PlfK3UwbIiTzeHfDcaKRPfruU2AY4IMsIAECGEQIArIUAAGQcIQDAaggAQA4QAgBcigAA5AQhAMBKBAAgRwgBAJYRAICcIQQAkAgAQC4RAgAQAICcIgQA+UYAAHKMEADkFwEAyDlCAJBPBAAAcuOH3wAAEkFJREFUhAAghwgAACQRAoC8IQAA+D5CAJAfBAAAr0EIAPKBAADgdQgBQPYRAACsihAAZBsBAMCaCAFAdhEAAKyLEABkU8F1AWisyErTi1bzZal8cXQrBEabClJ7k1FoHBfoIyvNlKTZslXZWpUj1wXVxzuvCjVbsnp+LHZdSkM8N7p0IB+4saggI31B/2MlAkDGxVYamYo1Omt1ZibWZEnSWmc1RtpclHrbAvW3GQ20B5kZ+JJ2bt7q5FSsMzNWE/NWUU7OFHtbjfrbjEZn8vEH+x4C6H+shwCQUbNlq0NnYx29YLVY6exkpclFaXIx1ssTUlMYa7DT6JqeQK0FRoLISkcuxDp8LtKFBdfVuGEkXbs1kBQTAlKM/kclCAAZU4qtDozFOjwR13z9cjGyOnTO6qWJWFd3BdrXG6qYw10jVtLR87G+MxZrvpyPSW89hADHxayD/kc1CAAZMjod65mR5Cep2EqHzsU6NmX15u2h+ttSPAImbLZs9bWTkcZm8zHRVYoQ4LiYVdD/qBZ5LgOspANjkZ48EdX1DHWuZPXk8bIOjsVrXkbMktOzVo8OM/mvZTkE5GlCSOPdAfQ/NooVAM9ZK31jpKwjFxrUklY6MB5pthxrf39BJqNj/7HJWM+cilI10KcRKwFua6H/UQtWADxmJT072sDmX2H4vNXXR6JMngmcmor1tZNM/pViJcAN+h+1IgB47OBYpOHz7lrw6IVYL2TsnvCzc1ZPnWRgqxYhoPHof9SKAOCpM7NWL5x133wHzkaZWfotRVZPnSzn5p7+pBECGof+RxIIAB4qxdLTJyPZNPSdlb4+Eqnkfiyq2TdPx5otua7Cb4SA+qP/kRQCgIeeH6vvbt9qzZWsDo75/fzbsVmrVy4wiiWBEFBf9D+SQgDwzGzZ6uWJ9E1UL03EmiulZ1Cq1vNjXPdPEiGgPuh/JIkA4JkXz9b+hK96WH5YiI/G5yz3+tcBISB59D+SRADwSGylY5Mp7P6LjlywqRycLmf4PANXvRACkkP/I2kEAI+MTMVaSNG1v0stRlaj035NplEsHefaf10RApJB/yNpBACPjHiwTD3i2S1B43NWKR5TM4MQUDv6H0kjAHhkbCb96frMbPprXMm3en1GCKgN/Y+kEQA8EcXSpAf3qE8tyqsH6Zyfd11BvhACNob+Rz0QADwxXbLy4T41ay/W6okpnmDScISA6tH/qAcCgCfmPXrOxoIHZyrLFsr5mYTShBBQHfof9UAA8ETZo3W1skf3AvlUa9YQAipH/6MeCAAAnCEEAO4QADxRCP0ZIAsBtaJyhIDLo/9RDwQAT2wKXVdQueai6woq11zgNCwNCAHro/9RDwQAT7Q3GRkPxkZjpPaiB4Ve1NFEC6QFIWBt9D/qgdHPE6GROjxI1publmr1xZZm1xVgJULA6uh/1AMBwCPb2tJ/uHpb01/jSj68p3lDCFidD59V3/o/7zhaHunzYEDc3p7+GlfausmoSBekDiHg9eh/JI2hzyMD7YGaC+ltsKbQqN+Ds5SVwkDasTm972meEQJei/5H0jhaHgmMtCvFk9Vgp5GPdwDt3uLRFuucIQS8iv5H0ggAntnbE6SyyQIj7e328+O0tcWotzWFbyokEQJWov+RJI6YZ1oLRld3pe+wXdMdqMXj239u2BbK3+qzjxCwhP5HktL3ScJl7esNU9VsrQWjfb1+L6NvbTHatSU97ylejxCwhP5HUggAHioG0i3bw3Q8GMRIbxoIleK9SRW7eVuotibXVWA9hAD6H8khAHiqr81oX4/71H391jAzg3FTaPTWgYJCuiLVCAH0P5LBUOexa3sDDW1xdwiHtgS6dmu2PkI9LUa37mA/QNoRAuh/1I6j5zEjaX9/qCEH166HtgTa3+/+DKQeBtoDvXVHmMrd1nhV3kMA/Y9aFVwXgNoYI+3fXlBrIdaBs5FU5y+3M0a6bmuY+eR/5eZAzaHRUycjLUR8Y2BaLYcAKdboTD6O03OjkSTpgRuLCuh/1ICjmAFG0r7eQLdfWajr7uDWgtHtOwu5af5tbUb3DIbaxjMCUo2VAPofG8ORzJC+NqN7hwra253sw0JCI72hJ9C9ewq5mwxbika37yroLQPpuvUKr7UcAq7oyM8xWm1jIP2PanAJIGOKgXRTX6i93YEOnYt1dNJqobyxdcHm0OiqTqO9OX/Ih5G0qzPQlZsDDZ+PdXgi1oWFfCw3+6Kz2eia7kD/Zm9Rf3agpGdORa5LaohLLwfQ/6gGASCjWopGN/WFumGbNDoda2TG6sxsrKlFya4xHhgjdTRJ21oDbW9f+mIPNsK9KjDSnq5Ae7oCTcxbnZyOdWbG6ty8VRS7ri5fwkDq3mTU1xpoR4fRlk2vflDff31RknIbAiT6H5UhAGRcYKSBjkADHZIUKrbS1KK0EFmVL25uK4RGzaFRR5No+Ap1bTLq2hRKW5f2Xc2WrGZLUjm2KhMG6qIQSIXAqLUotRbNmrdqBoYQsIz+x3oIADkTGKmzWVpa2Kbbk2AktRWN2orL/wXXCAGr/xv6HyuxCRBAJi2HgFsG8nO/+lrfIgishgAAILMIAcDaCAAAMo0QAKyOAAAg8wgBwOsRAADkAiEAeC0CAIDcIAQAryIAAMgVQgCwhAAAIHcIAQABAEBOEQKQdwQAALlFCECeEQAA5BohAHlFAACQe4QA5BEBAABECED+EAAA4CJCAPKEAAAAKxACkBcEAAC4BCEAeUAAAIBVEAKQdQQAAFgDIQBZRgAAgHUQApBV3gSAQOKjCMAJQgAq5dNc5U0AiK1mXdcAIL8IAaiECTTjuoZKeRMAAmOnXNcAIN8IAbicOPJnrvImANjATruuAQAIAViPMfGk6xoq5U0AiMqxN6kKQLYRArCWKPBnrvImAJj25hF5tLkCQLYRArCKeLFp02nXRVTKmwBwT7+ZsdJJ13UAwDJCAF7LHn/PgPFmw7o3AUCSjHTIdQ0AsBIhAK8yXs1RXgUA395cAPlACMASv+YorwKAMfF3XNcAAKshBMDKrznKqwAQ2PgJ1zUAwFoIAfkWRvHjrmuohnFdQLUeHS4dN9IVrusAgLXEVvr08yU9cypyXUrD/GB/qAduLCrwblZJij1211DTLtdVVMOrFQBJCmSfcF0DAKyHlYAcMsGXXZdQLe8CgGzwRdclAMDlEAJyxuoR1yVUy7sAELWFfy3JmyctAcgvQkBuTLYVw8+7LqJa3gWApQcC2f/jug4AqAQhIPuMzMO3XmnmXNdRLe8CgCTJms+6LgEAKkUIyLZI1ss5ycsA8NRQ4XFJ33NdBwBUihCQWS/ePVj4f66L2AgvA8BDxsSy9iOu6wCAahACssj8d2OMl3+dlwFAkromip81skdd1wEA1SAEZIkZLrwS/qXrKjbK2wCwf78pxdLvua4DAKpFCMgGY+KP3HGHKbuuY6O8DQCSdH6u+ElJL7quAwCqRQjwnNULW84WP+26jFp4HQDu22cWrdEHJGXh4wQgZwgB/jKhPrx/vym5rqMWXgcASbp7sPiktfZ/ua4DADaCEOAj+9l3XlX06ot/VuN9AJAkFYu/KOmc6zIAYCMIAV4ZL5jiL7suIgmZCAB37zSnZM1PiEsBADxFCPCCtTI/dcegGXVdSBIyEQAk6a7dhb+X0R+4rgMANooQkHJGH7l7qPC3rstISmYCgCR1nS38iqSvua4DADaKEJBaXy0cLfya6yKSZFwXkLTHD9mt5WL5q5L2uq4FADYqttKnny/pmVOR61Ia5gf7Qz1wY1FB6mYmcziOw7fds8eccV1JkjK1AiBJd+w143FQvlfSiOtaAGCjWAlIjVNlU7ora5O/lMEAIEn3XNVyJJK9V9J517UAwEYRAtwy0oRs/K57B1uOuq6lHjIZACTpXUNN347j+O2yOum6FgDYKEKAMyOxsXfetbv5eadV1FFmA4Ak3bOn+UA5KP+Q+OpgAB4jBDSYMS8HUfT2uwebvuXg1Rsm0wFAku4dbDkax4W3i7sDAHiMENAwXy0shm95x9WbXm7oqzqQ+QAgSffsMWcKrxTeLqvflBS7rgcANoIQUFfWSh/tOle48469Zrzur5YCqbvZot4eGS6/J5D9jKRu17UAwEZwi2Dixq01//7u3YUv1OW3p1QuVgBWumeo8PkoKFwn2c+KRwcD8BArAYn6u0JUuDlvk7+UwxWAlR49UrrNxPq4jK51XQsAVIuVgJp8z0gffudQ8UsJlOWl3K0ArHT3YPHJifnCzcbaD0n2Fdf1AEA1WAnYCDNsjP2ZrnOF6/I8+Us5XwFY6dlnbXGiO3qvZH9V0htc1wMAlWIloALGvGwU/054tPind9xhynUtzhMEgEs8ZG3wtuHyrTLmfsn+W0mbXdcEAJdDCFjVpGT/xljz5+8YKnzFGMO+rxUIAOt46rhtmS1H/zq28buMdKdkrnRdEwCshRAgSfYVmeAxWX2xrRh+/tYrzZzL+tKMAFCFLx6e3xMEwe2Bgpti2WuM7N6LoYD3EUAq5DEE7O4KDv/nNxV/p2jjx/LwAJ+kMHHV6POnbGtLaaHf2qDTxKbdBKY9itXuui4A+bUQK/jtp+Y+NDqtt7uupYH+ateZ9vc98RDX9ytFAACALHrYhoPjU5+RzI+7LqWBCAFVIAAAQFYRArAOAgAAZBkhAGsgAABA1hECsAoCAADkASEAlyAAAEBeEAKwAgEAAPKEEICLCAAAkDeEAIgAAAD5RAjIPQIAAOQVISDXCAAAkGeEgNwiAABA3hECcokAAAAgBOQQAQAAsIQQkCsEAADAqwgBuUEAAAC8FiEgFwgAAIDXIwRkHgEAALA6QkCmEQAAAGsjBGQWAQAAsD5CQCYRAAAAl0cIyBwCAACgMoSATCEAAAAqRwjIDAIAAKA6hIBMIAAAAKpHCPAeAQAAsDGEAK8RAAAAG/ewDa86O/1ZY/Ve16U0ijX63NGe9vt1n4lc11KLwHUBAACP3Weioz3t90v2L1yX0ijG6r2D41OflrVen0QTAAAAtbnPREe2dvykNfqc61Iax9x/1R9P/5rrKmrhdXoBAKRI/vYExArMu458oP1LrgvZCAIAACA5+dsTcCosL77x8IM9k64LqRaXAAAAycnfnoCBqFD08lIAKwAAgOTlayVgMSyHuw8/2HrCdSHVYAUAAJC8fK0ENEWF8s+7LqJarAAAAOonPxsDJ8Jy+/bDD5oF14VUihUAAED95OcWwa6oMHWP6yKqQQAAANRXTi4HGJl7XddQDQIAAKD+crASYKXbXNdQDQIAAKAxsr8SsPeK/2FbXBdRKQIAAKBxsr0SEDS3TO92XUSlCAAAgMbK8EqAjUyf6xoqRQAAADTexZWArIWAOIg7XNdQKQIAAMCNjIYAXxAAAADuZCwEBHEw5bqGShEAAABuZWhjoAntadc1VIoAAABwLxsbA+OFufaXXRdRKQIAACAdPF8JMNKLJ37BzLmuo1IEAABAeni8EhBLT7quoRoEAABAuni6EhAY+wXXNVSDAAAASB//VgImWno6HnVdRDUIAACAdPLqFkHzqYP3mUXXVVSDAAAASC8/LgcslEzwP10XUS0CAAAg3VJ+OcDI/MGJD7aedF1HtQgAAID0S+lKgJFOFpvn/pvrOjaCAAAA8EP6VgJiyfzkoZ/q9ebxvysRAAAA/kjXSsBvDP+n9i+7LmKjjOsCAACo2sM2HByf+oxkftzJ6xt98sgHO/6jk9dOCCsAAAD/fP8WQX2q4a9t9MkjPe0fbPjrJowVAACA1676+NSvG+k3VP+T2khWv3HkQx1ebvq7FAEAAOC93X88dae1+nMr7ajH7zfSycjq/lc+1PF4PX6/C1wCAAB47+UPdjxWbJ5/o2R+V1KST+RbMDIfabFzb8jS5C+xAgAAyJgr/nh2R9GWf04y/0FS9wZ/zTnJ/mk5Cn//+M+2nUqyvrQgAAAAMmnfw7Zp7uzU3bE17w6k26z0Bq298h1b6bvG6Ekj+w8tPR2P+vZs/2oRAAAAubDno7Z5sWl6dyE2A3Ect0lSEAQzkbUni1H78OEHzYLrGgEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAefb/AT8dOLOuMoTgAAAAAElFTkSuQmCC
        """
        icon_bytes = base64.b64decode(icon_base64)
        pixmap = QPixmap()
        pixmap.loadFromData(icon_bytes)
        return QIcon(pixmap)

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
