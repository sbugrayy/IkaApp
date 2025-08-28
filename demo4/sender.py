#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎥 IKA Kamera Gönderici - NVIDIA PC
Sadece kamera görüntüsü gönderen uygulama
"""

import sys
import cv2
import numpy as np
import json
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QGroupBox, QTextEdit, QTabWidget, QCheckBox,
                             QScrollArea, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont
import socketio
import threading

class CameraStreamThread(QThread):
    """Kamera akış thread'i"""
    frame_ready = pyqtSignal(int, np.ndarray)  # camera_id, frame
    error_occurred = pyqtSignal(str)
    
    def __init__(self, camera_id, camera_index, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self.camera_index = camera_index
        self.running = False
        self.cap = None
        
    def run(self):
        """Kamera akışını başlat"""
        try:
            # Farklı backend'lerle dene
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            
            for backend in backends:
                try:
                    self.cap = cv2.VideoCapture(self.camera_index, backend)
                    if self.cap.isOpened():
                        # Kamera ayarlarını optimize et
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.cap.set(cv2.CAP_PROP_FPS, 30)
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                        break
                except Exception as e:
                    continue
            
            if not self.cap or not self.cap.isOpened():
                self.error_occurred.emit(f"Kamera {self.camera_index} açılamadı!")
                return
            
            self.running = True
            
            while self.running:
                try:
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        # Frame'i işle ve gönder
                        processed_frame = self.process_frame(frame)
                        self.frame_ready.emit(self.camera_id, processed_frame)
                    else:
                        time.sleep(0.1)
                        
                except Exception as e:
                    self.error_occurred.emit(f"Frame okuma hatası: {str(e)}")
                    time.sleep(0.1)
                    
        except Exception as e:
            self.error_occurred.emit(f"Kamera thread hatası: {str(e)}")
        finally:
            if self.cap:
                self.cap.release()
    
    def process_frame(self, frame):
        """Frame'i işle - Optimize edilmiş"""
        try:
            # Boyutu küçült (daha düşük çözünürlük)
            frame = cv2.resize(frame, (320, 240))  # Daha küçük boyut
            
            # JPEG sıkıştırma (daha düşük kalite)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]  # Daha düşük kalite
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            return buffer
        except Exception as e:
            # Hata durumunda boş buffer döndür
            return np.array([], dtype=np.uint8)
    
    def stop(self):
        """Thread'i durdur"""
        self.running = False
        self.wait()

class IKACameraSender(QMainWindow):
    """IKA Kamera Gönderici Ana Uygulama"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎥 IKA Kamera Gönderici - NVIDIA PC")
        self.setGeometry(100, 100, 1200, 800)
        
        # Kamera thread'leri
        self.camera_threads = {}
        self.available_cameras = []
        self.selected_cameras = []
        
        # Socket.IO client
        self.sio = None
        self.connected = False
        self.room_id = ""
        
        # UI oluştur
        self.init_ui()
        self.apply_dark_theme()
        
        # Kamera tarama timer'ı
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_cameras)
        
    def init_ui(self):
        """UI oluştur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Sol Panel - Kontroller
        left_panel = self.create_control_panel()
        layout.addWidget(left_panel, 1)
        
        # Sağ Panel - Video Görüntüleri
        right_panel = self.create_video_panel()
        layout.addWidget(right_panel, 2)
        
    def create_control_panel(self):
        """Kontrol paneli oluştur"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Başlık
        title = QLabel("🎥 IKA Kamera Gönderici")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Kamera Tarama
        scan_group = QGroupBox("🔍 Kamera Tarama")
        scan_layout = QVBoxLayout(scan_group)
        
        scan_btn = QPushButton("🔍 Kameraları Tara")
        scan_btn.clicked.connect(self.scan_cameras)
        scan_layout.addWidget(scan_btn)
        
        auto_scan_cb = QCheckBox("🔄 Otomatik Tarama (5 saniye)")
        auto_scan_cb.toggled.connect(self.toggle_auto_scan)
        scan_layout.addWidget(auto_scan_cb)
        
        layout.addWidget(scan_group)
        
        # Kamera Seçimi
        camera_group = QGroupBox("📹 Kamera Seçimi")
        camera_layout = QVBoxLayout(camera_group)
        
        self.camera_list = QScrollArea()
        self.camera_list_widget = QWidget()
        self.camera_list_layout = QVBoxLayout(self.camera_list_widget)
        self.camera_list.setWidget(self.camera_list_widget)
        self.camera_list.setWidgetResizable(True)
        self.camera_list.setMaximumHeight(200)
        camera_layout.addWidget(self.camera_list)
        
        # Seçili Kameralar
        selected_label = QLabel("Seçili Kameralar:")
        selected_label.setStyleSheet("font-weight: bold; color: #00ff00;")
        camera_layout.addWidget(selected_label)
        
        self.selected_cameras_label = QLabel("Hiç kamera seçilmedi")
        self.selected_cameras_label.setStyleSheet("color: #ff4444;")
        camera_layout.addWidget(self.selected_cameras_label)
        
        layout.addWidget(camera_group)
        
        # Bağlantı Ayarları
        connection_group = QGroupBox("🔗 Bağlantı Ayarları")
        connection_layout = QVBoxLayout(connection_group)
        
        # Room ID
        room_layout = QHBoxLayout()
        room_layout.addWidget(QLabel("Room ID:"))
        self.room_id_input = QLineEdit()
        self.room_id_input.setText("ika-camera-room")
        room_layout.addWidget(self.room_id_input)
        connection_layout.addLayout(room_layout)
        
        # Server URL
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Server:"))
        self.server_url_input = QLineEdit()
        self.server_url_input.setText("http://localhost:3000")
        server_layout.addWidget(self.server_url_input)
        connection_layout.addLayout(server_layout)
        
        # Bağlantı Butonları
        self.connect_btn = QPushButton("🔌 Bağlan")
        self.connect_btn.clicked.connect(self.connect_to_server)
        connection_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("❌ Bağlantıyı Kes")
        self.disconnect_btn.clicked.connect(self.disconnect_from_server)
        self.disconnect_btn.setEnabled(False)
        connection_layout.addWidget(self.disconnect_btn)
        
        layout.addWidget(connection_group)
        
        # Yayın Kontrolleri
        stream_group = QGroupBox("📡 Yayın Kontrolleri")
        stream_layout = QVBoxLayout(stream_group)
        
        self.start_stream_btn = QPushButton("▶️ Yayını Başlat")
        self.start_stream_btn.clicked.connect(self.start_streaming)
        self.start_stream_btn.setEnabled(False)
        stream_layout.addWidget(self.start_stream_btn)
        
        self.stop_stream_btn = QPushButton("⏹️ Yayını Durdur")
        self.stop_stream_btn.clicked.connect(self.stop_streaming)
        self.stop_stream_btn.setEnabled(False)
        stream_layout.addWidget(self.stop_stream_btn)
        
        layout.addWidget(stream_group)
        
        # Durum
        status_group = QGroupBox("📋 Durum")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        return panel
    
    def create_video_panel(self):
        """Video paneli oluştur"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Başlık
        title = QLabel("📹 Kamera Görüntüleri")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Video Grid
        self.video_grid = QGridLayout()
        
        # 3 kamera için video label'ları
        self.video_labels = {}
        camera_names = ["Ön Kamera", "Lazer Atış Kamera", "Arka Kamera"]
        
        for i, name in enumerate(camera_names):
            video_frame = QFrame()
            video_frame.setFrameStyle(QFrame.Shape.Box)
            video_frame.setMinimumSize(400, 300)
            video_layout = QVBoxLayout(video_frame)
            
            # Başlık
            title_label = QLabel(f"📹 {name}")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("font-weight: bold; color: #00ff00;")
            video_layout.addWidget(title_label)
            
            # Video label
            video_label = QLabel("Kamera bağlı değil")
            video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            video_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    border: 2px solid #404040;
                    border-radius: 8px;
                    color: #888888;
                    font-size: 14px;
                }
            """)
            video_layout.addWidget(video_label)
            
            self.video_labels[i] = video_label
            
            # Grid'e ekle
            row = i // 2
            col = i % 2
            self.video_grid.addWidget(video_frame, row, col)
        
        layout.addLayout(self.video_grid)
        layout.addStretch()
        
        return panel
    
    def apply_dark_theme(self):
        """Koyu tema uygula"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00ff00;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #888888;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                color: white;
                padding: 5px;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                color: #00ff00;
                font-family: monospace;
            }
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #404040;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #0078d4;
                background-color: #0078d4;
            }
        """)
    
    def scan_cameras(self):
        """Kamerları tara - Optimize edilmiş"""
        self.log_status("🔍 Kameralar taranıyor...")
        
        try:
            # Kamera listesini temizle
            for i in reversed(range(self.camera_list_layout.count())):
                self.camera_list_layout.itemAt(i).widget().setParent(None)
            
            self.available_cameras = []
            self.selected_cameras = []
            
            # Sadece en yaygın backend'leri dene
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
            found_cameras = 0
            
            for backend in backends:
                if found_cameras >= 3:  # Maksimum 3 kamera yeterli
                    break
                    
                for i in range(5):  # Sadece ilk 5 indeksi kontrol et
                    try:
                        cap = cv2.VideoCapture(i, backend)
                        if cap.isOpened():
                            # Hızlı test - sadece bir frame oku
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                camera_info = {
                                    'index': i,
                                    'backend': backend,
                                    'name': f'Kamera {i}',
                                    'resolution': f'{frame.shape[1]}x{frame.shape[0]}'
                                }
                                
                                # Aynı kamera zaten eklenmiş mi kontrol et
                                if not any(cam['index'] == i for cam in self.available_cameras):
                                    self.available_cameras.append(camera_info)
                                    found_cameras += 1
                                    
                                    # Kamera checkbox'ı oluştur
                                    checkbox = QCheckBox(f"📹 {camera_info['name']} ({camera_info['resolution']})")
                                    checkbox.setChecked(len(self.selected_cameras) < 3)  # İlk 3'ü seç
                                    checkbox.stateChanged.connect(lambda state, cam=camera_info: self.on_camera_selected(cam, state))
                                    self.camera_list_layout.addWidget(checkbox)
                                    
                                    if len(self.selected_cameras) < 3:
                                        self.selected_cameras.append(camera_info)
                            
                            cap.release()
                            
                    except Exception as e:
                        cap.release() if 'cap' in locals() else None
                        continue
            
            self.log_status(f"✅ {len(self.available_cameras)} kamera bulundu")
            self.update_selected_cameras_label()
            
        except Exception as e:
            self.log_status(f"❌ Kamera tarama hatası: {str(e)}")
    
    def toggle_auto_scan(self, enabled):
        """Otomatik tarama toggle"""
        if enabled:
            self.scan_timer.start(5000)  # 5 saniye
            self.log_status("🔄 Otomatik kamera tarama başlatıldı")
        else:
            self.scan_timer.stop()
            self.log_status("⏹️ Otomatik kamera tarama durduruldu")
    
    def on_camera_selected(self, camera, state):
        """Kamera seçimi değişikliği"""
        if state == Qt.CheckState.Checked:
            if camera not in self.selected_cameras and len(self.selected_cameras) < 3:
                self.selected_cameras.append(camera)
        else:
            if camera in self.selected_cameras:
                self.selected_cameras.remove(camera)
        
        self.update_selected_cameras_label()
        self.log_status(f"📹 Seçili kamera sayısı: {len(self.selected_cameras)}")
    
    def update_selected_cameras_label(self):
        """Seçili kameralar label'ını güncelle"""
        if not self.selected_cameras:
            self.selected_cameras_label.setText("Hiç kamera seçilmedi")
            self.selected_cameras_label.setStyleSheet("color: #ff4444;")
        else:
            camera_names = [f"{cam['name']} ({cam['resolution']})" for cam in self.selected_cameras]
            self.selected_cameras_label.setText("Seçili: " + ", ".join(camera_names))
            self.selected_cameras_label.setStyleSheet("color: #00ff00;")
    
    def connect_to_server(self):
        """Server'a bağlan - Optimize edilmiş"""
        self.room_id = self.room_id_input.text().strip()
        server_url = self.server_url_input.text().strip()
        
        if not self.room_id:
            self.log_status("❌ Room ID boş olamaz!")
            return
        
        if not server_url:
            self.log_status("❌ Server URL boş olamaz!")
            return
        
        try:
            # Socket.IO client'ı optimize edilmiş ayarlarla oluştur
            self.sio = socketio.Client(
                logger=False,
                engineio_logger=False,
                reconnection=True,
                reconnection_attempts=3,
                reconnection_delay=1000
            )
            
            @self.sio.event
            def connect():
                self.log_status("✅ Server'a bağlandı")
                self.connected = True
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
                self.start_stream_btn.setEnabled(True)
                
                # Odaya katıl
                try:
                    self.sio.emit('join-room', {
                        'roomId': self.room_id,
                        'role': 'sender'
                    })
                except Exception as e:
                    self.log_status(f"❌ Odaya katılma hatası: {str(e)}")
            
            @self.sio.event
            def disconnect():
                self.log_status("❌ Server bağlantısı kesildi")
                self.connected = False
                self.connect_btn.setEnabled(True)
                self.disconnect_btn.setEnabled(False)
                self.start_stream_btn.setEnabled(False)
                self.stop_stream_btn.setEnabled(False)
            
            @self.sio.event
            def room_joined(data):
                self.log_status(f"✅ Odaya katıldı: {data.get('roomId', 'Bilinmeyen')}")
            
            @self.sio.event
            def peer_joined(data):
                self.log_status(f"👤 Yeni peer katıldı: {data.get('peerId', 'Bilinmeyen')}")
            
            @self.sio.event
            def peer_left(data):
                self.log_status(f"👤 Peer ayrıldı: {data.get('peerId', 'Bilinmeyen')}")
            
            # Bağlantıyı başlat
            self.sio.connect(server_url, wait_timeout=10)
            
        except Exception as e:
            self.log_status(f"❌ Bağlantı hatası: {str(e)}")
            self.connected = False
    
    def disconnect_from_server(self):
        """Server'dan bağlantıyı kes"""
        if self.sio:
            self.sio.disconnect()
            self.sio = None
    
    def start_streaming(self):
        """Yayını başlat - Optimize edilmiş"""
        if not self.selected_cameras:
            self.log_status("❌ Hiç kamera seçilmedi!")
            return
        
        if not self.connected:
            self.log_status("❌ Server'a bağlı değil!")
            return
        
        try:
            # Kamera thread'lerini başlat
            for i, camera in enumerate(self.selected_cameras):
                thread = CameraStreamThread(i, camera['index'], self)
                thread.frame_ready.connect(self.on_frame_ready)
                thread.error_occurred.connect(self.log_status)
                thread.start()
                
                self.camera_threads[i] = thread
                
                # Frame counter'ları sıfırla
                setattr(self, f'frame_counter_{i}', 0)
                setattr(self, f'send_counter_{i}', 0)
                
                self.log_status(f"📹 {camera['name']} yayını başlatıldı")
            
            self.start_stream_btn.setEnabled(False)
            self.stop_stream_btn.setEnabled(True)
            self.log_status("✅ Tüm kamera yayınları başlatıldı")
            
        except Exception as e:
            self.log_status(f"❌ Yayın başlatma hatası: {str(e)}")
    
    def stop_streaming(self):
        """Yayını durdur"""
        try:
            # Kamera thread'lerini durdur
            for thread in self.camera_threads.values():
                thread.stop()
            
            self.camera_threads.clear()
            
            # Video label'larını temizle
            for label in self.video_labels.values():
                label.setText("Kamera bağlı değil")
            
            self.start_stream_btn.setEnabled(True)
            self.stop_stream_btn.setEnabled(False)
            self.log_status("⏹️ Tüm kamera yayınları durduruldu")
            
        except Exception as e:
            self.log_status(f"❌ Yayın durdurma hatası: {str(e)}")
    
    def on_frame_ready(self, camera_id, frame_data):
        """Frame hazır olduğunda - Optimize edilmiş"""
        try:
            # Frame'i göster (sadece her 5 frame'de bir)
            if camera_id in self.video_labels and hasattr(self, f'frame_counter_{camera_id}'):
                frame_counter = getattr(self, f'frame_counter_{camera_id}', 0)
                if frame_counter % 5 == 0:  # Her 5 frame'de bir göster
                    # JPEG'den frame'i decode et
                    frame_array = np.frombuffer(frame_data, dtype=np.uint8)
                    if len(frame_array) > 0:
                        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                        if frame is not None:
                            # QImage'e çevir
                            height, width, channel = frame.shape
                            bytes_per_line = 3 * width
                            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
                            
                            # QPixmap'e çevir ve göster
                            pixmap = QPixmap.fromImage(q_image)
                            scaled_pixmap = pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio)
                            self.video_labels[camera_id].setPixmap(scaled_pixmap)
                
                setattr(self, f'frame_counter_{camera_id}', frame_counter + 1)
            
            # Server'a gönder (sadece her 3 frame'de bir)
            if self.connected and self.sio and hasattr(self, f'send_counter_{camera_id}'):
                send_counter = getattr(self, f'send_counter_{camera_id}', 0)
                if send_counter % 3 == 0:  # Her 3 frame'de bir gönder
                    try:
                        self.sio.emit('camera-stream', {
                            'roomId': self.room_id,
                            'cameraId': camera_id,
                            'frame': frame_data.tobytes().hex()  # Binary'yi hex'e çevir
                        })
                    except Exception as e:
                        # Socket hatası durumunda sessizce devam et
                        pass
                
                setattr(self, f'send_counter_{camera_id}', send_counter + 1)
                
        except Exception as e:
            # Hata durumunda sessizce devam et
            pass
    
    def log_status(self, message):
        """Durum mesajı ekle"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        """Uygulama kapatılırken"""
        self.stop_streaming()
        self.disconnect_from_server()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # OpenCV log seviyesini ayarla
    try:
        cv2.setLogLevel(cv2.LOG_LEVEL_SILENT)
    except:
        pass
    
    win = IKACameraSender()
    win.show()
    sys.exit(app.exec())
