import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QLCDNumber, QSizePolicy,
    QGraphicsDropShadowEffect, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QEasingCurve, QPropertyAnimation, QRect, QTimer, QUrl
from PyQt6.QtGui import QColor, QKeyEvent
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
import logging
import tempfile
import os
from dotenv import load_dotenv
from file_server import FileServer

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ika_app.log')
    ]
)

# Environment dosyasını yükle
load_dotenv('config.env')

# Agora kimlik bilgileri - Environment dosyasından alınır
AGORA_APP_ID = os.getenv('AGORA_APP_ID')
AGORA_TOKEN = os.getenv('AGORA_TOKEN')

# Kimlik bilgileri kontrolü
if not AGORA_APP_ID or not AGORA_TOKEN:
    print("❌ HATA: AGORA_APP_ID veya AGORA_TOKEN bulunamadı!")
    print("📝 Lütfen config.env dosyasını kontrol edin.")
    sys.exit(1)

# Firebase kütüphanelerini import edin (simülasyon modu)
try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# Camera 
class CameraPanel(QLabel):
    def __init__(self, camera_name: str):
        super().__init__()
        self.setMinimumSize(420, 300)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setProperty("class", "camera-tile")
        self.setText(f"""
            <div style="font-weight:800;font-size:18px;letter-spacing:.5px">
                {camera_name}<br>
                <span style="opacity:.8;font-size:14px">Simüle Edilmiş<br>Görüntü</span>
            </div>
        """)
        shadow = QGraphicsDropShadowEffect(blurRadius=24, xOffset=0, yOffset=8)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)



# Agora Camera Panel for remote video streaming
class AgoraCameraPanel(QWidget):
    def __init__(self, camera_name: str):
        super().__init__()
        self.camera_name = camera_name
        self.setMinimumSize(600, 400)  # 1440x900 için optimize edilmiş minimum boyut
        self.is_streaming = False
        self.html_file = None
        
        # Layout - tam doluluk için
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # WebView for video - tam doluluk
        self.webview = QWebEngineView()
        self.webview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.webview)
        
        # Setup WebView
        self.setup_webview()
        
        # Create HTML content
        self.html_file = self.create_webview_html()
        self.webview.setUrl(QUrl.fromLocalFile(self.html_file))
    
    def setup_webview(self):
        """WebView ayarlarını yapılandırır"""
        profile = QWebEngineProfile.defaultProfile()
        settings = profile.settings()
        
        # Medya izinleri
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, False)
        
        # Özel sayfa sınıfı oluştur
        class WebEnginePage(QWebEnginePage):
            def __init__(self, profile, parent=None):
                super().__init__(profile, parent)
                self.featurePermissionRequested.connect(self.handlePermissionRequest)
                
            def javaScriptConsoleMessage(self, level, message, line, source):
                logging.debug(f"JS [L{line}] {message}")
                
            def handlePermissionRequest(self, url, feature):
                if feature in [QWebEnginePage.Feature.MediaAudioCapture,
                             QWebEnginePage.Feature.MediaVideoCapture,
                             QWebEnginePage.Feature.MediaAudioVideoCapture]:
                    self.setFeaturePermission(
                        url,
                        feature,
                        QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
                    )
                    logging.debug(f"Medya izni verildi: {feature}")
        
        # Özel sayfayı ayarla
        self.page = WebEnginePage(profile, self.webview)
        self.webview.setPage(self.page)
        

    
    def create_webview_html(self):
        """WebView için HTML içeriği oluşturur"""
        html_content = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="Content-Security-Policy" content="default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; connect-src * 'unsafe-inline'; media-src * blob:;">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agora Remote Video</title>
        <script src="https://download.agora.io/sdk/release/AgoraRTC_N-4.19.3.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body { 
                margin: 0; 
                padding: 0;
                background: #000; 
                color: white; 
                font-family: Arial, sans-serif;
                width: 100vw;
                height: 100vh;
                overflow: hidden;
            }
            
            .video-container { 
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex; 
                align-items: center; 
                justify-content: center; 
                background: #000;
                min-width: 600px;
                min-height: 400px;
            }
            
            .video-item { 
                position: relative;
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .video-item video { 
                width: 100%;
                height: 100%;
                background: #000; 
                object-fit: cover;
                border-radius: 0;
                border: none;
                outline: none;
                min-width: 600px;
                min-height: 400px;
            }
            
            .status { 
                position: absolute;
                top: 10px;
                left: 10px;
                padding: 8px 12px;
                border-radius: 5px;
                background: rgba(0,0,0,0.8);
                font-size: 11px;
                z-index: 1000;
                max-width: 200px;
                word-wrap: break-word;
                backdrop-filter: blur(5px);
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .error { background: rgba(244,67,54,0.9); }
            .success { background: rgba(76,175,80,0.9); }
            .info { background: rgba(33,150,243,0.9); }
            .warning { background: rgba(255,152,0,0.9); }
            
            /* Responsive tasarım */
            @media (max-width: 768px) {
                .status {
                    font-size: 10px;
                    padding: 6px 10px;
                }
            }
            
            /* Video yüklenirken loading animasyonu */
            .loading {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #fff;
                font-size: 14px;
                z-index: 999;
            }
            
            /* Video container için aspect ratio koruması */
            .video-wrapper {
                position: relative;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }
        </style>
    </head>
    <body>
        <div class="status" id="status">Hazırlanıyor...</div>
        <div class="video-container">
            <div class="video-wrapper">
                <div class="video-item">
                    <video id="remoteVideo" autoplay muted></video>
                </div>
                <div class="loading" id="loading">Video bekleniyor...</div>
            </div>
        </div>
        
        <script>
            let agoraClient = null;
            let isStreaming = false;
            let loadingElement = null;
            
            function updateStatus(message, type = 'info') {
                const statusEl = document.getElementById('status');
                statusEl.textContent = message;
                statusEl.className = 'status ' + type;
                console.log(message);
            }
            
            function showLoading(show = true) {
                if (!loadingElement) {
                    loadingElement = document.getElementById('loading');
                }
                if (loadingElement) {
                    loadingElement.style.display = show ? 'block' : 'none';
                }
            }
            
            function resizeVideo() {
                const video = document.getElementById('remoteVideo');
                const container = document.querySelector('.video-container');
                
                if (video && container) {
                    // 1440x900 çözünürlüğü için optimize edilmiş ölçeklendirme
                    const containerWidth = container.offsetWidth;
                    const containerHeight = container.offsetHeight;
                    
                    // Video aspect ratio'sunu koru ama container'ı doldur
                    video.style.width = '100%';
                    video.style.height = '100%';
                    video.style.objectFit = 'cover';
                    video.style.minWidth = '600px';
                    video.style.minHeight = '400px';
                }
            }
            
            async function startStream(appId, token, channel) {
                if (isStreaming) {
                    updateStatus('Zaten yayın yapılıyor!', 'warning');
                    return;
                }
                
                try {
                    showLoading(true);
                    updateStatus('Agora istemcisi başlatılıyor...', 'info');
                    
                    agoraClient = AgoraRTC.createClient({ 
                        mode: "rtc", 
                        codec: "vp8",
                        role: "audience"
                    });
                    
                    agoraClient.on("error", (error) => {
                        console.error('Agora istemci hatası:', error);
                        updateStatus('❌ Agora hatası: ' + error.message, 'error');
                        showLoading(false);
                    });
                    
                    agoraClient.on("connection-state-change", (curState, prevState, reason) => {
                        console.log('Bağlantı durumu:', prevState, '->', curState, 'Neden:', reason);
                        updateStatus('Bağlantı: ' + curState, 'info');
                        
                        if (curState === 'CONNECTED') {
                            showLoading(false);
                        }
                    });
                    
                    agoraClient.on("user-published", handleUserPublished);
                    agoraClient.on("user-unpublished", handleUserUnpublished);
                    
                    updateStatus('Kanala katılım yapılıyor...', 'info');
                    await agoraClient.join(appId, channel, token, null);
                    
                    isStreaming = true;
                    updateStatus('✅ Bağlantı kuruldu, yayın bekleniyor...', 'success');
                    
                } catch (error) {
                    console.error('Hata:', error);
                    updateStatus('❌ Hata: ' + error.message, 'error');
                    showLoading(false);
                }
            }
            
            async function stopStream() {
                if (!isStreaming) {
                    updateStatus('Zaten yayın yapılmıyor!', 'warning');
                    return;
                }
                
                try {
                    updateStatus('Yayın durduruluyor...', 'info');
                    showLoading(true);
                    
                    if (agoraClient) {
                        await agoraClient.leave();
                        agoraClient = null;
                    }
                    
                    const video = document.getElementById('remoteVideo');
                    if (video) {
                        video.srcObject = null;
                    }
                    
                    isStreaming = false;
                    updateStatus('✅ Yayın durduruldu.', 'success');
                    showLoading(false);
                    
                } catch (error) {
                    console.error('Hata:', error);
                    updateStatus('❌ Hata: ' + error.message, 'error');
                    showLoading(false);
                }
            }
            
            async function handleUserPublished(user, mediaType) {
                updateStatus('Uzak kullanıcı yayın başlattı: ' + user.uid, 'info');
                
                await agoraClient.subscribe(user, mediaType);
                
                if (mediaType === 'video') {
                    const video = document.getElementById('remoteVideo');
                    user.videoTrack.play("remoteVideo");
                    
                    // Video yüklendiğinde boyutları ayarla
                    video.onloadedmetadata = function() {
                        resizeVideo();
                        showLoading(false);
                    };
                    
                    updateStatus('Uzak video eklendi', 'success');
                }
                if (mediaType === 'audio') {
                    user.audioTrack.play();
                    updateStatus('Uzak ses eklendi', 'success');
                }
            }
            
            function handleUserUnpublished(user) {
                updateStatus('Uzak kullanıcı yayın durdurdu: ' + user.uid, 'info');
                showLoading(true);
            }
            
            // Pencere boyutu değiştiğinde video boyutunu ayarla
            window.addEventListener('resize', resizeVideo);
            
            // Video elementinin boyutları değiştiğinde
            const video = document.getElementById('remoteVideo');
            if (video) {
                const resizeObserver = new ResizeObserver(() => {
                    resizeVideo();
                });
                resizeObserver.observe(video);
            }
            
            // Kaydetme fonksiyonları - WebRTC Remote Recorder yaklaşımı
            let mediaRecorder = null;
            let recordedChunks = [];
            let currentFilename = '';
            let currentFilepath = '';
            
            async function startRecording(filename, filepath) {
                try {
                    const video = document.getElementById('remoteVideo');
                    if (!video.srcObject) {
                        updateStatus('❌ Kaydedilecek video yok', 'error');
                        return;
                    }
                    
                    currentFilename = filename || 'kayit.webm';
                    currentFilepath = filepath || '';
                    recordedChunks = [];
                    
                    const stream = video.srcObject;
                    mediaRecorder = new MediaRecorder(stream, {
                        mimeType: 'video/webm;codecs=vp9'
                    });
                    
                    mediaRecorder.ondataavailable = function(event) {
                        if (event.data.size > 0) {
                            recordedChunks.push(event.data);
                        }
                    };
                    
                    mediaRecorder.onstop = function() {
                        const blob = new Blob(recordedChunks, { type: 'video/webm' });
                        
                                                // WebRTC Remote Recorder yaklaşımı - HTTP sunucusu ile dosya kaydetme
            if (currentFilepath) {
                // Blob'u base64'e çevir
                const reader = new FileReader();
                reader.onload = function() {
                    const base64Data = reader.result.split(',')[1];
                    
                    // HTTP sunucusuna gönder
                    fetch('http://localhost:8080', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            filename: currentFilename,
                            data: base64Data
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            updateStatus('✅ Dosya kaydedildi: ' + data.filepath, 'success');
                        } else {
                            updateStatus('❌ Dosya kaydetme hatası', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Dosya kaydetme hatası:', error);
                        updateStatus('❌ Dosya kaydetme hatası: ' + error.message, 'error');
                    });
                };
                reader.readAsDataURL(blob);
            }
            
            // Ayrıca tarayıcı indirme seçeneği de sun
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // URL'yi temizle
            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 10000);
                        
                        recordedChunks = [];
                        updateStatus('✅ Kayıt tamamlandı: ' + currentFilename, 'success');
                    };
                    
                    mediaRecorder.start(1000); // Her 1 saniyede bir chunk al
                    updateStatus('📹 Kayıt başladı: ' + currentFilename, 'info');
                    
                } catch (error) {
                    console.error('Kayıt hatası:', error);
                    updateStatus('❌ Kayıt hatası: ' + error.message, 'error');
                }
            }
            
            function stopRecording() {
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                    mediaRecorder.stop();
                    updateStatus('⏹️ Kayıt durduruldu', 'info');
                }
            }
            

            
            window.onload = function() {
                updateStatus('Sayfa yüklendi ve hazır.', 'info');
                showLoading(false);
                resizeVideo();
            };
        </script>
    </body>
