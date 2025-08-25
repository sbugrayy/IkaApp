import sys
import os
import cv2
import tempfile
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QComboBox, QLabel,
                           QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings

class CameraPreviewThread(QThread):
    frame_ready = pyqtSignal(QImage, int)

    def __init__(self, camera_id, index):
        super().__init__()
        self.camera_id = camera_id
        self.index = index
        self.running = True

    def run(self):
        cap = None
        backends = [None, cv2.CAP_DSHOW, cv2.CAP_MSMF]
        
        # Farklı backend'leri dene
        for backend in backends:
            try:
                if backend:
                    cap = cv2.VideoCapture(self.camera_id + backend)
                else:
                    cap = cv2.VideoCapture(self.camera_id)
                    
                if cap.isOpened():
                    print(f"Kamera {self.camera_id} başarıyla açıldı")
                    break
                else:
                    cap.release()
                    cap = None
            except Exception as e:
                print(f"Backend hatası: {e}")
                if cap:
                    cap.release()
                    cap = None
        
        if not cap or not cap.isOpened():
            print(f"Kamera {self.camera_id} açılamadı!")
            return
            
        try:
            while self.running:
                ret, frame = cap.read()
                if ret:
                    try:
                        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_image.shape
                        bytes_per_line = ch * w
                        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                        self.frame_ready.emit(qt_image, self.index)
                    except Exception as e:
                        print(f"Görüntü işleme hatası: {e}")
                        break
                else:
                    print("Kameradan görüntü alınamadı")
                    break
        except Exception as e:
            print(f"Kamera okuma hatası: {e}")
        finally:
            if cap:
                cap.release()

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self, is_sender=True):
        super().__init__()
        self.is_sender = is_sender
        self.camera_threads = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Çoklu Kamera Agora" + (" - Gönderici" if self.is_sender else " - Alıcı"))
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Agora kimlik bilgileri
        creds_layout = QHBoxLayout()
        
        self.app_id_input = QLineEdit()
        self.app_id_input.setPlaceholderText("Agora App ID")
        creds_layout.addWidget(self.app_id_input)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Agora Token")
        creds_layout.addWidget(self.token_input)

        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Kanal Adı")
        self.channel_input.setText("test_channel")
        creds_layout.addWidget(self.channel_input)

        layout.addLayout(creds_layout)

        # Kamera kontrolleri (sadece gönderici için)
        if self.is_sender:
            camera_controls = QHBoxLayout()
            self.camera_combos = []
            for i in range(3):
                combo = QComboBox()
                combo.addItems(self.get_available_cameras())
                camera_controls.addWidget(combo)
                self.camera_combos.append(combo)
            layout.addLayout(camera_controls)

            # Kamera önizleme alanı
            preview_layout = QHBoxLayout()
            self.preview_labels = []
            for i in range(3):
                label = QLabel()
                label.setFixedSize(380, 285)
                label.setStyleSheet("border: 1px solid black;")
                preview_layout.addWidget(label)
                self.preview_labels.append(label)
            layout.addLayout(preview_layout)

        # WebView alanı
        self.web_view = QWebEngineView()
        profile = QWebEngineProfile.defaultProfile()
        settings = self.web_view.settings()
        
        # WebRTC ve kamera izinleri
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        
        layout.addWidget(self.web_view)

        # Kontrol düğmeleri
        control_layout = QHBoxLayout()
        
        if self.is_sender:
            self.preview_button = QPushButton("Kamera Önizleme")
            self.preview_button.clicked.connect(self.toggle_camera_preview)
            control_layout.addWidget(self.preview_button)

        self.start_button = QPushButton("Yayını Başlat")
        self.start_button.clicked.connect(self.start_stream)
        control_layout.addWidget(self.start_button)

        layout.addLayout(control_layout)

        # HTML içeriğini oluştur ve yükle
        self.create_and_load_html()

    def get_available_cameras(self):
        def try_camera(index, backend=None):
            try:
                if backend:
                    cap = cv2.VideoCapture(index + backend)
                else:
                    cap = cv2.VideoCapture(index)
                
                if cap.isOpened():
                    # Kamera bilgilerini al
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    name = f"Kamera {index} ({int(width)}x{int(height)})"
                    cap.release()
                    return name
                cap.release()
            except Exception as e:
                print(f"Kamera {index} kontrol hatası: {e}")
            return None

        camera_list = []
        
        # Farklı backend'leri dene
        backends = [None, cv2.CAP_DSHOW, cv2.CAP_MSMF]
        
        for i in range(5):  # 5 kameraya kadar kontrol et
            for backend in backends:
                name = try_camera(i, backend)
                if name and name not in camera_list:
                    camera_list.append(name)
                    break  # Bu kamera için diğer backend'leri deneme
        
        if not camera_list:
            print("Hiç kamera bulunamadı!")
            camera_list.append("Kamera 0")
            
        return camera_list

    def toggle_camera_preview(self):
        try:
            if not hasattr(self, 'preview_active') or not self.preview_active:
                # Önizlemeyi başlat
                self.preview_active = True
                self.preview_button.setText("Önizlemeyi Durdur")
                
                for i, combo in enumerate(self.camera_combos):
                    try:
                        camera_text = combo.currentText()
                        # Parantez içindeki çözünürlük bilgisini kaldır
                        camera_id = int(camera_text.split()[1].split('(')[0])
                        thread = CameraPreviewThread(camera_id, i)
                        thread.frame_ready.connect(self.update_preview)
                        thread.start()
                        self.camera_threads.append(thread)
                    except Exception as e:
                        print(f"Kamera {i} başlatma hatası: {e}")
            else:
                # Önizlemeyi durdur
                self.preview_active = False
                self.preview_button.setText("Kamera Önizleme")
                
                for thread in self.camera_threads:
                    try:
                        thread.stop()
                    except Exception as e:
                        print(f"Thread durdurma hatası: {e}")
                self.camera_threads.clear()
                
                # Önizleme etiketlerini temizle
                for label in self.preview_labels:
                    label.clear()
        except Exception as e:
            print(f"Kamera önizleme hatası: {e}")
            self.preview_active = False
            self.preview_button.setText("Kamera Önizleme")
            for thread in self.camera_threads:
                try:
                    thread.stop()
                except:
                    pass
            self.camera_threads.clear()

    def update_preview(self, image, index):
        scaled_image = image.scaled(380, 285, Qt.AspectRatioMode.KeepAspectRatio)
        self.preview_labels[index].setPixmap(QPixmap.fromImage(scaled_image))

    def create_and_load_html(self):
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agora Multi-Camera</title>
    <script src="https://download.agora.io/sdk/release/AgoraRTC_N.js">
    <style>
        .video-container { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 10px; 
            justify-content: center; 
        }
        .video-item { 
            width: 320px; 
            height: 240px; 
            background: #000; 
            margin: 5px; 
        }
    </style>
