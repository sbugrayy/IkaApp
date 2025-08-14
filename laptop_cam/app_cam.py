import sys
import os
import datetime
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineDownloadItem
from PyQt5.QtWebEngineWidgets import QWebEnginePage

HTML_PATH = os.path.abspath("webrtc_recorder_cam.html")
SAVE_DIR  = os.path.abspath("../recordings")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        os.makedirs(SAVE_DIR, exist_ok=True)

        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        # Kamera/mikrofon izinlerini otomatik onayla
        self.view.page().featurePermissionRequested.connect(self.on_feature_permission)

        # İndirme olayını yakala
        profile = self.view.page().profile()  # QWebEngineProfile
        profile.downloadRequested.connect(self.on_download_requested)

        self.view.load(QUrl.fromLocalFile(HTML_PATH))
        self.setWindowTitle("WebRTC Kayıt - PyQt5")
        self.resize(900, 700)

    def on_feature_permission(self, url, feature):
        # Medya izinlerini otomatik ver
        allowed_features = {
            QWebEnginePage.MediaAudioCapture,
            QWebEnginePage.MediaVideoCapture,
            QWebEnginePage.MediaAudioVideoCapture,
            QWebEnginePage.DesktopVideoCapture,
            QWebEnginePage.DesktopAudioVideoCapture,
        }
        if feature in allowed_features:
            self.view.page().setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
        else:
            self.view.page().setFeaturePermission(url, feature, QWebEnginePage.PermissionDeniedByUser)

    def on_download_requested(self, download: QWebEngineDownloadItem):
        """
        HTML tarafında <a download> ile tetiklenen Blob indirmesini yakalar.
        Burada kaydedilecek dosya adını/konumunu belirleyip indirmeyi başlatıyoruz.
        """
        # Dosya uzantısını mevcut öneriden veya mime tipten çıkar
        suggested_path = download.path()  # ör: webrtc_recording.webm
        base_name = os.path.basename(suggested_path) if suggested_path else "webrtc_recording.webm"

        # Zaman damgalı dosya adı
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(base_name)
        if not ext:
            # webm varsayılan
            ext = ".webm"

        final_name = f"{name}_{stamp}{ext}"
        final_path = os.path.join(SAVE_DIR, final_name)

        download.setPath(final_path)
        download.accept()

        # Opsiyonel: durum takibi (log)
        download.finished.connect(lambda: print(f"[OK] Kayıt tamamlandı → {final_path}"))
        download.stateChanged.connect(lambda s: print(f"[DL] State: {s}"))
        download.downloadProgress.connect(lambda rcv, tot: print(f"[DL] {rcv}/{tot} bytes"))

def main():
    app = QApplication(sys.argv)

    # Güvenlik: Mikrofon/kamera vb. izinler için kullanıcıdan onay istemeden çalışmak istiyorsanız,
    # yukarıda on_feature_permission içinde otomatik grant veriyoruz.

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
