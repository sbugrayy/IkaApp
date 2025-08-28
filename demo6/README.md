# 🚗 IKA Multi-Camera System

Agora WebRTC ile çoklu kamera sistemi - PyQt6 tabanlı alıcı uygulaması.

## 📁 Dosya Yapısı

```
demo6/
├── ika-app.py              # Ana PyQt6 uygulaması (alıcı)
├── multi_camera_sender.html # Web tabanlı gönderici
├── file_server.py          # HTTP dosya kaydetme sunucusu
├── test_multi_camera.py    # Test scripti
├── config.env              # Agora kimlik bilgileri
├── requirements.txt        # Python bağımlılıkları
├── recordings/             # Kayıt dosyaları klasörü
└── README.md              # Bu dosya
```

## 🚀 Kurulum

### 1. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 2. Agora Kimlik Bilgilerini Ayarlayın
`config.env` dosyasını düzenleyin:
```env
AGORA_APP_ID=your_app_id_here
AGORA_TOKEN=your_token_here
```

## 🎯 Kullanım

### Alıcı Uygulaması (ika-app.py)
```bash
python ika-app.py
```

**Özellikler:**
- 🎥 3 kamera görüntüsü (Ön, Lazer, Arka)
- 📹 Kayıt sistemi (recordings klasörüne)
- 🎮 Manuel kontrol sistemi
- 📊 Sensör verileri
- 🔥 Firebase entegrasyonu

### Gönderici Web Uygulaması
```bash
python test_multi_camera.py
```

**Özellikler:**
- 📱 Mobil uyumlu
- 🎥 3 kamera desteği
- 🔐 Güvenli token sistemi
- 🌐 Web tabanlı

## 📹 Kayıt Sistemi

### Otomatik Kayıt
- **"🎥 Yayını Başlat"** butonuna basın
- **"📹 Kaydetmeyi Başlat"** butonuna basın
- Kayıtlar `recordings/` klasörüne kaydedilir:
  - `on-cam.webm` - Ön kamera
  - `lazer-cam.webm` - Lazer kamera  
  - `arka-cam.webm` - Arka kamera

### HTTP Sunucu Sistemi
- Port 8080'de çalışır
- Base64 encoding ile güvenli transfer
- CORS desteği
- Otomatik başlatma/durdurma

## 🎮 Kontrol Sistemi

### Manuel Kontrol
- **Yön Tuşları**: Hareket kontrolü
- **1, 2, B, G**: Vites kontrolü
- **L**: Lazer modu
- **M**: Manuel mod

### Otomatik Modlar
- **Manuel**: Tam kontrol
- **Yarı Otomatik**: Yardımlı kontrol
- **Otomatik**: Tam otomasyon

## 🔧 Teknik Detaylar

### Agora WebRTC
- **SDK**: AgoraRTC_N-4.19.3.js
- **Protokol**: WebRTC
- **Format**: WebM (VP9 codec)
- **Çözünürlük**: 1440x900 optimize

### PyQt6 Entegrasyonu
- **QWebEngineView**: Video görüntüleme
- **QWebEnginePage**: JavaScript entegrasyonu
- **Thread-safe**: Güvenli çoklu işlem
- **Event-driven**: Olay tabanlı mimari

### Firebase Entegrasyonu
- **Real-time Database**: Sensör verileri
- **Authentication**: Güvenli erişim
- **Cloud Functions**: Otomatik işlemler

## 🐛 Sorun Giderme

### Yayın Bağlantı Sorunu
```bash
# Token kontrolü
python test_multi_camera.py
```

### Kayıt Sorunu
```bash
# HTTP sunucu kontrolü
netstat -an | findstr 8080
```

### Firebase Sorunu
```bash
# Firebase bağlantı testi
python -c "import firebase_admin; print('Firebase OK')"
```

## 📝 Lisans

MIT License - Özgür kullanım.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun
3. Commit yapın
4. Push yapın
5. Pull Request açın

---

**🎉 Başarılı kullanımlar!**
