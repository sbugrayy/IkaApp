# Drone Kontrol Arayüzü

Modern ve kullanıcı dostu bir drone/robot kontrol arayüzü. PyQt6 ile geliştirilmiş profesyonel bir kontrol paneli.

## 🚀 Özellikler

### 📹 Kamera Görüntüleri
- **Ön Kamera**: Drone'un ön görüşü
- **Arka Kamera**: Drone'un arka görüşü  
- **Lazer Atış Kamera**: Lazer hedefleme görüntüsü
- Gerçek zamanlı görüntü akışı (simüle edilmiş)

### 📊 Sensör Verileri
- **IMU Sensörü**: Roll, Pitch, Yaw açıları ve ivme verileri
- **GPS Sensörü**: Konum, yükseklik ve hız bilgileri
- Gerçek zamanlı veri güncellemesi

### 🎮 Kontrol Sistemi
- **Acil Durdurma**: Güvenlik için acil durdurma butonu
- **Kontrol Modları**: Manuel, Yarı Otonom, Otonom
- **Yön Kontrolü**: İleri, Geri, Sol, Sağ, Dur komutları
- **Lazer Atış Modu**: Özel lazer kontrol tuşları

## 🎨 Tasarım Özellikleri

- Modern gradient arka plan
- Profesyonel renk paleti
- Hover efektleri
- Responsive tasarım
- Kullanıcı dostu arayüz

## 📋 Gereksinimler

```bash
pip install -r requirements.txt
```

### Gerekli Kütüphaneler
- PyQt6==6.6.1
- opencv-python==4.8.1.78
- numpy==1.24.3
- pyserial==3.5

## 🚀 Kurulum ve Çalıştırma

1. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

2. **Uygulamayı çalıştırın:**
```bash
python main.py
```

## 🎯 Kullanım

### Temel Kontroller
- **Manuel Mod**: Tam manuel kontrol
- **Yarı Otonom**: Yardımlı kontrol
- **Otonom**: Tam otomatik kontrol

### Yön Kontrolü
- ▲ **İleri**: Drone'u ileri hareket ettir
- ▼ **Geri**: Drone'u geri hareket ettir
- ◄ **Sol**: Drone'u sola döndür
- ► **Sağ**: Drone'u sağa döndür
- ● **Dur**: Drone'u durdur

### Lazer Atış Modu
- **LAZER ATIŞ MODU** butonuna tıklayın
- Özel lazer kontrol tuşları açılır
- 🔥 **ATEŞ!** butonu ile lazer ateşleyin

### Acil Durum
- **ACİL DURDUR** butonu ile güvenli durdurma

## 🔧 Teknik Detaylar

### Thread Yapısı
- **CameraThread**: Kamera görüntülerini işler
- **SensorThread**: Sensör verilerini okur
- Ana UI thread'i bloklamaz

### Simülasyon
- Gerçek kamera yerine simüle edilmiş görüntüler
- Rastgele sensör verileri
- Gerçek donanıma kolay entegrasyon

## 🎨 Özelleştirme

### Renk Teması
CSS benzeri stil dosyası ile kolay özelleştirme:
```python
self.setStyleSheet("""
    QMainWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #1e3c72, stop:1 #2a5298);
    }
""")
```

### Gerçek Donanım Entegrasyonu
- Kamera thread'lerinde gerçek kamera API'leri kullanın
- Sensör thread'inde gerçek sensör verilerini okuyun
- Kontrol fonksiyonlarında gerçek drone komutları gönderin

## 📱 Ekran Görüntüleri

Arayüz şu bölümlerden oluşur:
1. **Sol Panel**: Kamera görüntüleri
2. **Orta Panel**: Sensör verileri
3. **Sağ Panel**: Kontrol tuşları

## 🔮 Gelecek Özellikler

- [ ] Gerçek kamera entegrasyonu
- [ ] Harita görüntüleme
- [ ] Kayıt ve oynatma özelliği
- [ ] Çoklu drone desteği
- [ ] Web arayüzü

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit yapın (`git commit -m 'Add some AmazingFeature'`)
4. Push yapın (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 👨‍💻 Geliştirici

Drone kontrol arayüzü - PyQt6 ile geliştirilmiş modern kontrol paneli.

---

**Not**: Bu uygulama şu anda simülasyon modunda çalışmaktadır. Gerçek drone kontrolü için donanım entegrasyonu gereklidir.
