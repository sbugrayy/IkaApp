#!/usr/bin/env python3
"""
Agora WebRTC Test Script
PyQt6 olmadan hızlı test için
"""

import webbrowser
import tempfile
import os

def create_test_html():
    """Test HTML sayfası oluşturur"""
    html_content = """
<!DOCTYPE html>
<html>
     <head>
         <meta charset="UTF-8">
         <meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob: mediastream: wss: ws:; connect-src 'self' https: wss: ws: data: blob:; media-src 'self' https: data: blob:;">
         <meta name="viewport" content="width=device-width, initial-scale=1.0">
         <title>Agora WebRTC Test</title>
                  <script src="https://download.agora.io/sdk/release/AgoraRTC_N-4.19.3.js"></script>
         <script>
             // getUserMedia polyfill ve güvenlik kontrolü
             if (!navigator.mediaDevices) {
                 navigator.mediaDevices = {};
             }
             
             if (!navigator.mediaDevices.getUserMedia) {
                 navigator.mediaDevices.getUserMedia = function(constraints) {
                     const getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
                     
                     if (!getUserMedia) {
                         return Promise.reject(new Error('getUserMedia desteklenmiyor'));
                     }
                     
                     return new Promise(function(resolve, reject) {
                         getUserMedia.call(navigator, constraints, resolve, reject);
                     });
                 };
             }
             
             // enumerateDevices polyfill
             if (!navigator.mediaDevices.enumerateDevices) {
                 navigator.mediaDevices.enumerateDevices = function() {
                     return Promise.resolve([]);
                 };
             }
             
             // enumerateDevices'i her zaman polyfill ile değiştir (PyQt6 için)
             navigator.mediaDevices.enumerateDevices = function() {
                 console.log('enumerateDevices polyfill kullanılıyor');
                 return Promise.resolve([]);
             };
             
             // localStorage polyfill (data: URL'ler için)
             if (window.location.protocol === 'data:' || window.location.protocol === 'file:' || !window.localStorage) {
                 window.localStorage = {
                     getItem: function() { return null; },
                     setItem: function() {},
                     removeItem: function() {},
                     clear: function() {},
                     key: function() { return null; },
                     length: 0
                 };
                 
                 window.sessionStorage = {
                     getItem: function() { return null; },
                     setItem: function() {},
                     removeItem: function() {},
                     clear: function() {},
                     key: function() { return null; },
                     length: 0
                 };
                 
                 console.log('localStorage polyfill yüklendi');
             }
         </script>
     <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #1a1a1a; 
            color: white; 
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            padding: 20px;
            background: #333;
            border-radius: 10px;
        }
        .input-group { 
            margin: 15px 0; 
        }
        .input-group label { 
            display: block; 
            margin-bottom: 5px; 
        }
        .input-group input { 
            width: 100%; 
            padding: 10px; 
            border: none; 
            border-radius: 5px; 
            background: #444; 
            color: white; 
        }
        .btn { 
            padding: 12px 24px; 
            margin: 10px 5px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px; 
        }
        .btn-primary { background: #4CAF50; color: white; }
        .btn-danger { background: #f44336; color: white; }
        .btn-warning { background: #ff9800; color: white; }
        .status { 
            padding: 15px; 
            margin: 20px 0; 
            border-radius: 5px; 
            background: #333; 
        }
        .error { background: #f44336; }
        .success { background: #4CAF50; }
        .info { background: #2196F3; }
        .video-container { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 20px; 
            justify-content: center; 
            margin: 20px 0; 
        }
        .video-item { 
            text-align: center; 
        }
        .video-item video { 
            width: 320px; 
            height: 240px; 
            background: #000; 
            border-radius: 10px; 
            border: 2px solid #444; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 Agora WebRTC Test</h1>
            <p>Hızlı test için basit arayüz</p>
        </div>
        
                 <div class="input-group">
             <label for="appId">Agora App ID:</label>
             <input type="text" id="appId" placeholder="Agora Console'dan App ID girin">
         </div>
         
         <div class="input-group">
             <label for="token">Agora Token:</label>
             <input type="text" id="token" placeholder="Agora Console'dan Token girin">
         </div>
         
         <div class="input-group">
             <label for="channel">Kanal Adı:</label>
             <input type="text" id="channel" placeholder="test_channel" value="test_channel">
         </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <button class="btn btn-primary" onclick="startStream()">Yayını Başlat</button>
            <button class="btn btn-warning" onclick="toggleAudio()">Ses Aç/Kapat</button>
            <button class="btn btn-warning" onclick="toggleVideo()">Video Aç/Kapat</button>
            <button class="btn btn-danger" onclick="stopStream()">Yayını Durdur</button>
        </div>
        
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
        
                 async function startStream() {
             if (isStreaming) {
                 updateStatus('Zaten yayın yapılıyor!', 'warning');
                 return;
             }
             
             const appId = document.getElementById('appId').value.trim();
             const token = document.getElementById('token').value.trim();
             const channel = document.getElementById('channel').value.trim();
             
             if (!appId) {
                 updateStatus('❌ Lütfen Agora App ID girin!', 'error');
                 return;
             }
             
             if (!token) {
                 updateStatus('❌ Lütfen Agora Token girin!', 'error');
                 return;
             }
             
             if (!channel) {
                 updateStatus('❌ Lütfen kanal adı girin!', 'error');
                 return;
             }
            
            try {
                updateStatus('Agora istemcisi başlatılıyor...', 'info');
                
                                 agoraClient = AgoraRTC.createClient({ 
                     mode: "rtc", 
                     codec: "vp8",
                     role: "host"
                 });
                 
                 // Hata yakalama ekle
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
                 
                 try {
                     // getUserMedia için güvenlik kontrolü
                     if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                         throw new Error('getUserMedia desteklenmiyor. HTTPS veya localhost gerekli.');
                     }
                     
                     [localAudioTrack, localVideoTrack] = await AgoraRTC.createMicrophoneAndCameraTracks();
                 } catch (mediaError) {
                     console.error('Medya erişim hatası:', mediaError);
                     updateStatus('❌ Kamera/Mikrofon erişimi hatası: ' + mediaError.message, 'error');
                     return;
                 }
                
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
            updateStatus('Sayfa yüklendi. App ID ve kanal adını girin, sonra "Yayını Başlat" butonuna tıklayın.', 'info');
        };
    </script>
</body>
</html>
    """
    
    # Geçici HTML dosyası oluştur
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        return f.name

def main():
    """Test sayfasını tarayıcıda açar"""
    print("🎥 Agora WebRTC Test Sayfası Oluşturuluyor...")
    
    html_file = create_test_html()
    print(f"✅ Test sayfası oluşturuldu: {html_file}")
    
    # Tarayıcıda aç
    print("🌐 Tarayıcıda açılıyor...")
    webbrowser.open(f'file://{os.path.abspath(html_file)}')
    
    print("\n📋 Test Adımları:")
    print("1. Agora Console'dan App ID alın: https://console.agora.io/")
    print("2. Agora Console'dan Token oluşturun: Security > Token Generator")
    print("3. App ID ve Token'ı girin")
    print("4. Kanal adını belirleyin")
    print("5. 'Yayını Başlat' butonuna tıklayın")
    print("6. Kamera ve mikrofon izinlerini verin")
    print("\n🔗 Mobil test için: https://webdemo.agora.io/")
    print("   Aynı App ID, Token ve kanal adını kullanın")
    
    input("\nTest tamamlandıktan sonra Enter'a basın...")
    
    # Geçici dosyayı sil
    try:
        os.unlink(html_file)
        print("✅ Test dosyası temizlendi")
    except:
        pass

if __name__ == "__main__":
    main()
