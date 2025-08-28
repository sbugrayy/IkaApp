#!/usr/bin/env python3
"""
İKA Çoklu Kamera Test Scripti
Çoklu kamera gönderici sayfasını açar ve kimlik bilgilerini otomatik doldurur.
"""

import webbrowser
import os
import sys
import tempfile
from dotenv import load_dotenv

def main():
    """Çoklu kamera gönderici sayfasını açar ve kimlik bilgilerini otomatik doldurur"""

    # .env dosyasını yükle
    load_dotenv('config.env')
    agora_app_id = os.getenv('AGORA_APP_ID')
    agora_token = os.getenv('AGORA_TOKEN')

    if not agora_app_id or not agora_token:
        print("❌ HATA: AGORA_APP_ID veya AGORA_TOKEN bulunamadı!")
        print("📝 Lütfen config.env dosyasını kontrol edin.")
        return

    # HTML dosyasının yolu
    html_file_path = os.path.join(os.path.dirname(__file__), 'multi_camera_sender.html')

    if not os.path.exists(html_file_path):
        print(f"❌ HTML dosyası bulunamadı: {html_file_path}")
        return

    # HTML içeriğini oku
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Otomatik doldurma için bir JavaScript kodu oluştur
    autofill_script = f"""
<script>
    document.addEventListener('DOMContentLoaded', function() {{
        document.getElementById('appId').value = '{agora_app_id}';
        document.getElementById('token').value = '{agora_token}';
    }});
</script>
"""
    # Oluşturulan script'i </head> etiketinden hemen önce HTML içeriğine ekle
    html_content = html_content.replace('</head>', autofill_script + '</head>')
    
    # JavaScript değişkenlerini de doldurarak uygulamanın doğru çalışmasını garantile
    html_content = html_content.replace("let AGORA_APP_ID = '';", f"let AGORA_APP_ID = '{agora_app_id}';")
    html_content = html_content.replace("let AGORA_TOKEN = '';", f"let AGORA_TOKEN = '{agora_token}';")


    # Tarayıcının dosyayı okuyabilmesi için 'delete=False' olarak ayarlanmış geçici bir HTML dosyası oluştur
    # İşletim sistemi bu dosyayı daha sonra otomatik olarak temizleyecektir
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
        f.write(html_content)
        temp_html_path = f.name

    # Dosya URL'sini oluştur
    file_url = f"file:///{temp_html_path.replace(os.sep, '/')}"

    print("🚀 İKA Çoklu Kamera Gönderici açılıyor...")
    print(f"📁 Geçici Dosya: {temp_html_path}")
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
        print(f"Manuel olarak şu dosyayı açın: {temp_html_path}")

if __name__ == "__main__":
    main()