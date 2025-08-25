#!/usr/bin/env python3
"""
Agora WebRTC PyQt6 Uygulaması
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
import tempfile
import logging

# Logging ayarları
logging.basicConfig(level=logging.DEBUG)

class AgoraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agora WebRTC Uygulaması")
        self.setMinimumSize(1200, 800)
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Giriş formu
        self.create_login_form()
        main_layout.addWidget(self.login_group)
        
        # Video konteyner
        self.create_video_container()
        main_layout.addWidget(self.video_group)
        
        # Kontrol butonları
        self.create_control_buttons()
        main_layout.addWidget(self.control_group)
        
        # WebView için HTML oluştur
        self.html_file = self.create_webview_html()
        
        # WebView ayarları
        self.setup_webview()
        
        self.show()
    
    def create_login_form(self):
        """Giriş formu oluşturur"""
        self.login_group = QGroupBox("Agora Bağlantı Bilgileri")
        layout = QVBoxLayout()
        
        # App ID
        app_id_layout = QHBoxLayout()
        app_id_label = QLabel("App ID:")
        self.app_id_input = QLineEdit()
        app_id_layout.addWidget(app_id_label)
        app_id_layout.addWidget(self.app_id_input)
        layout.addLayout(app_id_layout)
        
        # Token
        token_layout = QHBoxLayout()
        token_label = QLabel("Token:")
        self.token_input = QLineEdit()
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)
        
        # Kanal
        channel_layout = QHBoxLayout()
        channel_label = QLabel("Kanal:")
        self.channel_input = QLineEdit()
        self.channel_input.setText("test_channel")
        channel_layout.addWidget(channel_label)
        channel_layout.addWidget(self.channel_input)
        layout.addLayout(channel_layout)
        
        self.login_group.setLayout(layout)
    
    def create_video_container(self):
        """Video konteyner oluşturur"""
        self.video_group = QGroupBox("Video Görüntüleme")
        layout = QHBoxLayout()
        
        # WebView widget'ı
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)
        
        self.video_group.setLayout(layout)
    
    def create_control_buttons(self):
        """Kontrol butonları oluşturur"""
        self.control_group = QGroupBox("Kontroller")
        layout = QHBoxLayout()
        
        # Yayın başlat/durdur
        self.start_button = QPushButton("Yayını Başlat")
        self.start_button.clicked.connect(self.toggle_stream)
        layout.addWidget(self.start_button)
        
        # Ses kontrolü
        self.audio_button = QPushButton("Ses Aç/Kapat")
        self.audio_button.clicked.connect(lambda: self.webview.page().runJavaScript("toggleAudio()"))
        layout.addWidget(self.audio_button)
        
        # Video kontrolü
        self.video_button = QPushButton("Video Aç/Kapat")
        self.video_button.clicked.connect(lambda: self.webview.page().runJavaScript("toggleVideo()"))
        layout.addWidget(self.video_button)
        
        self.control_group.setLayout(layout)
    
    def create_webview_html(self):
        """WebView için HTML içeriği oluşturur"""
        html_content = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="Content-Security-Policy" content="default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; connect-src * 'unsafe-inline'; media-src * blob:;">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agora WebRTC</title>
        <script src="https://download.agora.io/sdk/release/AgoraRTC_N-4.19.3.js"></script>
        <style>
            body { 
                margin: 0; 
                background: #1a1a1a; 
                color: white; 
            }
            .video-container { 
                display: flex; 
                flex-wrap: wrap; 
                gap: 20px; 
                justify-content: center; 
                padding: 20px; 
            }
            .video-item { 
                text-align: center; 
            }
            .video-item video { 
                width: 480px; 
                height: 360px; 
                background: #000; 
                border-radius: 10px; 
                border: 2px solid #444; 
            }
            .status { 
                padding: 15px; 
                margin: 20px; 
                border-radius: 5px; 
                background: #333; 
                text-align: center;
            }
            .error { background: #f44336; }
            .success { background: #4CAF50; }
            .info { background: #2196F3; }
        </style>
    </head>
    <body>
        <div class="status" id="status">Hazırlanıyor...</div>
        <div class="video-container">
            <div class="video-item">
                <h3>Yerel Video</h3>
                <video id="localVideo" autoplay muted></video>
            </div>
            <div class="video-item">
                <h3>Uzak Video</h3>
                <video id="remoteVideo" autoplay></video>
            </div>
        </div>
        
        <script>
            let agoraClient = null;
            let localAudioTrack = null;
            let localVideoTrack = null;
            let isStreaming = false;
            
            function updateStatus(message, type = 'info') {
                const statusEl = document.getElementById('status');
                statusEl.textContent = message;
                statusEl.className = 'status ' + type;
                console.log(message);
            }
            
            async function startStream(appId, token, channel) {
                if (isStreaming) {
                    updateStatus('Zaten yayın yapılıyor!', 'warning');
                    return;
                }
                
                try {
                    updateStatus('Agora istemcisi başlatılıyor...', 'info');
                    
                    agoraClient = AgoraRTC.createClient({ 
                        mode: "rtc", 
                        codec: "vp8",
                        role: "host"
                    });
                    
                    agoraClient.on("error", (error) => {
                        console.error('Agora istemci hatası:', error);
                        updateStatus('❌ Agora hatası: ' + error.message, 'error');
                    });
                    
                    agoraClient.on("connection-state-change", (curState, prevState, reason) => {
                        console.log('Bağlantı durumu:', prevState, '->', curState, 'Neden:', reason);
                        updateStatus('Bağlantı: ' + curState, 'info');
                    });
                    
                    agoraClient.on("user-published", handleUserPublished);
                    agoraClient.on("user-unpublished", handleUserUnpublished);
                    
                    updateStatus('Kanala katılım yapılıyor...', 'info');
                    await agoraClient.join(appId, channel, token, null);
                    
                    updateStatus('Kamera ve mikrofon erişimi isteniyor...', 'info');
                    [localAudioTrack, localVideoTrack] = await AgoraRTC.createMicrophoneAndCameraTracks();
                    
                    localVideoTrack.play("localVideo");
                    
                    updateStatus('Medya akışları yayınlanıyor...', 'info');
                    await agoraClient.publish([localAudioTrack, localVideoTrack]);
                    
                    isStreaming = true;
                    updateStatus('✅ Yayın başarıyla başlatıldı!', 'success');
                    
                } catch (error) {
                    console.error('Hata:', error);
                    updateStatus('❌ Hata: ' + error.message, 'error');
                }
            }
            
            async function stopStream() {
                if (!isStreaming) {
                    updateStatus('Zaten yayın yapılmıyor!', 'warning');
                    return;
                }
                
                try {
                    updateStatus('Yayın durduruluyor...', 'info');
                    
                    if (localAudioTrack) {
                        localAudioTrack.close();
                        localAudioTrack = null;
                    }
                    if (localVideoTrack) {
                        localVideoTrack.close();
                        localVideoTrack = null;
                    }
                    
                    if (agoraClient) {
                        await agoraClient.leave();
                        agoraClient = null;
                    }
                    
                    document.getElementById('localVideo').srcObject = null;
                    document.getElementById('remoteVideo').srcObject = null;
                    
                    isStreaming = false;
                    updateStatus('✅ Yayın durduruldu.', 'success');
                    
                } catch (error) {
                    console.error('Hata:', error);
                    updateStatus('❌ Hata: ' + error.message, 'error');
                }
            }
            
            function toggleAudio() {
                if (localAudioTrack) {
                    if (localAudioTrack.enabled) {
                        localAudioTrack.setEnabled(false);
                        updateStatus('🔇 Ses kapatıldı', 'warning');
                    } else {
                        localAudioTrack.setEnabled(true);
                        updateStatus('🔊 Ses açıldı', 'success');
                    }
                }
            }
            
            function toggleVideo() {
                if (localVideoTrack) {
                    if (localVideoTrack.enabled) {
                        localVideoTrack.setEnabled(false);
                        updateStatus('📹 Video kapatıldı', 'warning');
                    } else {
                        localVideoTrack.setEnabled(true);
                        updateStatus('📹 Video açıldı', 'success');
                    }
                }
            }
            
            async function handleUserPublished(user, mediaType) {
                updateStatus('Uzak kullanıcı yayın başlattı: ' + user.uid, 'info');
                
                await agoraClient.subscribe(user, mediaType);
                
                if (mediaType === 'video') {
                    user.videoTrack.play("remoteVideo");
                    updateStatus('Uzak video eklendi', 'success');
                }
                if (mediaType === 'audio') {
                    user.audioTrack.play();
                    updateStatus('Uzak ses eklendi', 'success');
                }
            }
            
            function handleUserUnpublished(user) {
                updateStatus('Uzak kullanıcı yayın durdurdu: ' + user.uid, 'info');
            }
            
            window.onload = function() {
                updateStatus('Sayfa yüklendi ve hazır.', 'info');
            };
        </script>
    </body>
</html>
        """
        
        # Geçici HTML dosyası oluştur
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            return f.name
    
    def setup_webview(self):
        """WebView ayarlarını yapılandırır"""
        # WebEngine ayarları
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
        
        # JavaScript hata ayıklama
        self.webview.page().loadFinished.connect(self.on_page_loaded)
        
        # HTML dosyasını yükle
        self.webview.setUrl(QUrl.fromLocalFile(self.html_file))
    
    def on_page_loaded(self, ok):
        """Sayfa yüklendiğinde çağrılır"""
        if ok:
            logging.debug("Sayfa başarıyla yüklendi")
            # JavaScript konsol mesajlarını görüntüle
            self.webview.page().runJavaScript(
                "console.log = function(message) { console.debug(message); };"
            )
    
    def toggle_stream(self):
        """Yayını başlatır/durdurur"""
        if self.start_button.text() == "Yayını Başlat":
            # Giriş bilgilerini kontrol et
            app_id = self.app_id_input.text().strip()
            token = self.token_input.text().strip()
            channel = self.channel_input.text().strip()
            
            if not app_id or not token or not channel:
                QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun!")
                return
            
            def check_stream_status(result):
                if result and isinstance(result, bool):
                    if result:
                        logging.debug("Yayın zaten aktif")
                        QMessageBox.warning(self, "Uyarı", "Yayın zaten aktif durumda!")
                        return
                    
                # JavaScript fonksiyonunu çağır
                js_code = f"startStream('{app_id}', '{token}', '{channel}')"
                self.webview.page().runJavaScript(js_code, self.handle_stream_start)
            
            # Önce yayın durumunu kontrol et
            self.webview.page().runJavaScript("isStreaming", check_stream_status)
            
            self.start_button.setText("Yayını Durdur")
            self.start_button.setStyleSheet("background-color: #f44336; color: white;")
        else:
            # Yayını durdur
            self.webview.page().runJavaScript("stopStream()", self.handle_stream_stop)
            
            self.start_button.setText("Yayını Başlat")
            self.start_button.setStyleSheet("")
    
    def handle_stream_start(self, result):
        """Yayın başlatma yanıtını işler"""
        if result:
            logging.debug(f"Yayın başlatma yanıtı: {result}")
            if isinstance(result, str) and "error" in result.lower():
                QMessageBox.warning(self, "Hata", f"Yayın başlatılamadı: {result}")
                self.start_button.setText("Yayını Başlat")
                self.start_button.setStyleSheet("")
    
    def handle_stream_stop(self, result):
        """Yayın durdurma yanıtını işler"""
        if result:
            logging.debug(f"Yayın durdurma yanıtı: {result}")
            if isinstance(result, str) and "error" in result.lower():
                QMessageBox.warning(self, "Hata", f"Yayın durdurulamadı: {result}")
                self.start_button.setText("Yayını Durdur")
                self.start_button.setStyleSheet("background-color: #f44336; color: white;")
    
    def handle_js_response(self, result):
        """JavaScript yanıtlarını işler"""
        if result:
            logging.debug(f"JavaScript yanıtı: {result}")
    
    def closeEvent(self, event):
        """Uygulama kapatılırken geçici dosyaları temizle"""
        try:
            os.unlink(self.html_file)
        except:
            pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = AgoraApp()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
