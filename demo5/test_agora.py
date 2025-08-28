#!/usr/bin/env python3
"""
Agora WebRTC Test Script
Mobil test için HTML dosyasını açar
"""

import webbrowser
import os
import sys

def main():
    """Mobil test HTML dosyasını açar"""
    
    # HTML dosyasının yolu
    html_file = os.path.join(os.path.dirname(__file__), 'mobile_test.html')
    
    if not os.path.exists(html_file):
        print(f"❌ HTML dosyası bulunamadı: {html_file}")
        return
    
    # Dosya URL'sini oluştur
    file_url = f"file:///{html_file.replace(os.sep, '/')}"
    
    print("🚀 Mobil test sayfası açılıyor...")
    print(f"📁 Dosya: {html_file}")
    print(f"🌐 URL: {file_url}")
    print("\n📱 Mobil cihazınızda test etmek için:")
    print("1. Bu dosyayı mobil cihazınıza kopyalayın")
    print("2. Mobil tarayıcıda açın")
    print("3. App ID ve Token girin")
    print("4. 'test_channel' kanalını kullanın")
    print("5. Yayını başlatın")
    print("\n💻 Bilgisayarda test etmek için:")
    print("1. main.py veya ika-app.py çalıştırın")
    print("2. Aynı App ID ve Token'ı girin")
    print("3. Mobil cihazdan gelen görüntüyü göreceksiniz")
    
    # Tarayıcıda aç
    try:
        webbrowser.open(file_url)
        print(f"\n✅ Tarayıcıda açıldı: {file_url}")
    except Exception as e:
        print(f"❌ Tarayıcı açılamadı: {e}")
        print(f"Manuel olarak şu dosyayı açın: {html_file}")

if __name__ == "__main__":
    main()
