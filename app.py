import sys, os, datetime
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtCore import QUrl

SAVE_DIR = os.path.abspath("./recordings")
os.makedirs(SAVE_DIR, exist_ok=True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        # HTML indirme olayını yakala
        self.view.page().profile().downloadRequested.connect(self.on_download_requested)

        html_path = os.path.abspath("server.py/webrtc_remote_recorder.html")
        self.view.load(QUrl.fromLocalFile(html_path))

        self.setWindowTitle("WebRTC Remote Stream Kayıt")
        self.resize(900, 700)

    def on_download_requested(self, download: QWebEngineDownloadItem):
        base_name = os.path.basename(download.path()) or "remote_stream.webm"
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(base_name)
        if not ext:
            ext = ".webm"
        final_name = f"{name}_{stamp}{ext}"
        final_path = os.path.join(SAVE_DIR, final_name)

        download.setPath(final_path)
        download.accept()
        download.finished.connect(lambda: print(f"[OK] Kayıt tamamlandı: {final_path}"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())