# IkaApp - WebRTC Görüntü Aktarım Demosu

Bu proje, PyQt5 ve WebRTC teknolojilerini kullanarak iki bilgisayar arasında canlı video akışı ve kaydı yapmayı sağlayan bir masaüstü uygulamasıdır.

## Özellikler

- **Gönderici (Sender):** Bilgisayarın kamerasından ve mikrofonundan canlı yayın yapar.
- **Alıcı (Receiver):** Gelen canlı yayını görüntüler ve isteğe bağlı olarak `.webm` formatında kaydedebilir.
- **Dinamik IP Yapılandırması:** Python betiği, sinyal sunucusu için IP adresini otomatik olarak algılar veya manuel olarak ayarlanabilir.
- **Hata Ayıklama:** Dahili geliştirici konsolu sayesinde bağlantı sorunlarını teşhis etme imkanı.

## Gereksinimler

Uygulamayı çalıştırmak için bilgisayarınızda Python 3 kurulu olmalıdır. Gerekli Python kütüphanelerini aşağıdaki komutla yükleyebilirsiniz:

```bash
pip install PyQt5 PyQtWebEngine websockets
```

## Nasıl Kullanılır?

Bu uygulama, aynı yerel ağa (LAN/Wi-Fi) bağlı iki bilgisayar arasında çalışacak şekilde tasarlanmıştır. Bir bilgisayar **Sunucu & Gönderici**, diğeri ise **Alıcı** olacaktır.

### Adım 1: Sunucu Bilgisayarını Hazırlama

Görüntüsünü gönderecek olan bilgisayarda (PC-1) aşağıdaki adımları izleyin:

1.  **Sinyal Sunucusunu Başlatın:**
    Bir terminal açın ve aşağıdaki komutla sinyal sunucusunu çalıştırın. Bu sunucu, iki bilgisayarın birbiriyle iletişim kurmasını sağlar.
    ```bash
    python demo/signaling_server.py
    ```
    Terminalde `Signaling server 0.0.0.0:8765 çalışıyor...` mesajını göreceksiniz. **Bu terminali kapatmayın!**

2.  **Uygulamayı Başlatın (Gönderici & Alıcı):**
    Yeni bir terminal açın ve `webrtc_app.py` betiğini çalıştırın.
    ```bash
    python demo/webrtc_app.py
    ```
    - Bu bilgisayarda `SIGNALING_SERVER_IP` ayarının `'auto'` kalması yeterlidir.
    - Ekranda "Gönderici" ve "Alıcı" pencereleri açılacaktır. "Gönderici" penceresinde kendi kamera görüntünüzü görmelisiniz.

### Adım 2: Alıcı Bilgisayarını Hazırlama

Görüntüyü alacak olan bilgisayarda (PC-2) aşağıdaki adımları izleyin:

1.  **Sunucu IP'sini Ayarlayın:**
    `demo/webrtc_app.py` dosyasını bir metin düzenleyici ile açın. Dosyanın en üstündeki `SIGNALING_SERVER_IP` değişkenini, **PC-1'in yerel IP adresiyle** değiştirin. (PC-1'in IP adresini `ipconfig` (Windows) veya `ifconfig` (Linux/macOS) komutlarıyla öğrenebilirsiniz.)

    Örnek:
    ```python
    # PC-1'in IP adresi 192.168.1.42 ise:
    SIGNALING_SERVER_IP = '192.168.1.42'
    ```

2.  **Uygulamayı Başlatın:**
    Bir terminal açın ve düzenlediğiniz `webrtc_app.py` betiğini çalıştırın.
    ```bash
    python demo/webrtc_app.py
    ```

### Adım 3: Bağlantı ve Test

- PC-2'de açılan "Alıcı" penceresinde birkaç saniye içinde PC-1'den gelen görüntünün belirmesi gerekir.
- Görüntü geldikten sonra, alıcıdaki "Kaydı Başlat/Durdur" butonu aktif olacaktır.

### Sorun Giderme

Eğer alıcıda görüntü görünmüyorsa:

1.  **IP Adresini Kontrol Edin:** PC-2'deki `SIGNALING_SERVER_IP` değişkenine PC-1'in doğru IP adresini yazdığınızdan emin olun.
2.  **Ağ Bağlantısı:** İki bilgisayarın da aynı Wi-Fi veya yerel ağa bağlı olduğunu doğrulayın.
3.  **Güvenlik Duvarı (Firewall):** Uygulamayı ilk kez çalıştırdığınızda Windows veya antivirüs yazılımınız ağ erişimi için izin isteyebilir. **Python'a mutlaka izin verin.** Eğer izin istemediyse, Windows Güvenlik Duvarı ayarlarından Python uygulamasına manuel olarak izin vermeniz gerekebilir. Bu, en yaygın bağlantı sorunudur.
4.  **Konsol Logları:** Herhangi bir pencereye sağ tıklayıp **"Inspect"** seçeneğini seçin. Açılan geliştirici panelindeki **"Console"** sekmesi, bağlantı sırasında oluşan hataları size gösterecektir. Özellikle `ICE bağlantı durumu: failed` hatası alıyorsanız, sorun büyük olasılıkla güvenlik duvarıdır.