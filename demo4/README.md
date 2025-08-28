# 🎥 IKA Dashboard - WebRTC Çoklu Kamera Entegrasyonu

Bu proje, IKA Dashboard'a WebRTC entegrasyonu ekleyerek çoklu kamera görüntü aktarımı sağlar.

## ✨ Özellikler

- 🎮 **Mevcut Dashboard**: Tüm mevcut özellikler korundu
- 📹 **WebRTC Entegrasyonu**: Çoklu kamera streaming
- 🎥 **Entegre Kamera Yönetimi**: Ana uygulamada kamera kontrolü
- 🔍 **Otomatik Kamera Algılama**: OpenCV ile kamera tespiti
- 📡 **Socket.IO Streaming**: Gerçek zamanlı görüntü aktarımı
- 🎨 **Koyu Tema**: Modern ve şık arayüz

## 🛠️ Kurulum

### 1. Python Bağımlılıkları
```bash
pip install -r requirements.txt
```

### 2. WebRTC Server Kurulumu (Docker)

#### Basit Kurulum (Önerilen):
```bash
# demo5 klasörüne git
cd demo5

# Basit Docker Compose ile başlat
docker-compose -f docker-compose-simple.yml up -d
```

#### Alternatif Kurulum:
```bash
# Node.js server'ı manuel başlat
cd webrtc-server
npm install
npm start
```

### 3. Uygulamayı Başlat
```bash
python main.py
```

## 🚀 Kullanım

### Ana Dashboard
1. **Sensör Verileri** bölümünde **"Kamera Yapılandırmaları"** görünür
2. Room ID gir (örn: `ika-camera-room`)
3. **"🔌 Sunucuya Bağlan"** ile bağlantı kur
4. **"▶️ Yayını Başlat"** ile streaming başlat
5. **"🐛 Debug - Görüntü Kontrolü"** ile test et

### Sender Uygulaması (NVIDIA PC)
1. `sender.py` dosyasını çalıştır
2. Kameraları otomatik tarar
3. Server'a bağlanır ve yayın başlatır

## 📁 Dosya Yapısı

```
demo5/
├── main.py                    # Ana uygulama (receiver)
├── sender.py                  # Sender uygulaması (NVIDIA PC)
├── requirements.txt           # Python bağımlılıkları
├── docker-compose-simple.yml # Basit Docker kurulumu
├── README.md                 # Bu dosya
└── webrtc-server/
    ├── package.json          # Node.js bağımlılıkları
    └── server.js             # WebRTC server
```

## 🔧 Teknik Detaylar

### WebRTC Bileşenleri
- **WebRTC Server**: Node.js server (port 3000)
- **Socket.IO**: Gerçek zamanlı iletişim

### Kamera Entegrasyonu
- OpenCV ile kamera algılama
- Socket.IO ile gerçek zamanlı iletişim
- Çoklu kamera desteği

### Arayüz Özellikleri
- Koyu tema
- Responsive tasarım
- Tab-based navigation
- Real-time durum güncellemeleri

## 🐛 Sorun Giderme

### Docker Sorunları
```bash
# Container'ları yeniden başlat
docker-compose -f docker-compose-simple.yml down
docker-compose -f docker-compose-simple.yml up -d

# Logları kontrol et
docker-compose -f docker-compose-simple.yml logs -f
```

### Port Çakışması
```bash
# Port kullanımını kontrol et
netstat -an | findstr :3000
```

### Python Bağımlılık Sorunları
```bash
# PyQt6-WebEngine'i yeniden kur
pip uninstall PyQt6-WebEngine
pip install PyQt6-WebEngine

# Tüm bağımlılıkları yeniden kur
pip install -r requirements.txt --force-reinstall
```

## ✅ Başarılı Kurulum Kontrolü

1. **WebRTC Server:** http://localhost:3000/health çalışır
2. **Ana Uygulama:** `python main.py` hatasız çalışır
3. **Sender Uygulaması:** `python sender.py` hatasız çalışır
4. **Kamera Tarama:** Kameralar bulunur
5. **Görüntü Aktarımı:** Frame'ler başarıyla iletilir

## 📝 Notlar

- Socket.IO tabanlı, düşük gecikme
- Çoklu platform desteği
- Gerçek zamanlı görüntü aktarımı
- Basit ve etkili kurulum

## 📄 Lisans

MIT License - Detaylar için LICENSE dosyasına bakın.