</head>
<body>
    <div class="video-container" id="videos">
        <!-- Video elementleri dinamik olarak eklenecek -->
    </div>

    <script>
        let rtc = {
            client: null,
            localAudioTrack: null,
            localVideoTracks: [],
            remoteUsers: {}
        };

        let options = {
            appId: null,
            token: null,
            channel: null,
            uid: null
        };

        async function startStream(appId, token, channel, cameraCount = 1, isSender = true) {
            try {
                options.appId = appId;
                options.token = token;
                options.channel = channel;
                
                rtc.client = AgoraRTC.createClient({ 
                    mode: "rtc", 
                    codec: "vp8",
                    role: isSender ? "host" : "audience"
                });
                
                // Hata yakalama
                rtc.client.on("error", (err) => {
                    console.error("Agora istemci hatası:", err);
                });
                
                rtc.client.on("connection-state-change", (curState, prevState) => {
                    console.log(`Bağlantı durumu: ${prevState} -> ${curState}`);
                });

                rtc.client.on("user-published", async (user, mediaType) => {
                    try {
                        await rtc.client.subscribe(user, mediaType);
                        console.log("Kullanıcıya abone olundu:", user.uid, mediaType);
                        
                        if (mediaType === "video") {
                            const playerContainer = document.createElement("div");
                            playerContainer.id = user.uid;
                            playerContainer.className = "video-item";
                            document.getElementById("videos").append(playerContainer);
                            user.videoTrack.play(playerContainer.id);
                        }
                        if (mediaType === "audio") {
                            user.audioTrack.play();
                        }
                    } catch (err) {
                        console.error("Abone olma hatası:", err);
                    }
                });

                rtc.client.on("user-unpublished", (user) => {
                    const playerContainer = document.getElementById(user.uid);
                    if (playerContainer) {
                        playerContainer.remove();
                    }
                });

                // Bağlantı öncesi log
                console.log("Kanala katılmaya çalışılıyor...");
                console.log("AppID:", appId);
                console.log("Channel:", channel);
                console.log("Token var mı:", !!token);

                await rtc.client.join(options.appId, options.channel, options.token || null);
                console.log("Kanala katılım başarılı");

                if (isSender) {
                    console.log(`${cameraCount} kamera için yayın başlatılıyor...`);
                    for (let i = 0; i < cameraCount; i++) {
                        try {
                            const cameraConfig = { 
                                deviceId: i.toString(),
                                encoderConfig: {
                                    width: 640,
                                    height: 480,
                                    frameRate: 15,
                                    bitrateMin: 600,
                                    bitrateMax: 1000
                                }
                            };
                            
                            console.log(`Kamera ${i} başlatılıyor...`);
                            const videoTrack = await AgoraRTC.createCameraVideoTrack(cameraConfig);
                            rtc.localVideoTracks.push(videoTrack);
                            
                            const playerContainer = document.createElement("div");
                            playerContainer.id = `local-${i}`;
                            playerContainer.className = "video-item";
                            document.getElementById("videos").append(playerContainer);
                            videoTrack.play(playerContainer.id);
                            
                            console.log(`Kamera ${i} yayını başlatılıyor...`);
                            await rtc.client.publish(videoTrack);
                            console.log(`Kamera ${i} yayını başarılı`);
                        } catch (err) {
                            console.error(`Kamera ${i} hatası:`, err);
                        }
                    }
                }
            } catch (error) {
                console.error("Hata:", error);
            }
        }

        async function stopStream() {
            for (const track of rtc.localVideoTracks) {
                track.close();
            }
            rtc.localVideoTracks = [];
            
            if (rtc.localAudioTrack) {
                rtc.localAudioTrack.close();
            }
            
            await rtc.client.leave();
            document.getElementById("videos").innerHTML = "";
        }

        // PyQt6 ile iletişim için global fonksiyonlar
        window.startStreamFromQt = (appId, token, channel, cameraCount, isSender) => {
            startStream(appId, token, channel, parseInt(cameraCount), isSender === "true");
        };
        
        window.stopStreamFromQt = () => {
            stopStream();
        };
    </script>
</body>
</html>
        """
        
        # Geçici HTML dosyası oluştur
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            self.html_file = f.name
            self.web_view.setUrl(QUrl.fromLocalFile(self.html_file))

    def start_stream(self):
        app_id = self.app_id_input.text().strip()
        token = self.token_input.text().strip()
        channel = self.channel_input.text().strip()

        if not app_id or not token or not channel:
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun!")
            return

        camera_count = "3" if self.is_sender else "0"
        js_code = f'startStreamFromQt("{app_id}", "{token}", "{channel}", "{camera_count}", "{str(self.is_sender).lower()}")'
        self.web_view.page().runJavaScript(js_code)

    def closeEvent(self, event):
        # Kamera önizlemelerini kapat
        if hasattr(self, 'preview_active') and self.preview_active:
            for thread in self.camera_threads:
                thread.stop()
        
        # Geçici HTML dosyasını sil
        if hasattr(self, 'html_file') and os.path.exists(self.html_file):
            try:
                os.unlink(self.html_file)
            except:
                pass
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Komut satırı argümanlarını kontrol et
    is_sender = len(sys.argv) < 2 or sys.argv[1].lower() != 'receiver'
    
    window = MainWindow(is_sender=is_sender)
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
