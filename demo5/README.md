# İKA Agora WebRTC Entegrasyonu - Optimize Edilmiş

Bu proje, İKA (İnsansız Kara Aracı) kontrol arayüzüne Agora WebRTC entegrasyonu ekler. Ön kamera görüntüsü yerine uzak video akışı gösterir.

## Özellikler

### ika-app.py (Ana Uygulama)
- **Agora Entegrasyonu**: Ön kamera paneli Agora WebRTC ile değiştirildi
- **Sensör Paneli**: App ID, Token ve "Yayını Başlat" butonu eklendi
- **Otomatik Kanal**: Channel adı otomatik olarak "test_channel" olarak ayarlanır
- **Uzak Video**: Ön kamera yerine uzak görüntü gösterilir

### main.py (Optimize Edilmiş)
- **Basit Arayüz**: Sadece App ID, Token ve "Yayını Başlat" butonu
- **Otomatik Kanal**: Channel otomatik "test_channel" seçilir
- **Temiz Tasarım**: Gereksiz kontroller kaldırıldı

## Kurulum

### Gereksinimler
```bash
pip install -r requirements.txt
```

### Bağımlılıklar
- PyQt6>=6.4.0
- PyQt6-WebEngine>=6.4.0
- PyQt6-Qt6>=6.4.0
- firebase-admin>=6.0.0

## Kullanım

### 1. Ana Uygulama (ika-app.py)
```bash
python ika-app.py
```

**Özellikler:**
- Sensör verilerinin altında Agora bağlantı bilgileri
- App ID ve Token girişi
- "Yayını Başlat" butonu ile uzak görüntü aktarımı
- Ön kamera yerine uzak video gösterimi

### 2. Optimize Edilmiş Uygulama (main.py)
```bash
python main.py
```

**Özellikler:**
- Sadece App ID, Token ve "Yayını Başlat" butonu
- Otomatik "test_channel" seçimi
- Temiz ve basit arayüz

## Mobil Test

### Test Ortamı Kurulumu

1. **Agora Hesabı Oluşturun:**
   - [Agora.io](https://www.agora.io) adresine gidin
   - Ücretsiz hesap oluşturun
   - App ID ve Token alın

2. **Mobil Test için:**
   - Mobil cihazınızda web tarayıcısı açın
   - Aşağıdaki test URL'lerini kullanın:

### Test URL'leri

#### Yayın Yapan (Sender) - Mobil
```
https://test.agora.io/agora-web-showcase/
```
- App ID girin
- Token girin (opsiyonel)
- Channel: "test_channel"
- "Join" butonuna basın
- Kamera izni verin

#### İzleyen (Receiver) - Bilgisayar
- `main.py` veya `ika-app.py` çalıştırın
- Aynı App ID ve Token'ı girin
- "Yayını Başlat" butonuna basın
- Mobil cihazdan gelen görüntüyü göreceksiniz

### Alternatif Test Yöntemi

#### Basit HTML Test Sayfası
```bash
python test_agora.py
```
Bu komut tarayıcıda test sayfası açar.

## Agora Ayarları

### App ID Alma
1. Agora Console'a giriş yapın
2. "Create" butonuna tıklayın
3. Proje adı girin
4. App ID'yi kopyalayın

### Token Alma (Opsiyonel)
- Test için token gerekmez
- Production için token gerekli
- Agora Console'dan token oluşturabilirsiniz

## Sorun Giderme

### Yaygın Sorunlar

1. **Kamera İzni Hatası:**
   - Tarayıcıda kamera izni verin
   - HTTPS kullanın (production)

2. **Bağlantı Hatası:**
   - App ID'yi kontrol edin
   - İnternet bağlantısını kontrol edin

3. **Video Görünmüyor:**
   - Mobil cihazda yayın başlatıldığından emin olun
   - Aynı channel adını kullandığınızdan emin olun

### Debug Modu
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dosya Yapısı

```
demo6/
├── ika-app.py          # Ana uygulama (Agora entegrasyonlu)
├── main.py             # Optimize edilmiş uygulama
├── test_agora.py       # Test scripti
├── requirements.txt    # Bağımlılıklar
└── README.md          # Bu dosya
```

## Teknik Detaylar

### Agora Entegrasyonu
- WebRTC tabanlı video akışı
- Audience role ile uzak video izleme
- Host role ile yayın yapma
- Otomatik bağlantı yönetimi

### PyQt6 WebEngine
- HTML5 video desteği
- JavaScript entegrasyonu
- Medya izinleri yönetimi

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.
