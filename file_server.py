#!/usr/bin/env python3
"""
Dosya Kaydetme HTTP Sunucusu
WebRTC kayıtlarını recordings klasörüne kaydeder
"""

import os
import base64
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

class FileUploadHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, recordings_dir="recordings", **kwargs):
        self.recordings_dir = recordings_dir
        os.makedirs(recordings_dir, exist_ok=True)
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Dosya yükleme isteği"""
        try:
            # Content length al
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # JSON verisini parse et
            data = json.loads(post_data.decode('utf-8'))
            
            filename = data.get('filename', 'kayit.webm')
            base64_data = data.get('data', '')
            
            if not base64_data:
                self.send_error(400, "Base64 data eksik")
                return
            
            # Base64'ü decode et
            file_data = base64.b64decode(base64_data)
            
            # Dosya yolunu oluştur
            filepath = os.path.join(self.recordings_dir, filename)
            
            # Dosyayı kaydet
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            # Başarılı yanıt
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'status': 'success',
                'message': f'Dosya kaydedildi: {filepath}',
                'filepath': filepath
            }
            
            self.wfile.write(json.dumps(response).encode())
            print(f"✅ Dosya kaydedildi: {filepath}")
            
        except Exception as e:
            print(f"❌ Dosya kaydetme hatası: {e}")
            self.send_error(500, f"Dosya kaydetme hatası: {str(e)}")
    
    def do_OPTIONS(self):
        """CORS preflight isteği"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Log mesajlarını sustur"""
        pass

class FileServer:
    def __init__(self, port=8080, recordings_dir="recordings"):
        self.port = port
        self.recordings_dir = recordings_dir
        self.server = None
        self.server_thread = None
        
    def start(self):
        """Sunucuyu başlat"""
        try:
            # Handler'ı oluştur
            handler = type('FileUploadHandler', (FileUploadHandler,), {
                'recordings_dir': self.recordings_dir
            })
            
            # HTTP sunucusu oluştur
            self.server = HTTPServer(('localhost', self.port), handler)
            
            # Sunucuyu ayrı thread'de başlat
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"✅ Dosya sunucusu başlatıldı: http://localhost:{self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Sunucu başlatma hatası: {e}")
            return False
    
    def stop(self):
        """Sunucuyu durdur"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("✅ Dosya sunucusu durduruldu")
    
    def get_recordings_list(self):
        """Recordings klasöründeki dosyaları listele"""
        try:
            files = []
            for filename in os.listdir(self.recordings_dir):
                filepath = os.path.join(self.recordings_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'name': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'modified': time.ctime(stat.st_mtime)
                    })
            return files
        except Exception as e:
            print(f"❌ Dosya listesi alınamadı: {e}")
            return []

def main():
    """Test fonksiyonu"""
    server = FileServer(port=8080)
    
    if server.start():
        print("Sunucu çalışıyor... Ctrl+C ile durdurun")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
    
    # Dosyaları listele
    files = server.get_recordings_list()
    print(f"\nRecordings klasöründe {len(files)} dosya var:")
    for file in files:
        print(f"  - {file['name']} ({file['size']} bytes)")

if __name__ == "__main__":
    main()
