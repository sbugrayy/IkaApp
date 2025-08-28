#!/usr/bin/env python3
"""
İKA Çoklu Kamera Test Scripti
Çoklu kamera gönderici sayfasını açar
"""

import webbrowser
import os
import sys

def main():
    """Çoklu kamera gönderici sayfasını açar"""
    
    # HTML dosyasının yolu
    html_file = os.path.join(os.path.dirname(__file__), 'multi_camera_sender.html')
    
    if not os.path.exists(html_file):
        print(f"❌ HTML dosyası bulunamadı: {html_file}")
        return
    
    # Dosya URL'sini oluştur
    file_url = f"file:///{html_file.replace(os.sep, '/')}"
    
    print("🚀 İKA Çoklu Kamera Gönderici açılıyor...")
    print(f"📁 Dosya: {html_file}")
    print(f"🌐 URL: {file_url}")
    print("\n📱 Kullanım Talimatları:")
    print("1. App ID ve Token otomatik olarak doldurulmuştur")
    print("2. Temel Kanal adını belirleyin (örn: ika_multi_camera)")
    print("3. '🚀 Tüm Kameraları Başlat' butonuna basın")
    print("4. Veya her kamera için ayrı ayrı 'Başlat' butonuna basın")
    print("5. Farklı kameralar farklı kanallara yayın yapacak:")
    print("   - Ön Kamera: channel_one (UID: 1)")
    print("   - Lazer Kamera: channel_two (UID: 2)")
    print("   - Arka Kamera: channel_three (UID: 3)")
    print("\n💻 İKA Uygulamasında:")
    print("1. python ika-app.py çalıştırın")
    print("2. '🎥 Yayını Başlat' butonuna basın")
    print("3. Mobil cihazdan gelen görüntüleri görün")
    print("4. '📹 Kaydetmeyi Başlat' ile kayıt alın")
    
    # Tarayıcıda aç
    try:
        webbrowser.open(file_url)
        print(f"\n✅ Tarayıcıda açıldı: {file_url}")
    except Exception as e:
        print(f"❌ Tarayıcı açılamadı: {e}")
        print(f"Manuel olarak şu dosyayı açın: {html_file}")

if __name__ == "__main__":
    main()
