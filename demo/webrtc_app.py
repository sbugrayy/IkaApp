import sys
import os
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineDownloadItem, QWebEngineSettings
from PyQt5.QtCore import QUrl

# ==================== AYARLAR ====================
# Tarafsız, herkese açık bir sinyal sunucusu kullanacağız. ngrok'a gerek kalmadı.
# Bu sunucu WebRTC örnekleri için yaygın olarak kullanılır.
PUBLIC_SIGNALING_SERVER = '53eb26a886c6.ngrok-free.app'
SAVE_DIR = os.path.abspath("./recordings")
# ================================================

# Bu satır, betiğin çalıştığı klasörün yolunu alır.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = "9223"
os.makedirs(SAVE_DIR, exist_ok=True)


class MainWindow(QMainWindow):
    def __init__(self, signaling_server_url):
        super().__init__()
        self.signaling_server_url = signaling_server_url
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
        self.view.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        self.view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
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
            self.setWindowTitle("WebRTC - Gönderici")
        elif mode == "receiver":
            html_path = os.path.join(BASE_DIR, "receiver.html")
            self.setWindowTitle("WebRTC - Alıcı")
        else:
            return
        self.load_html_with_server_url(html_path)
        self.sender_btn.setEnabled(False)
        self.receiver_btn.setEnabled(False)

    def load_html_with_server_url(self, html_path):
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # HTML'deki WebSocket adresini herkese açık sunucu adresiyle değiştiriyoruz.
            html_content = html_content.replace('ws://SIGNALING_SERVER_IP:8765', self.signaling_server_url)

            base_url = QUrl.fromLocalFile(os.path.dirname(html_path) + os.path.sep)
            self.view.setHtml(html_content, baseUrl=base_url)
            print(f"'{os.path.basename(html_path)}' yüklendi. Sinyal sunucusu: {self.signaling_server_url}")
        except FileNotFoundError:
            self.view.setHtml(f"<h2>Hata</h2><p>HTML dosyası bulunamadı: {html_path}</p>")

    def on_feature_permission(self, url, feature):
        allowed_features = {
            QWebEnginePage.MediaAudioCapture, QWebEnginePage.MediaVideoCapture, QWebEnginePage.MediaAudioVideoCapture,
        }
        if feature in allowed_features:
            self.view.page().setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)

    def on_download_requested(self, download: QWebEngineDownloadItem):
        base_name = os.path.basename(download.path()) or "remote_stream.webm"
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(base_name)
        if not ext: ext = ".webm"
        final_name = os.path.join(SAVE_DIR, f"{name}_{stamp}{ext}")
        print(f"Kayıt talebi alındı. Dosya kaydediliyor: {final_name}")
        download.setPath(final_name)
        download.accept()
        download.finished.connect(lambda: print(f"[OK] Kayıt tamamlandı: {final_name}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow(signaling_server_url=PUBLIC_SIGNALING_SERVER)
    win.show()
    sys.exit(app.exec_())