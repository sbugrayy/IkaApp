import sys, os, datetime, tempfile

# ---------- GPU ve cache ayarları ------------
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QUrl

# Kayıt dizini
SAVE_DIR = os.path.abspath("./recordings")
os.makedirs(SAVE_DIR, exist_ok=True)

# Cache dizini
temp_dir = os.path.join(tempfile.gettempdir(), "QtWebEngineCache")
os.makedirs(temp_dir, exist_ok=True)
profile = QWebEngineProfile.defaultProfile()
profile.setCachePath(temp_dir)
profile.setPersistentStoragePath(temp_dir)
# -------------------------------------------

class ModeSelectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebRTC Mod Seçimi")
        self.resize(300,150)

        layout = QVBoxLayout()
        btn_sender = QPushButton("Gönderici (Sender)")
        btn_receiver = QPushButton("Alıcı (Receiver)")

        btn_sender.clicked.connect(self.start_sender)
        btn_receiver.clicked.connect(self.start_receiver)

        layout.addWidget(btn_sender)
        layout.addWidget(btn_receiver)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_sender(self):
        self.hide()
        self.sender_win = WebRTCWindow(mode="sender")
        self.sender_win.show()

    def start_receiver(self):
        self.hide()
        self.receiver_win = WebRTCWindow(mode="receiver")
        self.receiver_win.show()

class WebRTCWindow(QMainWindow):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        if self.mode=="receiver":
            self.view.page().downloadRequested.connect(self.on_download_requested)
            html_path = os.path.abspath("receiver.html")
            self.setWindowTitle("Alıcı (Receiver)")
        else:
            html_path = os.path.abspath("sender.html")
            self.setWindowTitle("Gönderici (Sender)")

        if not os.path.exists(html_path):
            QMessageBox.critical(self, "Hata", f"{html_path} bulunamadı!")
        else:
            self.view.load(QUrl.fromLocalFile(html_path))

        self.resize(900,700)

    def on_download_requested(self, download):
        # download: otomatik olarak doğru QWebEngineDownloadItem objesi
        base_name = os.path.basename(download.path()) or "remote_stream.webm"
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(base_name)
        if not ext: ext = ".webm"
        final_name = os.path.join(SAVE_DIR, f"{name}_{stamp}{ext}")
        download.setPath(final_name)
        download.accept()
        download.finished.connect(lambda: print(f"Kayıt tamamlandı: {final_name}"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ModeSelectionWindow()
    win.show()
    sys.exit(app.exec())