</html>
        """
        
        # Geçici HTML dosyası oluştur
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            return f.name
    
    def start_stream(self, app_id, token, channel):
        """Yayını başlatır"""
        if not self.is_streaming:
            js_code = f"startStream('{app_id}', '{token}', '{channel}')"
            self.webview.page().runJavaScript(js_code)
            self.is_streaming = True
    
    def stop_stream(self):
        """Yayını durdurur"""
        if self.is_streaming:
            self.webview.page().runJavaScript("stopStream()")
            self.is_streaming = False
    
    def start_recording(self, filename):
        """Kaydetmeyi başlatır"""
        try:
            # Recordings klasörüne tam yol oluştur
            recordings_dir = os.path.join(os.path.dirname(__file__), 'recordings')
            os.makedirs(recordings_dir, exist_ok=True)
            filepath = os.path.join(recordings_dir, filename)
            
            # Kaydetme için JavaScript kodu - tam dosya yolu ile
            js_code = f"startRecording('{filename}', '{filepath}')"
            self.webview.page().runJavaScript(js_code)
            logging.info(f"Kaydetme başlatıldı: {filepath}")
        except Exception as e:
            logging.error(f"Kaydetme başlatma hatası: {e}")
    
    def stop_recording(self):
        """Kaydetmeyi durdurur"""
        try:
            self.webview.page().runJavaScript("stopRecording()")
            logging.info("Kaydetme durduruldu")
        except Exception as e:
            logging.error(f"Kaydetme durdurma hatası: {e}")
    
    def closeEvent(self, event):
        """Widget kapatılırken geçici dosyaları temizle"""
        try:
            if self.html_file and os.path.exists(self.html_file):
                os.unlink(self.html_file)
        except:
            pass
        event.accept()

# Sensör verisi üretici thread (Firebase entegrasyonu ile)

class SensorThread(QThread):
    sensor_data = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = True
        self.firebase_initialized = False
        
    def run(self):
        while self.running:
            if FIREBASE_AVAILABLE and self.firebase_initialized:
                try:
                    ref = db.reference('sensors')
                    firebase_data = ref.get()
                    
                    if firebase_data:
                        self.sensor_data.emit(firebase_data)
                        
                except Exception as e:
                    pass
            
            self.msleep(1000)  # 1 saniye bekle

    def set_firebase_initialized(self, status: bool):
        """Firebase durumunu güncelle"""
        self.firebase_initialized = status

    def stop(self):
        self.running = False

# -----------------------------
# Firebase Thread (mevcut entegrasyonu koru)
# -----------------------------
class FirebaseThread(QThread):
    data_received = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.firebase_initialized = False
        
    def initialize_firebase(self):
        if not FIREBASE_AVAILABLE:
            return False
            
        try:
            # Firebase zaten başlatılmışsa sadece bağlantıyı kontrol et
            if firebase_admin._apps:
                self.firebase_initialized = True
                return True
                
            # Firebase'i başlat
            cred = credentials.Certificate('ika-db-eb609-firebase-adminsdk-fbsvc-27327d9168.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://ika-db-eb609-default-rtdb.europe-west1.firebasedatabase.app/'
            })
            self.firebase_initialized = True
            return True
        except Exception as e:
            self.firebase_initialized = False
            return False
    
    def run(self):
        if not self.initialize_firebase():
            # Simülasyon yok: bağlantı kurulana kadar bekle ve tekrar dene
            while self.running and not self.initialize_firebase():
                self.msleep(1000)
        else:
            # Gerçek Firebase modu
            ref = db.reference()
            while self.running:
                try:
                    # Sensör verilerini al
                    sensors = ref.child('sensors').get()
                    if sensors:
                        self.data_received.emit({'type': 'sensors', 'data': sensors})
                    else:
                        # Sensör verisi yoksa bunu bildir
                        self.data_received.emit({'type': 'sensors_empty', 'data': None})
                    
                    # Kontrol verilerini al
                    control = ref.child('control').get()
                    if control:
                        self.data_received.emit({'type': 'control', 'data': control})
                    
                    # Vites verisini al
                    gear = ref.child('gear').get()
                    if gear:
                        self.data_received.emit({'type': 'gear', 'data': gear})
                    
                    # Komut verilerini al
                    commands = ref.child('commands').get()
                    if commands:
                        self.data_received.emit({'type': 'commands', 'data': commands})
                    
                    # Lazer verilerini al
                    laser = ref.child('laser').get()
                    if laser:
                        self.data_received.emit({'type': 'laser', 'data': laser})
                    
                    # Acil durum verilerini al
                    emergency = ref.child('emergency').get()
                    if emergency:
                        self.data_received.emit({'type': 'emergency', 'data': emergency})
                    
                    self.msleep(100)
                    
                except Exception as e:
                    self.msleep(1000)
    
    def stop(self):
        self.running = False

# Ana Pencere
class IKADashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.laser_mode = False
        self.current_theme = "NeoDark"
        self.firebase_initialized = False
        self.setWindowTitle("İKA Kontrol Arayüzü")
        self._base_title = self.windowTitle()
        
        self.pressed_keys = set()
        # Klavye tekrar sorununu çözmek için
        self.key_states = {}
        
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        # 1440x900 çözünürlüğü için optimize edilmiş boyutlar
        window_width = min(1440, screen_geometry.width() - 50)
        window_height = min(900, screen_geometry.height() - 50)
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        
        self.setGeometry(x, y, window_width, window_height)

        self.build_ui()
        self.setup_shortcuts()
        self.build_sensors()
        self.init_firebase()
        self.apply_theme(self.current_theme)
        
        # Firebase başlatıldıktan sonra eski dalları temizle!! BURAYA TEKRAR BAK
        if self.firebase_initialized:
            self.cleanup_firebase_data()
        
        self.show()
    # Genel CSS 
    def neo_dark_qss(self):
        return """
        * { font-family: 'Segoe UI', 'Inter', 'Arial'; }
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0b1020, stop:1 #0a0f1a);
        }
        /* Top Bar */
        #TopBar {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0e1726, stop:1 #0a1020);
            border-bottom: 1px solid #0f1d3a;
        }
        QLabel#Title {
            color:#e2e8f0; font-weight:900; font-size:18px; letter-spacing:.8px;
        }
        QLabel#Badge {
            color:#94a3b8; background: rgba(30,41,59,.35);
            padding:6px 10px; border-radius:999px; border:1px solid #1e293b;
            font-weight:700; font-size:12px;
        }
        QPushButton#TopBtn {
            background: rgba(15,23,42,.6);
            border: 1px solid #1f2a44; color:#cbd5e1;
            border-radius: 10px; padding:8px 12px; font-weight:700;
        }
        QPushButton#TopBtn:hover { background: rgba(30,41,59,.9); border-color:#334155; }
        /* Group Cards */
        QGroupBox {
            color:#e5e7eb; font-weight:800; font-size:16px;
            border: 1px solid #1f2a44; border-radius: 16px;
            margin-top: 16px; padding-top: 18px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(17,24,39,.65), stop:1 rgba(2,6,23,.65));
        }
        QGroupBox::title {
            subcontrol-origin: margin; left:16px; padding:0 10px;
            background: rgba(15,23,42,.9);
            border:1px solid #1f2a44; border-radius:10px;
        }
        QLabel { color:#cbd5e1; font-weight:700; font-size:14px; }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #12213f, stop:1 #0c1a33);
            border: 1px solid #1e335a; border-radius: 12px;
            color: #e5e7eb; font-weight: 800; padding: 10px 12px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1c2f5a, stop:1 #12213f);
            border-color: #3b82f6;
        }
        QPushButton:pressed { background:#0b1730; border-color:#0b1730; }
        QPushButton#emergency {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #991b1b, stop:1 #7f1d1d);
            border: 2px solid #b91c1c; color:#fee2e2;
            font-size: 18px; border-radius: 18px; padding:14px;
        }
        QPushButton#emergency:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #dc2626, stop:1 #b91c1c);
            border: 3px solid #ef4444; color:#fff;
        }
        QPushButton#laser {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #7c2d12, stop:1 #7f1d1d);
            border: 1px solid #b45309;
        }
        QPushButton#laser:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ea580c, stop:1 #b45309);
            border: 2px solid #f59e0b; color:#fff;
        }
        QLCDNumber {
            background:#0b1325; color:#22d3ee;
            border:1px solid #1e335a; border-radius:10px;
        }
        QLabel[class~="camera-tile"] {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0b1730, stop:1 #0b1120);
            border:1px solid #1e335a; border-radius:16px;
        }
        #BottomBar {
            background: rgba(2,6,23,.6);
            border-top: 1px solid #1f2a44;
        }
        QProgressBar {
            background: #0b1325; border:1px solid #1e335a;
            border-radius:8px; color:#e5e7eb; text-align:center;
        }
        QProgressBar::chunk { background:#16a34a; border-radius:8px; }
        """

    def glass_qss(self):
        return """
        * { font-family: 'Segoe UI', 'Inter', 'Arial'; }
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0f172a, stop:1 #111827);
        }
        #TopBar {
            background: rgba(255,255,255,.06);
            border-bottom: 1px solid rgba(255,255,255,.08);
        }
        QLabel#Title { color:#f8fafc; font-weight:900; font-size:18px; letter-spacing:.8px; }
        QLabel#Badge {
            color:#e5e7eb; background: rgba(255,255,255,.08);
            padding:6px 10px; border-radius:999px; border:1px solid rgba(255,255,255,.12);
            font-weight:700; font-size:12px;
        }
        QPushButton#TopBtn {
            background: rgba(255,255,255,.06);
            border: 1px solid rgba(255,255,255,.12);
            color:#e5e7eb; border-radius: 10px; padding:8px 12px; font-weight:700;
        }
        QPushButton#TopBtn:hover { background: rgba(255,255,255,.1); }
        QGroupBox {
            color:#f3f4f6; font-weight:900; font-size:16px;
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 20px; margin-top: 18px; padding-top: 20px;
            background: rgba(255,255,255,.06);
        }
        QGroupBox::title {
            subcontrol-origin: margin; left:16px; padding:0 10px;
            background: rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.12);
            border-radius:10px;
        }
        QLabel { color:#e2e8f0; font-weight:800; font-size:14px; }
        QPushButton {
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 12px; color:#f8fafc; font-weight:900; padding:10px 12px;
        }
        QPushButton:hover { background: rgba(255,255,255,.14); }
        QPushButton:pressed { background: rgba(255,255,255,.2); }
        QPushButton#emergency {
            background: rgba(239,68,68,.2); border-color: rgba(239,68,68,.5);
            color:#fee2e2; font-size:18px; border-radius:18px; padding:14px;
        }
        QPushButton#laser {
            background: rgba(234,88,12,.2); border-color: rgba(234,88,12,.5);
        }
        QPushButton#emergency:checked {
            background: rgba(239,68,68,.35); border-color: rgba(239,68,68,.7);
            color:#fff;
        }
        QPushButton#laser:checked {
            background: rgba(234,88,12,.35); border-color: rgba(234,88,12,.7);
            color:#fff;
        }
        QLCDNumber {
            background: rgba(2,6,23,.6); color:#22d3ee;
            border: 1px solid rgba(255,255,255,.12); border-radius: 10px;
        }
        QLabel[class~="camera-tile"] {
            background: rgba(255,255,255,.06);
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 18px;
        }
        #BottomBar {
            background: rgba(255,255,255,.06);
            border-top: 1px solid rgba(255,255,255,.12);
        }
        QProgressBar {
            background: rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12);
            border-radius:8px; color:#e5e7eb; text-align:center;
        }
        QProgressBar::chunk { background: rgba(34,197,94,.9); border-radius:8px; }
        """

    def apply_theme(self, name: str):
        if name == "NeoDark":
            self.setStyleSheet(self.neo_dark_qss())
        else:
            self.setStyleSheet(self.glass_qss())

    # UI
    def build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        middle_wrap = QWidget()
        middle = QHBoxLayout(middle_wrap)
        middle.setContentsMargins(12, 12, 12, 12)
        middle.setSpacing(20)

        # Sol: Kameralar
        left = self.create_camera_panel()
        middle.addWidget(left, 4)

        # Sağ: Kontroller + Sensörler
        right = self.create_control_panel()
        middle.addWidget(right, 1)

        root.addWidget(middle_wrap, 1)

        self._middle_wrap = middle_wrap

    def reveal_anim(self, widget):
        anim = QPropertyAnimation(widget, b"geometry")
        start_rect = QRect(widget.x(), widget.y() + 30, widget.width(), widget.height())
        anim.setDuration(380)
        anim.setStartValue(start_rect)
        anim.setEndValue(widget.geometry())
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._reveal_anim = anim  # referansı sakla

    def _force_initial_layout(self):
      
        if self._middle_wrap is not None:
            lay = self._middle_wrap.layout()
            if lay is not None:
                lay.activate()
        self.updateGeometry()
        QApplication.processEvents()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, "_first_shown"):
            self._first_shown = True
            QTimer.singleShot(0, lambda: (self._force_initial_layout(), self.reveal_anim(self._middle_wrap)))
        
        # Pencereye focus ver ki tuş olayları yakalansın
        self.setFocus()

    # Camera
    def create_camera_panel(self):
        panel = QGroupBox("📹 Kamera Görüntüleri")
        layout = QVBoxLayout(panel)
        layout.setSpacing(14)

        # Üst satır: Ön Kamera (Agora) + Vites Kontrolü
        top_row = QHBoxLayout()
        top_row.setSpacing(20)  # 1440x900 için daha fazla boşluk

        # Ön kamera yerine Agora kamera paneli kullan - 1440x900 için optimize
        self.front_camera = AgoraCameraPanel("🚗 Ön Kamera")
        self.front_camera.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.front_camera.setMinimumSize(800, 450)  # 1440x900 için optimize edilmiş minimum boyut
        self.front_camera.setMaximumHeight(500)  # Maksimum yükseklik sınırı
        top_row.addWidget(self.front_camera, 1)

        self.gear_group = self.create_gear_group()
        self.gear_group.setMaximumWidth(180)  # 1440x900 için daha geniş
        top_row.addWidget(self.gear_group, 0)

        layout.addLayout(top_row)

                # Alt satır: Lazer Kamera ve Arka Kamera (Agora)
        grid = QGridLayout()
        grid.setSpacing(20)  # 1440x900 için daha fazla boşluk

        # Lazer Atış Kamera - Agora entegrasyonu (1440x900 için optimize)
        self.laser_camera = AgoraCameraPanel("🎯 Lazer Atış Kamera")
        self.laser_camera.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.laser_camera.setMinimumSize(600, 350)  # 1440x900 için optimize edilmiş boyut
        self.laser_camera.setMaximumHeight(400)  # Maksimum yükseklik sınırı

        # Arka Kamera - Agora entegrasyonu (1440x900 için optimize)
        self.back_camera = AgoraCameraPanel("🔙 Arka Kamera")
        self.back_camera.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.back_camera.setMinimumSize(600, 350)  # 1440x900 için optimize edilmiş boyut
        self.back_camera.setMaximumHeight(400)  # Maksimum yükseklik sınırı

        grid.addWidget(self.laser_camera, 0, 0)
        grid.addWidget(self.back_camera, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        layout.addLayout(grid)
        return panel

    def create_gear_group(self):
        group = QGroupBox("Vites")
        g = QGridLayout(group); g.setSpacing(6)

        # Vites Kontrol Tuşları
        self.gear1_btn = QPushButton("1"); self.gear1_btn.setMinimumSize(70, 40); self.gear1_btn.setCheckable(True)
        self.gear2_btn = QPushButton("2"); self.gear2_btn.setMinimumSize(70, 40); self.gear2_btn.setCheckable(True)
        self.gearB_btn = QPushButton("B"); self.gearB_btn.setMinimumSize(70, 40); self.gearB_btn.setCheckable(True)
        self.gearG_btn = QPushButton("G"); self.gearG_btn.setMinimumSize(90, 60); self.gearG_btn.setCheckable(True)

        for btn, gr in [
            (self.gear1_btn, "1"),
            (self.gear2_btn, "2"),
            (self.gearB_btn, "B"),
            (self.gearG_btn, "G"),
        ]:
            btn.setStyleSheet("font-size:14px;font-weight:900;")
            btn.pressed.connect(lambda gear=gr: self.gear_pressed(gear))
            btn.released.connect(lambda gear=gr: self.gear_released(gear))

        g.addWidget(self.gear1_btn, 0, 0)
        g.addWidget(self.gear2_btn, 1, 0)
        g.addWidget(self.gearB_btn, 2, 0)
        g.addWidget(self.gearG_btn, 3, 0)
        
        # Gaz kontrolü 
        throttle_layout = QVBoxLayout()
        throttle_layout.setSpacing(2)
        throttle_layout.setContentsMargins(0, 8, 0, 0)
        
        throttle_label = QLabel("Gaz Kontrolü")
        throttle_label.setStyleSheet("font-size:10px;font-weight:700;color:#cbd5e1;")
        throttle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        throttle_layout.addWidget(throttle_label)
        
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        self.throttle_up_btn = QPushButton("+"); self.throttle_up_btn.setMinimumSize(30, 25)
        self.throttle_down_btn = QPushButton("-"); self.throttle_down_btn.setMinimumSize(30, 25)
        
        for b, name in [(self.throttle_up_btn,"up"),(self.throttle_down_btn,"down")]:
            b.setStyleSheet("font-size:10px;font-weight:900;")
            b.pressed.connect(lambda nm=name: self.throttle_pressed(nm))
            b.released.connect(lambda nm=name: self.throttle_released(nm))
        
        button_layout.addWidget(self.throttle_up_btn)
        button_layout.addWidget(self.throttle_down_btn)
        throttle_layout.addLayout(button_layout)
        g.addLayout(throttle_layout, 4, 0)
        
        return group

    def create_sensor_panel(self):
        panel = QGroupBox("Sensör Verileri")
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        panel.setStyleSheet("QLabel { font-size:12px; }")

        # IMU
        imu_group = QWidget()
        imu = QGridLayout(imu_group); imu.setSpacing(6); imu.setContentsMargins(0, 0, 0, 0)

        self.roll_lcd = QLCDNumber(); self.roll_lcd.setDigitCount(6)
        self.pitch_lcd = QLCDNumber(); self.pitch_lcd.setDigitCount(6)
        self.yaw_lcd = QLCDNumber(); self.yaw_lcd.setDigitCount(6)

        imu.addWidget(QLabel("Roll (°):"), 0, 0); imu.addWidget(self.roll_lcd, 0, 1)
        imu.addWidget(QLabel("Pitch (°):"), 1, 0); imu.addWidget(self.pitch_lcd, 1, 1)
        imu.addWidget(QLabel("Yaw (°):"), 2, 0); imu.addWidget(self.yaw_lcd, 2, 1)

        layout.addWidget(imu_group)

        # GPS 
        gps_group = QWidget()
        gps = QGridLayout(gps_group); gps.setSpacing(6); gps.setContentsMargins(0, 0, 0, 0)

        self.lat_lcd = QLCDNumber(); self.lat_lcd.setDigitCount(9)
        self.lon_lcd = QLCDNumber(); self.lon_lcd.setDigitCount(9)
        self.alt_lcd = QLCDNumber(); self.alt_lcd.setDigitCount(6)
        self.speed_lcd = QLCDNumber(); self.speed_lcd.setDigitCount(6)

        gps.addWidget(QLabel("Latitude:"), 0, 0); gps.addWidget(self.lat_lcd, 0, 1)
        gps.addWidget(QLabel("Longitude:"), 1, 0); gps.addWidget(self.lon_lcd, 1, 1)
        gps.addWidget(QLabel("Altitude (m):"), 2, 0); gps.addWidget(self.alt_lcd, 2, 1)
        gps.addWidget(QLabel("Speed (km/h):"), 3, 0); gps.addWidget(self.speed_lcd, 3, 1)

        layout.addWidget(gps_group)
        
        # Kamera Kontrol Paneli
        camera_group = QGroupBox("📹 Kamera Kontrolü")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setSpacing(10)
        
        # Yayın Başlatma Butonu
        self.start_all_streams_btn = QPushButton("🎥 Yayını Başlat")
        self.start_all_streams_btn.clicked.connect(self.start_all_camera_streams)
        self.start_all_streams_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: 1px solid #4CAF50; border-radius: 8px;
                color: white; font-weight: 800; padding: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #4CAF50);
            }
        """)
        camera_layout.addWidget(self.start_all_streams_btn)
        
        # Kaydetme Başlatma Butonu
        self.start_recording_btn = QPushButton("📹 Kaydetmeyi Başlat")
        self.start_recording_btn.clicked.connect(self.start_recording_all_cameras)
        self.start_recording_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                border: 1px solid #2196F3; border-radius: 8px;
                color: white; font-weight: 800; padding: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976D2, stop:1 #2196F3);
            }
        """)
        camera_layout.addWidget(self.start_recording_btn)
        
        layout.addWidget(camera_group)
        layout.addStretch()
        return panel

    def create_control_panel(self):
        panel = QGroupBox("Kontrol Paneli")
        layout = QVBoxLayout(panel)
        layout.setSpacing(6)

        # Acil Durdur
        self.emergency_btn = QPushButton("🚨 ACİL DURDUR")
        self.emergency_btn.setObjectName("emergency")
        self.emergency_btn.setCheckable(True)
        self.emergency_btn.clicked.connect(self.emergency_stop)
        layout.addWidget(self.emergency_btn)

        # Durum Kontrolü
        mode_group = QGroupBox("Kontrol Modu")
        mode_l = QHBoxLayout(mode_group); mode_l.setSpacing(8)

        self.manual_btn = QPushButton("Manuel"); self.manual_btn.setCheckable(True); self.manual_btn.setChecked(True)
        self.semi_auto_btn = QPushButton("Yarı Otonom"); self.semi_auto_btn.setCheckable(True)
        self.auto_btn = QPushButton("Otonom"); self.auto_btn.setCheckable(True)

        self.manual_btn.clicked.connect(lambda: self.set_control_mode("manual"))
        self.semi_auto_btn.clicked.connect(lambda: self.set_control_mode("semi"))
        self.auto_btn.clicked.connect(lambda: self.set_control_mode("auto"))

        mode_l.addWidget(self.manual_btn)
        mode_l.addWidget(self.semi_auto_btn)
        mode_l.addWidget(self.auto_btn)
        layout.addWidget(mode_group)

        # Lazer Modu
        self.laser_btn = QPushButton("LAZER ATIŞ MODU")
        self.laser_btn.setObjectName("laser")
        self.laser_btn.setCheckable(True)
        self.laser_btn.clicked.connect(self.toggle_laser_mode)
        layout.addWidget(self.laser_btn)

        # Normal Yön Tuşları
        self.direction_group = QGroupBox("Yön Kontrolü")
        d = QGridLayout(self.direction_group); d.setSpacing(6)
        d.setContentsMargins(0, 0, 0, 0)
        d.setRowStretch(3, 1)

        self.up_btn = QPushButton("▲\nİleri"); self.up_btn.setMinimumSize(70, 70)
        self.down_btn = QPushButton("▼\nGeri"); self.down_btn.setMinimumSize(70, 70)

        self.left_btn = QPushButton("◄\nSol"); self.left_btn.setMinimumSize(70, 70)
        self.right_btn = QPushButton("►\nSağ"); self.right_btn.setMinimumSize(70, 70)

        for b, name in [(self.up_btn,"up"),(self.down_btn,"down"),(self.left_btn,"left"),(self.right_btn,"right")]:
            b.setStyleSheet("font-size:14px;font-weight:900;")
            b.pressed.connect(lambda nm=name: self.direction_pressed(nm))
            b.released.connect(lambda nm=name: self.direction_released(nm))

        d.addWidget(self.up_btn, 0, 1)
        d.addWidget(self.left_btn, 1, 0)
        d.addWidget(self.down_btn, 1, 1)
        d.addWidget(self.right_btn, 1, 2)
        layout.addWidget(self.direction_group)

        # Lazer yön kontrol tuşları
        self.laser_direction_group = QGroupBox("Lazer Yön Kontrolü")
        ld = QGridLayout(self.laser_direction_group); ld.setSpacing(6)

        self.laser_up_btn = QPushButton("▲\nYukarı"); self.laser_up_btn.setMinimumSize(70, 70)
        self.laser_down_btn = QPushButton("▼\nAşağı"); self.laser_down_btn.setMinimumSize(70, 70)
        self.laser_left_btn = QPushButton("◄\nSol"); self.laser_left_btn.setMinimumSize(70, 70)
        self.laser_right_btn = QPushButton("►\nSağ"); self.laser_right_btn.setMinimumSize(70, 70)
        self.laser_fire_btn = QPushButton("🔥\nATEŞ!"); self.laser_fire_btn.setMinimumSize(70, 70)

        redish = "font-size:12px;font-weight:900;"
        for b, nm in [
            (self.laser_up_btn,"up"), (self.laser_down_btn,"down"),
            (self.laser_left_btn,"left"), (self.laser_right_btn,"right")
        ]:
            b.setStyleSheet(redish)
            b.pressed.connect(lambda name=nm: self.laser_direction_pressed(name))
            b.released.connect(lambda name=nm: self.laser_direction_released(name))

        self.laser_fire_btn.setStyleSheet("font-size:14px;font-weight:1000;")
        self.laser_fire_btn.pressed.connect(self.laser_fire_pressed)
        self.laser_fire_btn.released.connect(self.laser_fire_released)

        ld.addWidget(self.laser_up_btn, 0, 1)
        ld.addWidget(self.laser_left_btn, 1, 0)
        ld.addWidget(self.laser_fire_btn, 1, 1)
        ld.addWidget(self.laser_right_btn, 1, 2)
        ld.addWidget(self.laser_down_btn, 2, 1)

        layout.addWidget(self.laser_direction_group)
        self.laser_direction_group.hide()

        sensor_panel = self.create_sensor_panel()
        layout.addWidget(sensor_panel)

        layout.addStretch()

        return panel

    # ---------- Klavye Kısayolları ----------
    def setup_shortcuts(self):
        # Artık keyPressEvent ve keyReleaseEvent kullandığımız için kısayol tuşlarına gerek yok
        # Sadece focus'u pencereye verdik ki tuş olayları yakalansın
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _highlight_button(self, direction: str):
        """Tuşa basınca ilgili butonu vurgula"""
        # Buton eşleştirmeleri
        button_map = {
            'up': self.up_btn,
            'down': self.down_btn,
            'left': self.left_btn,
            'right': self.right_btn
        }
        
        if direction in button_map:
            button = button_map[direction]
            # Butonu vurgula - basılı tutma süresince kalacak

            original_style = button.styleSheet()
            button.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            button.setProperty("original_style", original_style)

    def _unhighlight_button(self, direction: str):
        """Tuş bırakıldığında butonun vurgusunu kaldır"""
        button_map = {
            'up': self.up_btn,
            'down': self.down_btn,
            'left': self.left_btn,
            'right': self.right_btn
        }
        
        if direction in button_map:
            button = button_map[direction]
            original_style = button.property("original_style")
            if original_style:
                button.setStyleSheet(original_style)

    def _highlight_laser_button(self, direction: str):
        """Lazer modunda tuşa basınca ilgili butonu vurgula"""
        # Lazer buton eşleştirmeleri
        laser_button_map = {
            'up': self.laser_up_btn,
            'down': self.laser_down_btn,
            'left': self.laser_left_btn,
            'right': self.laser_right_btn
        }
        
        if direction in laser_button_map:
            button = laser_button_map[direction]
            # Butonu vurgula - basılı tutma süresince kalacak
            original_style = button.styleSheet()
            button.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            # Butonun orijinal stilini sakla ki tuş bırakıldığında geri döndürebilelim
            button.setProperty("original_style", original_style)

    def _unhighlight_laser_button(self, direction: str):
        """Lazer modunda tuş bırakıldığında butonun vurgusunu kaldır"""
        laser_button_map = {
            'up': self.laser_up_btn,
            'down': self.laser_down_btn,
            'left': self.laser_left_btn,
            'right': self.laser_right_btn
        }
        
        if direction in laser_button_map:
            button = laser_button_map[direction]
            original_style = button.property("original_style")
            if original_style:
                button.setStyleSheet(original_style)

    def _highlight_gear_button(self, gear: str):
        """Vites tuşuna basınca ilgili butonu vurgula"""
        # Vites buton eşleştirmeleri
        gear_button_map = {
            '1': self.gear1_btn,
            '2': self.gear2_btn,
            'B': self.gearB_btn,
            'G': self.gearG_btn
        }
        
        if gear in gear_button_map:
            button = gear_button_map[gear]
            # Butonu vurgula - basılı tutma süresince kalacak
            original_style = button.styleSheet()
            button.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            button.setProperty("original_style", original_style)

    def _unhighlight_gear_button(self, gear: str):
        """Vites tuşu bırakıldığında butonun vurgusunu kaldır"""
        gear_button_map = {
            '1': self.gear1_btn,
            '2': self.gear2_btn,
            'B': self.gearB_btn,
            'G': self.gearG_btn
        }
        
        if gear in gear_button_map:
            button = gear_button_map[gear]
            original_style = button.property("original_style")
            if original_style:
                button.setStyleSheet(original_style)

    def _highlight_laser_fire_button(self):
        """Lazer ateşleme butonunu vurgula"""
        if hasattr(self, 'laser_fire_btn'):
            original_style = self.laser_fire_btn.styleSheet()
            self.laser_fire_btn.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            self.laser_fire_btn.setProperty("original_style", original_style)

    def _unhighlight_laser_fire_button(self):
        """Lazer ateşleme butonunun vurgusunu kaldır"""
        if hasattr(self, 'laser_fire_btn'):
            original_style = self.laser_fire_btn.property("original_style")
            if original_style:
                self.laser_fire_btn.setStyleSheet(original_style)

    def _highlight_laser_toggle_button(self):
        """Lazer toggle butonunu vurgula"""
        original_style = self.laser_btn.styleSheet()
        self.laser_btn.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
        QTimer.singleShot(200, lambda: self.laser_btn.setStyleSheet(original_style))

    def _highlight_emergency_button(self):
        """Acil durdurma butonunu vurgula"""
        original_style = self.emergency_btn.styleSheet()
        self.emergency_btn.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
        QTimer.singleShot(200, lambda: self.emergency_btn.setStyleSheet(original_style))



    def _highlight_throttle_button(self, direction: str):
        """Gaz butonunu vurgula"""
        throttle_button_map = {
            'up': self.throttle_up_btn,
            'down': self.throttle_down_btn
        }
        
        if direction in throttle_button_map:
            button = throttle_button_map[direction]
            original_style = button.styleSheet()
            button.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            button.setProperty("original_style", original_style)

    def _unhighlight_throttle_button(self, direction: str):
        """Gaz butonunun vurgusunu kaldır"""
        throttle_button_map = {
            'up': self.throttle_up_btn,
            'down': self.throttle_down_btn
        }
        
        if direction in throttle_button_map:
            button = throttle_button_map[direction]
            original_style = button.property("original_style")
            if original_style:
                button.setStyleSheet(original_style)
    # ---------- Sensörler ----------
    def build_sensors(self):
        self.sensor_thread = SensorThread()
        self.sensor_thread.sensor_data.connect(self.update_sensor_data)
        # Başlangıçta simülasyon modunda başla
        self.sensor_thread.set_firebase_initialized(False)
        self.sensor_thread.start()

    def update_sensor_data(self, data):
        """Sensör verilerini UI'da güncelle"""
        try:
            if 'imu' in data and isinstance(data['imu'], dict):
                imu = data['imu']
                if 'roll' in imu:
                    self.roll_lcd.display(f"{float(imu['roll']):.1f}")
                if 'pitch' in imu:
                    self.pitch_lcd.display(f"{float(imu['pitch']):.1f}")
                if 'yaw' in imu:
                    self.yaw_lcd.display(f"{float(imu['yaw']):.1f}")
            
            if 'gps' in data and isinstance(data['gps'], dict):
                gps = data['gps']
                if 'latitude' in gps:
                    self.lat_lcd.display(f"{float(gps['latitude']):.6f}")
                if 'longitude' in gps:
                    self.lon_lcd.display(f"{float(gps['longitude']):.6f}")
                if 'altitude' in gps:
                    self.alt_lcd.display(f"{float(gps['altitude']):.1f}")
                if 'speed' in gps:
                    self.speed_lcd.display(f"{float(gps['speed']):.1f}")
            
        except Exception as e:
            # Sensör verisi güncellenirken hata oluştu, sessizce geç!! BURAYA TEKRAR BAK
            pass

    # Firebase Entegrasyonu!! BURAYI MUTLAKA KONTOL ET
    def init_firebase(self):
        # Firebase thread'i her zaman oluştur (hata önleme için)
        try:
            self.firebase_thread = FirebaseThread()
            self.firebase_thread.data_received.connect(self.handle_firebase_data)
            self.firebase_thread.start()
        except Exception as e:
            # Firebase thread oluşturulamazsa boş bir thread oluştur
            self.firebase_thread = None
        
        if FIREBASE_AVAILABLE:
            try:
                if self.initialize_firebase():
                    if hasattr(self, 'sensor_thread'):
                        self.sensor_thread.set_firebase_initialized(True)
                else:
                    if hasattr(self, 'sensor_thread'):
                        self.sensor_thread.set_firebase_initialized(False)
            except Exception as e:
                if hasattr(self, 'sensor_thread'):
                    self.sensor_thread.set_firebase_initialized(False)
        else:
            if hasattr(self, 'sensor_thread'):
                self.sensor_thread.set_firebase_initialized(False)
        
        # Dosya sunucusu başlat
        self.file_server = FileServer(port=8080, recordings_dir="recordings")
        if self.file_server.start():
            logging.info("Dosya sunucusu başlatıldı")
        else:
            logging.error("Dosya sunucusu başlatılamadı")
    
    def initialize_firebase(self):
        """Firebase'i başlat"""
        if not FIREBASE_AVAILABLE:
            self.firebase_initialized = False
            return False
            
        try:
            if firebase_admin._apps:
                for app in firebase_admin._apps.copy().values():
                    firebase_admin.delete_app(app)
            
            cred = credentials.Certificate('ika-db-eb609-firebase-adminsdk-fbsvc-27327d9168.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://ika-db-eb609-default-rtdb.europe-west1.firebasedatabase.app/'
            })
            self.firebase_initialized = True
            return True
            
        except Exception as e:
            self.firebase_initialized = False
            return False
    
    def send_to_firebase(self, path, data):
        """Firebase'e veri gönder"""
        if not FIREBASE_AVAILABLE:
            return True
            
        if not self.firebase_initialized:
            return True
            
        try:
            # Tüm verilere timestamp ekle zamanlama için lazım
            data['timestamp'] = time.time()
            
            ref = db.reference(path)
            ref.set(data)
            return True
        except Exception as e:
            return True
    
    def handle_firebase_data(self, firebase_data):
        """Firebase'den gelen verileri işle"""
        data_type = firebase_data.get('type')
        data = firebase_data.get('data')
        
        if data_type == 'sensors' and data:
            self.update_sensor_data(data)
            
            if hasattr(self, 'sensor_thread'):
                self.sensor_thread.set_firebase_initialized(True)
                
        elif data_type == 'sensors_empty':
            if hasattr(self, 'sensor_thread'):
                self.sensor_thread.set_firebase_initialized(False)
            
        elif data_type == 'control' and data:
            mode = data.get('mode')
            if mode is not None:
                if mode == 'manual':
                    self.manual_btn.setChecked(True)
                    self.semi_auto_btn.setChecked(False)
                    self.auto_btn.setChecked(False)
                elif mode == 'semi_auto':
                    self.manual_btn.setChecked(False)
                    self.semi_auto_btn.setChecked(True)
                    self.auto_btn.setChecked(False)
                elif mode == 'auto':
                    self.manual_btn.setChecked(False)
                    self.semi_auto_btn.setChecked(False)
                    self.auto_btn.setChecked(True)

        elif data_type == 'gear' and data:
            if isinstance(data, dict):
                gear = data.get('gear')
            else:
                gear = str(data)

            if gear is not None:
                mapping = {
                    "1": self.gear1_btn,
                    "2": self.gear2_btn,
                    "B": self.gearB_btn,
                    "G": self.gearG_btn,
                }
                for key, btn in mapping.items():
                    btn.setChecked(key == gear)
        
        elif data_type == 'commands' and data:
            command = data.get('command', '')
        
        elif data_type == 'laser' and data:
            command = data.get('command', '')
        
        elif data_type == 'emergency' and data is not None:
            val = bool(data.get('emergency', False)) if isinstance(data, dict) else bool(data)
            self.emergency_btn.setChecked(val)
            self.emergency_btn.setText("🚨 ACİL DURDUR AKTİF" if val else "🚨 ACİL DURDUR")

    # ---------- Kontroller ----------
    def emergency_stop(self):
        is_active = self.emergency_btn.isChecked()
        self.emergency_btn.setText("🚨 ACİL DURDUR AKTİF" if is_active else "🚨 ACİL DURDUR")

        self.send_to_firebase('emergency', {'emergency': bool(is_active)})

    def start_all_camera_streams(self):
        """Tüm kameraları aynı anda başlatır"""
        # Buton metnini kontrol et
        if "Başlat" in self.start_all_streams_btn.text():
            try:
                # Her kamera için ayrı kanal ve token
                camera_configs = [
                    {
                        'camera': self.front_camera,
                        'channel': 'channel_one',
                        'token': '007eJxTYJjJXb1osVvw15vhDhLLtHw/WM6PsHnRnHDqqO3l+wLnYmoVGAwTLSwSU40tE81MTEwSjSwszJOME9NSLS0tLEzTkowsz+htyGgIZGTgfBHLxMgAgSA+N0NyRmJeXmpOfH5eKgMDAEaqIm8='
                    },
                    {
                        'camera': self.laser_camera,
                        'channel': 'channel_two',
                        'token': '007eJxTYPhrVb6g/dRbz82Shf8WMzmmqkrHsemY9Lprvarx+O5wxFeBwTDRwiIx1dgy0czExCTRyMLCPMk4MS3V0tLCwjQtycjypt6GjIZARoag7m3MjAwQCOJzMyRnJOblpebEl5TnMzAAANlVITo='
                    },
                    {
                        'camera': self.back_camera,
                        'channel': 'channel_three',
                        'token': '007eJxTYEhYEXxF43da6HQlzfhWZ0/u16ues+7817P8N0/u5i9s3j8VGAwTLSwSU40tE81MTEwSjSwszJOME9NSLS0tLEzTkowsH+ttyGgIZGQoiQhjYWSAQBCflyE5IzEvLzUnviSjKDWVgQEAot4jew=='
                    }
                ]
                
                # Tüm kameraları başlat
                for config in camera_configs:
                    config['camera'].start_stream(AGORA_APP_ID, config['token'], config['channel'])
                
                # Buton metnini güncelle
                self.start_all_streams_btn.setText("⏹️ Yayını Durdur")
                self.start_all_streams_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #f44336, stop:1 #d32f2f);
                        border: 1px solid #f44336; border-radius: 8px;
                        color: white; font-weight: 800; padding: 15px;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #d32f2f, stop:1 #f44336);
                    }
                """)
                
                QMessageBox.information(self, "Başarılı", "Tüm kameralar başlatıldı!")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kamera başlatma hatası: {str(e)}")
        else:
            # Tüm kameraları durdur
            try:
                self.front_camera.stop_stream()
                self.laser_camera.stop_stream()
                self.back_camera.stop_stream()
                
                # Buton metnini güncelle
                self.start_all_streams_btn.setText("🎥 Yayını Başlat")
                self.start_all_streams_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #4CAF50, stop:1 #45a049);
                        border: 1px solid #4CAF50; border-radius: 8px;
                        color: white; font-weight: 800; padding: 15px;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #45a049, stop:1 #4CAF50);
                    }
                """)
                
                QMessageBox.information(self, "Başarılı", "Tüm kameralar durduruldu!")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kamera durdurma hatası: {str(e)}")

    def start_recording_all_cameras(self):
        """Tüm kameraları kaydetmeye başlatır"""
        # Buton metnini kontrol et
        if "Başlat" in self.start_recording_btn.text():
            try:
                # Recordings klasörünü oluştur
                recordings_dir = os.path.join(os.path.dirname(__file__), 'recordings')
                os.makedirs(recordings_dir, exist_ok=True)
                
                # Her kamera için kaydetme başlat
                camera_recordings = [
                    {
                        'camera': self.front_camera,
                        'filename': 'on-cam.webm'
                    },
                    {
                        'camera': self.laser_camera,
                        'filename': 'lazer-cam.webm'
                    },
                    {
                        'camera': self.back_camera,
                        'filename': 'arka-cam.webm'
                    }
                ]
                
                for recording in camera_recordings:
                    # Sadece dosya adını gönder, tam yolu değil
                    recording['camera'].start_recording(recording['filename'])
                
                # Buton metnini güncelle
                self.start_recording_btn.setText("⏹️ Kaydetmeyi Durdur")
                self.start_recording_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #f44336, stop:1 #d32f2f);
                        border: 1px solid #f44336; border-radius: 8px;
                        color: white; font-weight: 800; padding: 15px;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #d32f2f, stop:1 #f44336);
                    }
                """)
                
                QMessageBox.information(self, "Başarılı", "Tüm kameralar kaydedilmeye başlandı!")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")
        else:
            # Kaydetmeyi durdur
            try:
                self.front_camera.stop_recording()
                self.laser_camera.stop_recording()
                self.back_camera.stop_recording()
                
                # Buton metnini güncelle
                self.start_recording_btn.setText("📹 Kaydetmeyi Başlat")
                self.start_recording_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #2196F3, stop:1 #1976D2);
                        border: 1px solid #2196F3; border-radius: 8px;
                        color: white; font-weight: 800; padding: 15px;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #1976D2, stop:1 #2196F3);
                    }
                """)
                
                QMessageBox.information(self, "Başarılı", "Tüm kayıtlar durduruldu!")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme durdurma hatası: {str(e)}")

    def set_control_mode(self, mode):
        if mode == "manual":
            self.semi_auto_btn.setChecked(False)
            self.auto_btn.setChecked(False)
            self.send_to_firebase('control', {'mode': 'manual'})
        elif mode == "semi":
            self.manual_btn.setChecked(False)
            self.auto_btn.setChecked(False)
            self.send_to_firebase('control', {'mode': 'semi_auto'})
        elif mode == "auto":
            self.manual_btn.setChecked(False)
            self.semi_auto_btn.setChecked(False)
            self.send_to_firebase('control', {'mode': 'auto'})

    def toggle_laser_mode(self):
        self.laser_mode = self.laser_btn.isChecked()
        if self.laser_mode:
            self.direction_group.hide()
            self.laser_direction_group.show()
            self.laser_btn.setText("🔄 NORMAL MODA DÖN")
            self.send_to_firebase('laser_mode', {'active': True})
        else:
            self.laser_direction_group.hide()
            self.direction_group.show()
            self.laser_btn.setText("LAZER ATIŞ MODU")
            self.send_to_firebase('laser_mode', {'active': False})

    def direction_pressed(self, direction):
        if direction == 'up':
            self.send_to_firebase('movement', {'command': 'forward'})
        elif direction == 'down':
            self.send_to_firebase('movement', {'command': 'backward'})
        else:
            self.send_to_firebase('steering', {'command': direction})
        self._flash_title(f"Yön: {direction}")

    def direction_released(self, direction):
        if direction == 'up':
            self.send_to_firebase('movement', {'command': 'null'})
        elif direction == 'down':
            self.send_to_firebase('movement', {'command': 'null'})
        else:
            self.send_to_firebase('steering', {'command': 'null'})

    def throttle_pressed(self, direction):
        if direction == 'up':
            self.send_to_firebase('gas', {'command': 'increase'})
        else:
            self.send_to_firebase('gas', {'command': 'decrease'})
        self._flash_title(f"Gaz: {direction}")

    def throttle_released(self, direction):
        self.send_to_firebase('gas', {'command': 'null'})

    def gear_pressed(self, gear: str):
        mapping = {
            "1": self.gear1_btn,
            "2": self.gear2_btn,
            "B": self.gearB_btn,
            "G": self.gearG_btn,
        }
        for key, btn in mapping.items():
            btn.setChecked(key == gear)

        self.send_to_firebase('gear', {'gear': gear})
        self._flash_title(f"Vites: {gear}")

    def gear_released(self, gear: str):
        self.send_to_firebase('gear', {'gear': 'null'})

    def set_gear(self, gear: str):
        mapping = {
            "1": self.gear1_btn,
            "2": self.gear2_btn,
            "B": self.gearB_btn,
            "G": self.gearG_btn,
        }
        for key, btn in mapping.items():
            btn.setChecked(key == gear)

        self.send_to_firebase('gear', {'gear': gear})
        self._flash_title(f"Vites: {gear}")

    def _flash_title(self, text: str):
        self.setWindowTitle(f"{self._base_title} — {text}")
        QTimer.singleShot(1500, lambda: self.setWindowTitle(self._base_title))

    def laser_direction_pressed(self, direction):
        self.send_to_firebase('laser', {'command': direction})

    def laser_direction_released(self, direction):
        self.send_to_firebase('laser', {'command': 'null'})

    def laser_fire(self):
        # Space tuşu ile ateşleme
        self.send_to_firebase('laser', {'command': 'fire'})
    

    
    def laser_fire_pressed(self):
        """Mouse ile lazer ateşleme butonuna basıldığında"""
        if 'fire' not in self.pressed_keys:
            self.pressed_keys.add('fire')
            self.send_to_firebase('laser', {'command': 'fire'})
            self._highlight_laser_fire_button()
    
    def laser_fire_released(self):
        """Mouse ile lazer ateşleme butonu bırakıldığında"""
        if 'fire' in self.pressed_keys:
            self.pressed_keys.remove('fire')
            self.send_to_firebase('laser', {'command': 'null'})

    def toggle_theme(self):
        self.current_theme = "Glass" if self.current_theme == "NeoDark" else "NeoDark"
        self.apply_theme(self.current_theme)

    def closeEvent(self, event):
        self.sensor_thread.stop()
        if hasattr(self, 'firebase_thread') and self.firebase_thread is not None:
            self.firebase_thread.stop()
        self.sensor_thread.wait()
        if hasattr(self, 'firebase_thread') and self.firebase_thread is not None:
            self.firebase_thread.wait()
        
        # Dosya sunucusunu durdur
        if hasattr(self, 'file_server'):
            self.file_server.stop()
        
        event.accept()

    def cleanup_firebase_data(self):
        """Firebase'deki eski dalları temizle"""
        if not self.firebase_initialized:
            return False
            
        try:
           
            ref = db.reference('throttle')
            ref.delete()
            
            ref = db.reference('command')
            ref.delete()
            
            return True
        except Exception as e:
            return False

    def keyPressEvent(self, event: QKeyEvent):
        """Tuş basma olayını yakala"""
        key = event.key()
        
        # Klavye tekrar olaylarını filtrele
        if event.isAutoRepeat():
            event.accept()
            return
        
        if key == Qt.Key.Key_Up:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('up')
                if self.laser_mode:
                    self.laser_direction_pressed('up')
                    self._highlight_laser_button('up')
                else:
                    self.direction_pressed('up')
                    self._highlight_button('up')
        elif key == Qt.Key.Key_Left:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('left')
                if self.laser_mode:
                    self.laser_direction_pressed('left')
                    self._highlight_laser_button('left')
                else:
                    self.direction_pressed('left')
                    self._highlight_button('left')
        elif key == Qt.Key.Key_Right:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('right')
                if self.laser_mode:
                    self.laser_direction_pressed('right')
                    self._highlight_laser_button('right')
                else:
                    self.direction_pressed('right')
                    self._highlight_button('right')
        elif key == Qt.Key.Key_Down:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('down')
                if self.laser_mode:
                    self.laser_direction_pressed('down')
                    self._highlight_laser_button('down')
                else:
                    self.direction_pressed('down')
                    self._highlight_button('down')
        
        elif key == Qt.Key.Key_1:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('gear_1')
                self.gear_pressed('1')
                self._highlight_gear_button('1')
        elif key == Qt.Key.Key_2:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('gear_2')
                self.gear_pressed('2')
                self._highlight_gear_button('2')
        elif key == Qt.Key.Key_B:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('gear_B')
                self.gear_pressed('B')
                self._highlight_gear_button('B')
        elif key == Qt.Key.Key_G:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('gear_G')
                self.gear_pressed('G')
                self._highlight_gear_button('G')
        
        elif key == Qt.Key.Key_Space:
            if self.laser_mode:
                if key not in self.key_states or not self.key_states[key]:
                    self.key_states[key] = True
                    self.pressed_keys.add('fire')
                    self.send_to_firebase('laser', {'command': 'fire'})
                    self._highlight_laser_fire_button()
        
        elif key == Qt.Key.Key_L:
            self.toggle_laser_mode()
            self._highlight_laser_toggle_button()
        
        elif key == Qt.Key.Key_E:
            self.emergency_btn.click()
            self._highlight_emergency_button()
        
        elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('throttle_up')
                self.throttle_pressed('up')
                self._highlight_throttle_button('up')
        elif key == Qt.Key.Key_Minus:
            if key not in self.key_states or not self.key_states[key]:
                self.key_states[key] = True
                self.pressed_keys.add('throttle_down')
                self.throttle_pressed('down')
                self._highlight_throttle_button('down')
        

        
        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent):
        """Tuş çekme olayını yakala"""
        key = event.key()
        
        # Klavye tekrar olaylarını filtrele
        if event.isAutoRepeat():
            event.accept()
            return
        
        if key == Qt.Key.Key_Up:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('up')
                if self.laser_mode:
                    self.send_to_firebase('laser', {'command': 'null'})
                    self._unhighlight_laser_button('up')
                else:
                    self.send_to_firebase('movement', {'command': 'null'})
                    self._unhighlight_button('up')
        elif key == Qt.Key.Key_Left:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('left')
                if self.laser_mode:
                    self.send_to_firebase('laser', {'command': 'null'})
                    self._unhighlight_laser_button('left')
                else:
                    self.send_to_firebase('steering', {'command': 'null'})
                    self._unhighlight_button('left')
        elif key == Qt.Key.Key_Right:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('right')
                if self.laser_mode:
                    self.send_to_firebase('laser', {'command': 'null'})
                    self._unhighlight_laser_button('right')
                else:
                    self.send_to_firebase('steering', {'command': 'null'})
                    self._unhighlight_button('right')
        elif key == Qt.Key.Key_Down:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('down')
                if self.laser_mode:
                    self.send_to_firebase('laser', {'command': 'null'})
                    self._unhighlight_laser_button('down')
                else:
                    self.send_to_firebase('movement', {'command': 'null'})
                    self._unhighlight_button('down')
        
        elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('throttle_up')
                self.send_to_firebase('gas', {'command': 'null'})
                self._unhighlight_throttle_button('up')
        elif key == Qt.Key.Key_Minus:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('throttle_down')
                self.send_to_firebase('gas', {'command': 'null'})
                self._unhighlight_throttle_button('down')
        
        elif key == Qt.Key.Key_Space:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('fire')
                self.send_to_firebase('laser', {'command': 'null'})
                self._unhighlight_laser_fire_button()
        
        elif key == Qt.Key.Key_1:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('gear_1')
                self.gear_released('1')
                self._unhighlight_gear_button('1')
        elif key == Qt.Key.Key_2:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('gear_2')
                self.gear_released('2')
                self._unhighlight_gear_button('2')
        elif key == Qt.Key.Key_B:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('gear_B')
                self.gear_released('B')
                self._unhighlight_gear_button('B')
        elif key == Qt.Key.Key_G:
            if key in self.key_states and self.key_states[key]:
                self.key_states[key] = False
                self.pressed_keys.remove('gear_G')
                self.gear_released('G')
                self._unhighlight_gear_button('G')
        
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = IKADashboard()
    win.show()
    sys.exit(app.exec())
