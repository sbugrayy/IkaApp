# demo/main_app.py

import sys
import os
import datetime
import socket
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineDownloadItem, QWebEngineSettings
from PyQt5.QtCore import QUrl

# ==================== AYARLAR ====================
# Sinyal sunucusunun IP adresini otomatik al veya elle gir.
# Başka bir bilgisayara bağlanacaksanız, sunucuyu çalıştıran
# bilgisayarın IP adresini buraya yazın. Örn: '192.168.1.42'
SIGNALING_SERVER_IP = 'auto'
SAVE_DIR = os.path.abspath("./recordings")
# ================================================

os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = "9223"
os.makedirs(SAVE_DIR, exist_ok=True)


def get_local_ip():
    """Yerel IP adresini bulan yardımcı fonksiyon."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


class MainWindow(QMainWindow):
    def __init__(self, signaling_ip):
        super().__init__()
        self.signaling_ip = signaling_ip
        self.setWindowTitle("WebRTC Görüntü Aktarımı")
        self.resize(900, 750)

        # Ana layout ve widget'lar
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)

        # Butonlar için yatay layout
        self.button_layout = QHBoxLayout()
        self.sender_btn = QPushButton("Gönderici Olarak Başlat")
        self.receiver_btn = QPushButton("Alıcı Olarak Başlat")
        self.button_layout.addWidget(self.sender_btn)
        self.button_layout.addWidget(self.receiver_btn)

        # Web view (HTML içeriği burada gösterilecek)
        self.view = QWebEngineView()
        self.view.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        self.view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        # Layout'a widget'ları ekle
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.view)
        self.setCentralWidget(self.central_widget)

        # Sinyalleri (buton tıklamalarını) slotlara (fonksiyonlara) bağla
        self.sender_btn.clicked.connect(lambda: self.load_mode("sender"))
        self.receiver_btn.clicked.connect(lambda: self.load_mode("receiver"))

        # Gerekli izin ve indirme yöneticilerini bağla
        self.view.page().featurePermissionRequested.connect(self.on_feature_permission)
        self.view.page().profile().downloadRequested.connect(self.on_download_requested)

    def load_mode(self, mode):
        """Seçilen moda göre ilgili HTML dosyasını yükler."""
        if mode == "sender":
            html_path = os.path.abspath("sender.html")
            self.setWindowTitle("WebRTC - Gönderici")
        elif mode == "receiver":
            html_path = os.path.abspath("receiver.html")
            self.setWindowTitle("WebRTC - Alıcı")
        else:
            return

        self.load_html_with_ip(html_path)
        # Mod seçildikten sonra butonları pasif yap
        self.sender_btn.setEnabled(False)
        self.receiver_btn.setEnabled(False)

    def load_html_with_ip(self, html_path):
        """HTML dosyasını okur, sinyal sunucusu IP'sini içine yazar ve yükler."""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # IP adresini HTML içeriğindeki yer tutucu ile değiştir
            html_content = html_content.replace('SIGNALING_SERVER_IP', self.signaling_ip)

            # HTML'i yerel dosya yolunu baz alarak yükle (CSS/JS dosyaları için önemli)
            base_url = QUrl.fromLocalFile(os.path.dirname(html_path) + os.path.sep)
            self.view.setHtml(html_content, baseUrl=base_url)
            print(f"'{os.path.basename(html_path)}' yüklendi. Sinyal sunucusu: {self.signaling_ip}")

        except FileNotFoundError:
            self.view.setHtml(f"<h2>Hata</h2><p>HTML dosyası bulunamadı: {html_path}</p>")

    def on_feature_permission(self, url, feature):
        """Kamera ve mikrofon gibi medya izinlerini otomatik olarak verir."""
        allowed_features = {
            QWebEnginePage.MediaAudioCapture,
            QWebEnginePage.MediaVideoCapture,
            QWebEnginePage.MediaAudioVideoCapture,
        }
        if feature in allowed_features:
            self.view.page().setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)

    def on_download_requested(self, download: QWebEngineDownloadItem):
        """HTML tarafından tetiklenen video kaydı indirmesini yakalar ve dosyayı kaydeder."""
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

    server_ip = SIGNALING_SERVER_IP
    if server_ip == 'auto':
        server_ip = get_local_ip()

    print(f"Sinyal Sunucusu için kullanılacak IP Adresi: {server_ip}")

    win = MainWindow(signaling_ip=server_ip)
    win.show()

    sys.exit(app.exec_())