# 🎥 Agora WebRTC Video Streaming Uygulaması

Bu uygulama PyQt6 ve QWebEngineView kullanarak Agora WebRTC ile video streaming yapmanızı sağlar.

## ✨ Özellikler

- 🎬 **Gerçek zamanlı video streaming**
- 🎤 **Ses ve video kontrolü**
- 🔄 **Otomatik kamera/mikrofon izinleri**
- 📱 **Modern ve kullanıcı dostu arayüz**
- 📊 **Detaylı log sistemi**
- 🌐 **Agora'nın güvenilir WebRTC altyapısı**
- 🌍 **Farklı Wi-Fi ağları üzerinden çalışma**
- 🔧 **TURN sunucu desteği**

## 🚀 Kurulum

### 1. Gereksinimler

- Python 3.8+
- Windows 10/11 (PyQt6-WebEngine Windows'ta daha stabil)
- Kamera ve mikrofon

### 2. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 3. Agora Hesabı Oluşturun

1. [Agora Console](https://console.agora.io/) adresine gidin
2. Ücretsiz hesap oluşturun
3. Yeni bir proje oluşturun
4. **App ID**'yi kopyalayın
5. **Token** oluşturun (Security > Token Generator)

## 🎯 Kullanım

### 1. Uygulamayı Başlatın

```bash
cd demo3
python main.py
```

### 2. Agora Bilgilerini Girin

- **App ID**: Agora Console'dan aldığınız App ID'yi yapıştırın
- **Token**: Agora Console'dan oluşturduğunuz Token'ı yapıştırın
- **Kanal Adı**: Belirleyin (örn: "test_channel")

### 3. Yayını Başlatın

- **"Başlat"** butonuna tıklayın
- Kamera ve mikrofon izinlerini verin
- **"Yayını Başlat"** butonuna tıklayın

### 4. Video Kontrolleri

- 🎤 **Ses Aç/Kapat**: Mikrofonu açıp kapatır
- 📹 **Video Aç/Kapat**: Kamerayı açıp kapatır
- 🛑 **Yayını Durdur**: Yayını sonlandırır

## 🔧 Test Etme

### Tek Kullanıcı Testi

1. Uygulamayı başlatın
2. App ID ve kanal adını girin
3. "Başlat" → "Yayını Başlat"
4. Yerel videonuzu görün

### İki Kullanıcı Testi

1. **İlk kullanıcı**: Uygulamayı başlat, App ID ve kanal adını gir, yayını başlat
2. **İkinci kullanıcı**: Aynı App ID ve kanal adını kullan, yayını başlat
3. Her iki kullanıcı da birbirinin video ve sesini görecek

### Farklı Cihazlarda Test

- **PC'de**: Python uygulaması
- **Mobilde**: Web tarayıcı ile [Agora WebRTC Demo](https://webdemo.agora.io/) kullanın
- **Farklı Wi-Fi'ler**: TURN sunucu sayesinde farklı ağlardan bağlanabilir
- Aynı App ID, Token ve kanal adını kullanın

## 📱 Mobil Test

Mobil cihazlarda test etmek için:

1. Agora WebRTC Demo sayfasını açın: https://webdemo.agora.io/
2. App ID'nizi girin
3. Token'ınızı girin
4. Aynı kanal adını kullanın
5. PC'deki uygulama ile bağlantı kurun

## 🛠️ Sorun Giderme

### Kamera/Mikrofon Erişimi Yok

- Tarayıcı izinlerini kontrol edin
- Windows kamera/mikrofon izinlerini kontrol edin
- Uygulama loglarını inceleyin

### Bağlantı Hatası

- App ID'nin doğru olduğundan emin olun
- İnternet bağlantınızı kontrol edin
- Agora Console'da proje durumunu kontrol edin

### Video Görünmüyor

- Kamera izinlerini kontrol edin
- Başka uygulamaların kamerayı kullanmadığından emin olun
- Log mesajlarını kontrol edin

### getUserMedia Hatası

- **"can not find getUserMedia"**: Bu hata genellikle güvenlik politikaları nedeniyle oluşur
- **Çözümler**:
  - Uygulamayı localhost'ta çalıştırın
  - Windows Defender veya antivirüs yazılımını geçici olarak devre dışı bırakın
  - Kamera ve mikrofon izinlerini Windows ayarlarından kontrol edin
  - Uygulamayı yönetici olarak çalıştırın
  - **PyQt6 WebEngine**: Güçlendirilmiş polyfill eklendi
  - **Debug**: Konsol loglarını kontrol edin

### WebSocket Bağlantı Hatası

- **"Refused to connect to wss://..."**: Content Security Policy nedeniyle WebSocket bağlantıları engelleniyor
- **Çözümler**:
  - Uygulamayı yeniden başlatın (CSP güncellendi)
  - Tarayıcıda sayfayı yenileyin
  - Konsol hatalarını kontrol edin

### localStorage Hatası

- **"Storage is disabled inside 'data:' URLs"**: PyQt6 WebEngine'de data URL'lerde storage erişimi yok
- **Çözümler**:
  - localStorage polyfill eklendi
  - Uygulamayı yeniden başlatın
  - Alternatif olarak test script'ini kullanın

## 🔒 Güvenlik

- App ID'nizi paylaşmayın
- Production'da token authentication kullanın
- Güvenli HTTPS bağlantıları kullanın

## 📚 API Referansı

- [Agora WebRTC SDK](https://docs.agora.io/en/Video/API%20Reference/web/index.html)
- [Agora Console](https://console.agora.io/)
- [WebRTC Standartları](https://webrtc.org/)

## 🆘 Destek

- Agora Dokümantasyonu: https://docs.agora.io/
- Agora Forum: https://www.agora.io/en/community/
- GitHub Issues: Proje sayfasında issue açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

---

**Not**: Bu uygulama demo amaçlıdır. Production kullanımı için ek güvenlik önlemleri alın.
