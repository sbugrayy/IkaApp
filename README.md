# 🚗 İKA - İnsansız Kara Aracı

**Agora WebRTC ile Çoklu Kamera Sistemi ve PyQt6 Tabanlı Kontrol Arayüzü**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)](https://pypi.org/project/PyQt6/)
[![Agora](https://img.shields.io/badge/Agora-WebRTC-orange.svg)](https://www.agora.io/)
[![Firebase](https://img.shields.io/badge/Firebase-Realtime-red.svg)](https://firebase.google.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 İçindekiler

- [🎯 Proje Hakkında](#-proje-hakkında)
- [🚀 Özellikler](#-özellikler)
- [📁 Proje Yapısı](#-proje-yapısı)
- [🛠️ Kurulum](#️-kurulum)
- [🎮 Kullanım](#-kullanım)
- [📹 Kayıt Sistemi](#-kayıt-sistemi)
- [🔧 Teknik Detaylar](#-teknik-detaylar)
- [🐛 Sorun Giderme](#-sorun-giderme)
- [📝 Lisans](#-lisans)

## 🎯 Proje Hakkında

**İKA (İnsansız Kara Aracı)**, TEKNOFEST yarışması için geliştirilmiş gelişmiş bir kontrol ve izleme sistemidir. Agora WebRTC teknolojisi kullanarak çoklu kamera desteği, PyQt6 ile modern kullanıcı arayüzü ve Firebase ile gerçek zamanlı veri yönetimi sağlar.

### 🎯 Ana Hedefler
- **Çoklu Kamera İzleme**: 3 farklı açıdan eş zamanlı görüntü
- **Gerçek Zamanlı Kontrol**: Manuel, yarı otomatik ve tam otomatik modlar
- **Veri Kaydı**: Sensör verileri ve video kayıtları
- **Mobil Uyumluluk**: Web tabanlı gönderici uygulaması

## 🚀 Özellikler

### 🎥 **Çoklu Kamera Sistemi**
- **Ön Kamera**: Sürüş görüntüsü ve yol takibi
- **Lazer Kamera**: Hedef vurma ve nişan alma
- **Arka Kamera**: Geri görüş ve takip sistemi
- **Ayrı UID'ler**: Her kamera için benzersiz kimlik
- **Ayrı Kanallar**: Bağımsız yayın kanalları

### 🎮 **Kontrol Sistemi**
- **Manuel Kontrol**: Tam kullanıcı kontrolü
- **Yarı Otomatik**: Yardımlı sürüş sistemi
- **Tam Otomatik**: Otonom sürüş modu
- **Vites Kontrolü**: 1, 2, B, G vites seçenekleri
- **Lazer Modu**: Hedef vurma sistemi

### 📊 **Veri Yönetimi**
- **Firebase Entegrasyonu**: Gerçek zamanlı veri senkronizasyonu
- **Sensör Verileri**: Hız, sıcaklık, basınç takibi
- **Kayıt Sistemi**: Video ve veri kaydı
- **Analitik**: Performans analizi

### 🔐 **Güvenlik**
- **Environment Variables**: Güvenli kimlik bilgisi yönetimi
- **Token Sistemi**: Agora güvenlik tokenları
- **CORS Desteği**: Web güvenliği
- **Hata Yönetimi**: Güvenli hata yakalama

## 📁 Proje Yapısı

```
IkaApp/
├── 📄 ika-app.py                   # Ana PyQt6 uygulaması (alıcı)
├── 🌐 multi_camera_sender.html     # Web tabanlı gönderici
├── 🔧 file_server.py               # HTTP dosya kaydetme sunucusu
├── 🧪 test_multi_camera.py         # Test ve başlatma scripti
├── ⚙️ config.env                   # Agora kimlik bilgileri
├── 📦 requirements.txt             # Python bağımlılıkları
├── 📁 recordings/                  # Video kayıtları klasörü
├── 🔥 ika-db.json                  # Firebase kimlik bilgileri
├── 📋 .gitignore                   # Git ignore kuralları
├── 📄 LICENSE                      # MIT Lisansı
└── 📖 README.md                    # Bu dosya
```

## 🛠️ Kurulum

### 1. **Sistem Gereksinimleri**
- **Python**: 3.8 veya üzeri
- **PyQt6**: GUI framework
- **Agora Hesabı**: WebRTC servisi
- **Firebase Projesi**: Veri yönetimi

### 2. **Bağımlılıkları Yükleyin**
```bash
# Repository'yi klonlayın
git clone https://github.com/sbugrayy/IkaApp.git
cd IkaApp

# Virtual environment oluşturun (önerilen)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# veya
.venv\Scripts\activate     # Windows

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3. **Agora Kimlik Bilgilerini Ayarlayın**
`config.env` dosyasını düzenleyin:
```env
AGORA_APP_ID=your_app_id_here
AGORA_TOKEN=your_token_here
```

### 4. **Firebase Kurulumu**
1. [Firebase Console](https://console.firebase.google.com/)'a gidin
2. Yeni proje oluşturun
3. Realtime Database'i etkinleştirin
4. Service account key'i indirin
5. `ika-db.json` dosyasını güncelleyin

## 🎮 Kullanım

### **Alıcı Uygulaması (Ana Kontrol)**
```bash
python ika-app.py
```

**Özellikler:**
- 🎥 3 kamera görüntüsü (Ön, Lazer, Arka)
- 📹 Kayıt sistemi (recordings klasörüne)
- 🎮 Manuel kontrol sistemi
- 📊 Sensör verileri
- 🔥 Firebase entegrasyonu

### **Gönderici Web Uygulaması**
```bash
python test_multi_camera.py
```

**Özellikler:**
- 🎥 3 kamera desteği
- 🔐 Güvenli token sistemi (form'dan alınır)
- 🌐 Web tabanlı
- 📱 Mobil uyumlu (Agora sayesinde görüntü aktarımı)
- ✅ Kimlik bilgileri güvenli (hardcoded değil)

### **Kontrol Tuşları**
| Tuş | Fonksiyon |
|-----|-----------|
| **↑↓←→** | Hareket kontrolü |
| **1, 2** | Vites kontrolü |
| **B, G** | Özel vitesler |
| **L** | Lazer modu |
| **M** | Manuel mod |
| **Space** | Acil durdurma |

## 📹 Kayıt Sistemi

### **Otomatik Kayıt**
1. **"🎥 Yayını Başlat"** butonuna basın
2. **"📹 Kaydetmeyi Başlat"** butonuna basın
3. Kayıtlar `recordings/` klasörüne kaydedilir:
   - `on-cam.webm` - Ön kamera
   - `lazer-cam.webm` - Lazer kamera  
   - `arka-cam.webm` - Arka kamera

### **HTTP Sunucu Sistemi**
- **Port**: 8080
- **Protokol**: HTTP/HTTPS
- **Encoding**: Base64
- **CORS**: Desteklenir
- **Otomatik**: Başlatma/durdurma

## 🔧 Teknik Detaylar

### **Agora WebRTC**
- **SDK**: AgoraRTC_N-4.19.3.js
- **Protokol**: WebRTC
- **Codec**: VP9 (WebM)
- **Çözünürlük**: 1440x900 optimize
- **FPS**: 30fps
- **Bitrate**: Adaptif

### **PyQt6 Entegrasyonu**
- **QWebEngineView**: Video görüntüleme
- **QWebEnginePage**: JavaScript entegrasyonu
- **Thread-safe**: Güvenli çoklu işlem
- **Event-driven**: Olay tabanlı mimari
- **Responsive**: Dinamik boyutlandırma

### **Firebase Entegrasyonu**
- **Realtime Database**: Sensör verileri
- **Authentication**: Güvenli erişim
- **Cloud Functions**: Otomatik işlemler
- **Analytics**: Performans takibi

### **Dosya Yönetimi**
- **HTTP Server**: Port 8080
- **Base64 Encoding**: Güvenli transfer
- **CORS Support**: Web güvenliği
- **Auto-cleanup**: Otomatik temizlik

## 🐛 Sorun Giderme

### **Yayın Bağlantı Sorunu**
```bash
# Token kontrolü
python test_multi_camera.py

# Agora servis durumu
curl https://api.agora.io/dev/v1/status
```

### **Kayıt Sorunu**
```bash
# HTTP sunucu kontrolü
netstat -an | findstr 8080

# Port kullanımı
netstat -ano | findstr :8080
```

### **Firebase Sorunu**
```bash
# Firebase bağlantı testi
python -c "import firebase_admin; print('Firebase OK')"

# Credentials kontrolü
python -c "import json; json.load(open('ika-db-eb609-firebase-adminsdk-fbsvc-96c3b83edc.json'))"
```

### **PyQt6 Sorunu**
```bash
# PyQt6 kurulum kontrolü
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"

# WebEngine kontrolü
python -c "from PyQt6.QtWebEngineWidgets import QWebEngineView; print('WebEngine OK')"
```

### **Yaygın Hatalar**

| Hata | Çözüm |
|------|-------|
| `CAN_NOT_GET_GATEWAY_SERVER` | Token'ı yenileyin |
| `No module named 'PyQt6'` | `pip install PyQt6` |
| `Firebase connection failed` | Credentials dosyasını kontrol edin |
| `Port 8080 already in use` | Farklı port kullanın |

## 📝 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

```
MIT License

Copyright (c) 2024 IKA Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🤝 Katkıda Bulunma

1. **Fork** yapın
2. **Feature branch** oluşturun (`git checkout -b feature/AmazingFeature`)
3. **Commit** yapın (`git commit -m 'Add some AmazingFeature'`)
4. **Push** yapın (`git push origin feature/AmazingFeature`)
5. **Pull Request** açın

### **Geliştirme Kuralları**
- **Code Style**: PEP 8 standartları
- **Documentation**: Docstring'ler zorunlu
- **Testing**: Unit testler ekleyin
- **Commits**: Açıklayıcı commit mesajları

## 📞 İletişim

- **Proje Linki**: [https://github.com/sbugrayy/IkaApp](https://github.com/sbugrayys/IkaApp)
- **Buğra Yıldırım**: [https://github.com/sbugrayy](https://github.com/sbugrayy)
- **Ayşenur Ebrar Gündüz**: [https://github.com/AysenurGunduz](https://github.com/AysenurGunduz)
- **Sidal Sınırtaş**: [https://github.com/sidalss](https://github.com/sidalss)

---

**🎉 İKA Projesi - İnsansız Kara Aracı Kontrol Sistemi**

*Bu proje, Teknofest İka yarışması için geliştirilmiş gelişmiş bir kontrol ve izleme sistemidir.*
