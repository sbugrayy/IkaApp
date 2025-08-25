#!/usr/bin/env python3
"""
Agora WebRTC PyQt6 Çoklu Kamera Uygulaması
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
import json

# Logging ayarları
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('AgoraMultiCam')
logger.setLevel(logging.INFO)

class AgoraMultiCamApp(QMainWindow):
    def __init__(self, is_sender=True):
        super().__init__()
        self.is_sender = is_sender
        self.setWindowTitle("Agora WebRTC Çoklu Kamera" + (" - Gönderici" if is_sender else " - Alıcı"))
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
        
        if self.is_sender:
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
                font-family: Arial, sans-serif;
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
                margin: 10px;
            }
            .video-item video { 
                width: 320px; 
                height: 240px; 
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
            
            let isStreaming = false;
            
            function updateStatus(message, type = 'info') {
                const statusEl = document.getElementById('status');
                statusEl.textContent = message;
                statusEl.className = 'status ' + type;
                console.log(message);
            }
            
            async function startStream(appId, token, channel, isSender = true) {
                if (isStreaming) {
                    updateStatus('Zaten yayın yapılıyor!', 'warning');
                    return;
                }
                
                try {
                    options.appId = appId;
                    options.token = token;
                    options.channel = channel;
                    
                    updateStatus('Agora istemcisi başlatılıyor...', 'info');
                    
                    rtc.client = AgoraRTC.createClient({ 
                        mode: "rtc", 
                        codec: "vp8",
                        role: isSender ? "host" : "audience"
                    });
                    
                    rtc.client.on("error", (error) => {
                        console.error('Agora istemci hatası:', error);
                        updateStatus('❌ Agora hatası: ' + error.message, 'error');
                    });
                    
                    rtc.client.on("connection-state-change", (curState, prevState, reason) => {
                        console.log('Bağlantı durumu:', prevState, '->', curState, 'Neden:', reason);
                        updateStatus('Bağlantı: ' + curState, 'info');
                    });
                    
                    rtc.client.on("user-published", async (user, mediaType) => {
                        try {
                            await rtc.client.subscribe(user, mediaType);
                            console.log("Kullanıcıya abone olundu:", user.uid, mediaType);
                            
                            if (mediaType === "video") {
                                const container = document.createElement('div');
                                container.className = 'video-item';
                                container.innerHTML = `<h3>Uzak Kamera ${Object.keys(rtc.remoteUsers).length + 1}</h3>`;
                                
                                const videoElement = document.createElement('div');
                                videoElement.id = `remote-${user.uid}`;
                                container.appendChild(videoElement);
                                
                                document.getElementById('videos').appendChild(container);
                                user.videoTrack.play(`remote-${user.uid}`);
                                
                                rtc.remoteUsers[user.uid] = user;
                                updateStatus('Uzak video eklendi', 'success');
                            }
                            if (mediaType === "audio") {
                                user.audioTrack.play();
                                updateStatus('Uzak ses eklendi', 'success');
                            }
                        } catch (err) {
                            console.error("Abone olma hatası:", err);
                            updateStatus('❌ Abone olma hatası: ' + err.message, 'error');
                        }
                    });

                    rtc.client.on("user-unpublished", (user) => {
                        const container = document.getElementById(`remote-${user.uid}`);
                        if (container) {
                            container.parentElement.remove();
                        }
                        delete rtc.remoteUsers[user.uid];
                        updateStatus(`Uzak kullanıcı yayın durdurdu: ${user.uid}`, 'info');
                    });
                    
                    updateStatus('Kanala katılım yapılıyor...', 'info');
                    await rtc.client.join(options.appId, options.channel, options.token || null);
                    
                    if (isSender) {
                        updateStatus('Kameralar başlatılıyor...', 'info');
                        
                        // Önce ses track'i oluştur
                        rtc.localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack();
                        await rtc.client.publish([rtc.localAudioTrack]);
                        
                        // Her kamera için ayrı bir video track oluştur
                        for (let i = 0; i < 3; i++) {
                            try {
                                const videoTrack = await AgoraRTC.createCameraVideoTrack({
                                    encoderConfig: {
                                        width: 640,
                                        height: 480,
                                        frameRate: 15,
                                        bitrateMin: 600,
                                        bitrateMax: 1000
                                    }
                                });
                                
                                rtc.localVideoTracks.push(videoTrack);
                                
                                const container = document.createElement('div');
                                container.className = 'video-item';
                                container.innerHTML = `<h3>Yerel Kamera ${i + 1}</h3>`;
                                
                                const videoElement = document.createElement('div');
                                videoElement.id = `local-${i}`;
                                container.appendChild(videoElement);
                                
                                document.getElementById('videos').appendChild(container);
                                videoTrack.play(`local-${i}`);
                                
                                await rtc.client.publish([videoTrack]);
                                updateStatus(`Kamera ${i + 1} yayını başarılı`, 'success');
                            } catch (err) {
                                console.error(`Kamera ${i + 1} hatası:`, err);
                                updateStatus(`❌ Kamera ${i + 1} hatası: ${err.message}`, 'error');
                            }
                        }
                    }
                    
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
                    
                    if (rtc.localAudioTrack) {
                        rtc.localAudioTrack.close();
                        rtc.localAudioTrack = null;
                    }
                    
                    for (const track of rtc.localVideoTracks) {
                        track.close();
                    }
                    rtc.localVideoTracks = [];
                    
                    await rtc.client.leave();
                    
                    document.getElementById('videos').innerHTML = '';
                    
                    isStreaming = false;
                    updateStatus('✅ Yayın durduruldu.', 'success');
                    
                } catch (error) {
                    console.error('Hata:', error);
                    updateStatus('❌ Hata: ' + error.message, 'error');
                }
            }
            
            function toggleAudio() {
                if (rtc.localAudioTrack) {
                    rtc.localAudioTrack.setEnabled(!rtc.localAudioTrack.enabled);
                    updateStatus(
                        rtc.localAudioTrack.enabled ? '🔊 Ses açıldı' : '🔇 Ses kapatıldı',
                        rtc.localAudioTrack.enabled ? 'success' : 'warning'
                    );
                }
            }
            
            function toggleVideo() {
                for (const track of rtc.localVideoTracks) {
                    track.setEnabled(!track.enabled);
                }
                updateStatus(
                    rtc.localVideoTracks[0]?.enabled ? '📹 Video açıldı' : '📹 Video kapatıldı',
                    rtc.localVideoTracks[0]?.enabled ? 'success' : 'warning'
                );
            }
            
            window.onload = function() {
                updateStatus('Sayfa yüklendi ve hazır.', 'info');
            };
            
            // PyQt6 ile iletişim için global fonksiyonlar
            window.startStreamFromQt = function(appId, token, channel, isSender) {
                console.log("startStreamFromQt çağrıldı:", { appId, token, channel, isSender });
                startStream(appId, token, channel, isSender === "true");
            };
            
            window.stopStreamFromQt = function() {
                console.log("stopStreamFromQt çağrıldı");
                stopStream();
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
                # Sadece önemli mesajları göster
                if "error" in message.lower() or "warning" in message.lower():
                    logger.warning(f"JS [L{line}] {message}")
                elif "success" in message.lower():
                    logger.info(f"JS [L{line}] {message}")
                
            def handlePermissionRequest(self, url, feature):
                if feature in [QWebEnginePage.Feature.MediaAudioCapture,
                             QWebEnginePage.Feature.MediaVideoCapture,
                             QWebEnginePage.Feature.MediaAudioVideoCapture]:
                    self.setFeaturePermission(
                        url,
                        feature,
                        QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
                    )
                    logger.info(f"Medya izni verildi: {feature}")
        
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
            logger.info("Sayfa başarıyla yüklendi")
    
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
                        logger.warning("Yayın zaten aktif")
                        QMessageBox.warning(self, "Uyarı", "Yayın zaten aktif durumda!")
                        return
                    
                # JavaScript fonksiyonunu çağır
                js_code = f"startStreamFromQt('{app_id}', '{token}', '{channel}', {str(self.is_sender).lower()})"
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
            logger.info(f"Yayın başlatma yanıtı: {result}")
            if isinstance(result, str) and "error" in result.lower():
                QMessageBox.warning(self, "Hata", f"Yayın başlatılamadı: {result}")
                self.start_button.setText("Yayını Başlat")
                self.start_button.setStyleSheet("")
    
    def handle_stream_stop(self, result):
        """Yayın durdurma yanıtını işler"""
        if result:
            logger.info(f"Yayın durdurma yanıtı: {result}")
            if isinstance(result, str) and "error" in result.lower():
                QMessageBox.warning(self, "Hata", f"Yayın durdurulamadı: {result}")
                self.start_button.setText("Yayını Durdur")
                self.start_button.setStyleSheet("background-color: #f44336; color: white;")
    
    def closeEvent(self, event):
        """Uygulama kapatılırken geçici dosyaları temizle"""
        try:
            os.unlink(self.html_file)
        except:
            pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Komut satırı argümanlarını kontrol et
    is_sender = len(sys.argv) < 2 or sys.argv[1].lower() != 'receiver'
    
    window = AgoraMultiCamApp(is_sender=is_sender)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()