# demo/webrtc_app.py (ALICI KAMERASI AKTİF HALİ)

import sys
import os
import datetime
import socket

# ==================== AYAR ====================
SIGNALING_SERVER_IP = 'auto'
# ==============================================

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineDownloadItem, QWebEngineSettings
from PyQt5.QtCore import QUrl

os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = "9223"
SAVE_DIR = os.path.abspath("./recordings")
os.makedirs(SAVE_DIR, exist_ok=True)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


class WebRTCWindow(QMainWindow):
    def __init__(self, mode, signaling_ip):
        super().__init__()
        self.mode = mode
        self.signaling_ip = signaling_ip
        self.view = QWebEngineView()

        self.view.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        self.view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        # Her iki mod için de kamera iznini bağlıyoruz.
        self.view.page().featurePermissionRequested.connect(self.on_feature_permission)

        if self.mode == "receiver":
            html_path = os.path.abspath("receiver.html")
            self.setWindowTitle("Alıcı (Receiver)")
            self.view.page().profile().downloadRequested.connect(self.on_download_requested)
        else:  # sender
            html_path = os.path.abspath("sender.html")
            self.setWindowTitle("Gönderici (Sender)")

        self.load_html_with_ip(html_path)

        self.setCentralWidget(self.view)
        self.resize(900, 700)

    def load_html_with_ip(self, html_path):
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            html_content = html_content.replace('SIGNALING_SERVER_IP', self.signaling_ip)

            base_url = QUrl.fromLocalFile(os.path.dirname(html_path) + os.path.sep)
            self.view.setHtml(html_content, baseUrl=base_url)

        except FileNotFoundError:
            self.view.setHtml(f"<h2>Hata</h2><p>HTML dosyası bulunamadı: {html_path}</p>")

    def on_feature_permission(self, url, feature):
        allowed_features = {
            QWebEnginePage.MediaAudioCapture,
            QWebEnginePage.MediaVideoCapture,
            QWebEnginePage.MediaAudioVideoCapture,
        }
        if feature in allowed_features:
            self.view.page().setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)

    def on_download_requested(self, download: QWebEngineDownloadItem):
        base_name = os.path.basename(download.path()) or "remote_stream.webm"
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(base_name)
        if not ext: ext = ".webm"
        final_name = os.path.join(SAVE_DIR, f"{name}_{stamp}{ext}")

        download.setPath(final_name)
        download.accept()
        download.finished.connect(lambda: print(f"[OK] Kayıt tamamlandı: {final_name}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    server_ip = SIGNALING_SERVER_IP
    if server_ip == 'auto':
        server_ip = get_local_ip()

    print(f"Sinyal Sunucusu için kullanılacak IP Adresi: {server_ip}")

    sender_win = WebRTCWindow(mode="sender", signaling_ip=server_ip)
    receiver_win = WebRTCWindow(mode="receiver", signaling_ip=server_ip)

    sender_win.show()
    receiver_win.show()

    app_geometry = QApplication.desktop().availableGeometry()
    sender_win.move(app_geometry.left() + 50, app_geometry.top() + 100)
    receiver_win.move(sender_win.geometry().right() + 20, app_geometry.top() + 100)

    sys.exit(app.exec_())