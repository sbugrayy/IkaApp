import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineDownloadItem, QWebEngineSettings
from PyQt5.QtCore import QUrl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(os.path.dirname(BASE_DIR), "recordings")
os.makedirs(SAVE_DIR, exist_ok=True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebRTC Görüntü Aktarımı")
        self.resize(900, 750)

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.button_layout = QHBoxLayout()
        self.sender_btn = QPushButton("Gönderici Olarak Başlat")
        self.receiver_btn = QPushButton("Alıcı Olarak Başlat")
        self.button_layout.addWidget(self.sender_btn)
        self.button_layout.addWidget(self.receiver_btn)
        self.view = QWebEngineView()
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.view)
        self.setCentralWidget(self.central_widget)

        self.sender_btn.clicked.connect(lambda: self.load_mode("sender"))
        self.receiver_btn.clicked.connect(lambda: self.load_mode("receiver"))
        self.view.page().featurePermissionRequested.connect(self.on_feature_permission)
        self.view.page().profile().downloadRequested.connect(self.on_download_requested)

    def load_mode(self, mode):
        if mode == "sender":
            html_path = os.path.join(BASE_DIR, "sender.html")
        else:  # receiver
            html_path = os.path.join(BASE_DIR, "receiver.html")

        self.view.load(QUrl.fromLocalFile(html_path))
        self.sender_btn.setEnabled(False)
        self.receiver_btn.setEnabled(False)

    def on_feature_permission(self, url, feature):
        if feature in {QWebEnginePage.MediaAudioCapture, QWebEnginePage.MediaVideoCapture,
                       QWebEnginePage.MediaAudioVideoCapture}:
            self.view.page().setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)

    def on_download_requested(self, download: QWebEngineDownloadItem):
        final_name = os.path.join(SAVE_DIR, "kayit.webm")  # Basit bir isim verelim
        download.setPath(final_name)
        download.accept()
        download.finished.connect(lambda: print(f"Kayıt tamamlandı: {final_name}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())