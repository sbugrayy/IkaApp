# Çoklu Kamera Agora Uygulaması

Bu uygulama, Agora WebRTC platformunu kullanarak çoklu kamera desteği ile görüntü aktarımı yapmanızı sağlar.

## Özellikler

- 3 farklı kamera görüntüsünü aynı anda gönderme
- Gönderici ve alıcı modları
- Kamera önizleme özelliği
- Agora WebRTC entegrasyonu
- PyQt6 tabanlı modern arayüz

## Gereksinimler

Gerekli paketleri yüklemek için:

```bash
pip install -r requirements.txt
```

## Kullanım

1. Gönderici modunda başlatmak için:
```bash
python main.py
```

2. Alıcı modunda başlatmak için:
```bash
python main.py receiver
```

3. Uygulama başladıktan sonra:
   - Agora App ID ve Token bilgilerini girin
   - Kanal adını belirleyin
   - (Gönderici) Kamera seçimlerini yapın
   - (Gönderici) Kamera önizlemeyi başlatın
   - "Yayını Başlat" düğmesine tıklayın

## Notlar

- Agora App ID ve Token bilgilerini [Agora Console](https://console.agora.io/)'dan alabilirsiniz
- Her kamera için ayrı bir video track oluşturulur
- Alıcı tarafı otomatik olarak tüm video trackleri alır ve gösterir
- WebRTC bağlantısı için internet bağlantısı gereklidir
