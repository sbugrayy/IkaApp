import sys
import random
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QLCDNumber, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QEasingCurve, QPropertyAnimation, QRect, QTimer
from PyQt6.QtGui import QColor, QShortcut, QKeySequence

# --- Sessiz Mod / Logging Anahtarı ---
import builtins as _builtins
VERBOSE = True  # Terminale log akışını açmak için True yapın

def _noop_print(*args, **kwargs):
    pass

def set_verbose(flag: bool):
    global print
    if flag:
        print = _builtins.print
    else:
        print = _noop_print

# Varsayılan: sessiz
set_verbose(VERBOSE)

# Firebase kütüphanelerini import edin (simülasyon modu)
try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
    print("✅ Firebase kütüphanesi yüklü")
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase kütüphanesi bulunamadı. Çevrimdışı modda çalışıyor.")

# -----------------------------
# Camera Panel (simüle kutu)
# -----------------------------
class CameraPanel(QLabel):
    def __init__(self, camera_name: str):
        super().__init__()
        self.setMinimumSize(420, 300)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setProperty("class", "camera-tile")
        self.setText(f"""
            <div style="font-weight:800;font-size:18px;letter-spacing:.5px">
                {camera_name}<br>
                <span style="opacity:.8;font-size:14px">Simüle Edilmiş<br>Görüntü</span>
            </div>
        """)
        shadow = QGraphicsDropShadowEffect(blurRadius=24, xOffset=0, yOffset=8)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)

# -----------------------------
# Sensör verisi üretici thread
# -----------------------------
class SensorThread(QThread):
    sensor_data = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = True
        
    def run(self):
        while self.running:
            # Firebase'den sensör verilerini almaya çalış
            if FIREBASE_AVAILABLE:
                try:
                    import firebase_admin
                    from firebase_admin import db
                    
                    # Firebase'den sensör verilerini çek
                    ref = db.reference('sensors')
                    firebase_data = ref.get()
                    
                    if firebase_data:
                        print(f"📊 Firebase'den sensör verisi alındı: {firebase_data}")
                        self.sensor_data.emit(firebase_data)
                    else:
                        print("⚠️ Firebase 'sensors' yolunda veri yok")
                        
                except Exception as e:
                    print(f"❌ Firebase sensör veri alma hatası: {e}")
            
            self.msleep(1000)  # 1 saniye bekle

    def stop(self):
        self.running = False

# -----------------------------
# Firebase Thread (mevcut entegrasyonu koru)
# -----------------------------
class FirebaseThread(QThread):
    data_received = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.firebase_initialized = False
        
    def initialize_firebase(self):
        if not FIREBASE_AVAILABLE:
            print("⚠️ Firebase yüklü değil; bağlantı kapalı")
            return False
            
        try:
            # Firebase zaten başlatılmışsa sadece bağlantıyı kontrol et
            if firebase_admin._apps:
                self.firebase_initialized = True
                print("✅ Firebase zaten başlatılmış!")
                return True
                
            # Firebase'i başlat
            cred = credentials.Certificate('firebase-credentials.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://ikaarayu-default-rtdb.firebaseio.com/'
            })
            self.firebase_initialized = True
            print("✅ Firebase başarıyla başlatıldı!")
            return True
        except Exception as e:
            print(f"❌ Firebase başlatma hatası: {e}")
            print("🔄 Firebase yeniden denenecek...")
            self.firebase_initialized = False
            return False
    
    def run(self):
        if not self.initialize_firebase():
            # Simülasyon yok: bağlantı kurulana kadar bekle ve tekrar dene
            while self.running and not self.initialize_firebase():
                self.msleep(1000)
        else:
            # Gerçek Firebase modu
            ref = db.reference()
            while self.running:
                try:
                    # Sensör verilerini al
                    sensors = ref.child('sensors').get()
                    if sensors:
                        self.data_received.emit({'type': 'sensors', 'data': sensors})
                    
                    # Kontrol verilerini al
                    control = ref.child('control').get()
                    if control:
                        self.data_received.emit({'type': 'control', 'data': control})
                    
                    # Vites verisini al (ayrı düğüm)
                    gear = ref.child('gear').get()
                    if gear:
                        self.data_received.emit({'type': 'gear', 'data': gear})
                    
                    # Komut verilerini al
                    commands = ref.child('commands').get()
                    if commands:
                        self.data_received.emit({'type': 'commands', 'data': commands})
                    
                    # Lazer verilerini al
                    laser = ref.child('laser').get()
                    if laser:
                        self.data_received.emit({'type': 'laser', 'data': laser})
                    
                    # Acil durum verilerini al
                    emergency = ref.child('emergency').get()
                    if emergency:
                        self.data_received.emit({'type': 'emergency', 'data': emergency})
                    
                    self.msleep(100)  # 10 FPS
                    
                except Exception as e:
                    print(f"Firebase veri alma hatası: {e}")
                    self.msleep(1000)
    
    def stop(self):
        self.running = False

# -----------------------------
# Ana Pencere
# -----------------------------
class IKADashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.laser_mode = False
        self.current_theme = "NeoDark"
        self.firebase_initialized = False
        self.setWindowTitle("İKA Kontrol Arayüzü — Geniş Kameralar")
        self._base_title = self.windowTitle()
        
        # Ekran boyutunu al ve pencereyi uygun şekilde boyutlandır
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_width = min(1600, screen_geometry.width() - 100)
        window_height = min(900, screen_geometry.height() - 100)
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        
        self.setGeometry(x, y, window_width, window_height)

        self.build_ui()
        self.setup_shortcuts()
        self.build_sensors()
        self.init_firebase()
        self.apply_theme(self.current_theme)
        self.show()

    # ---------- Tema QSS'leri ----------
    def neo_dark_qss(self):
        return """
        * { font-family: 'Segoe UI', 'Inter', 'Arial'; }
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0b1020, stop:1 #0a0f1a);
        }
        /* Top Bar */
        #TopBar {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0e1726, stop:1 #0a1020);
            border-bottom: 1px solid #0f1d3a;
        }
        QLabel#Title {
            color:#e2e8f0; font-weight:900; font-size:18px; letter-spacing:.8px;
        }
        QLabel#Badge {
            color:#94a3b8; background: rgba(30,41,59,.35);
            padding:6px 10px; border-radius:999px; border:1px solid #1e293b;
            font-weight:700; font-size:12px;
        }
        QPushButton#TopBtn {
            background: rgba(15,23,42,.6);
            border: 1px solid #1f2a44; color:#cbd5e1;
            border-radius: 10px; padding:8px 12px; font-weight:700;
        }
        QPushButton#TopBtn:hover { background: rgba(30,41,59,.9); border-color:#334155; }
        /* Group Cards */
        QGroupBox {
            color:#e5e7eb; font-weight:800; font-size:16px;
            border: 1px solid #1f2a44; border-radius: 16px;
            margin-top: 16px; padding-top: 18px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(17,24,39,.65), stop:1 rgba(2,6,23,.65));
        }
        QGroupBox::title {
            subcontrol-origin: margin; left:16px; padding:0 10px;
            background: rgba(15,23,42,.9);
            border:1px solid #1f2a44; border-radius:10px;
        }
        QLabel { color:#cbd5e1; font-weight:700; font-size:14px; }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #12213f, stop:1 #0c1a33);
            border: 1px solid #1e335a; border-radius: 12px;
            color: #e5e7eb; font-weight: 800; padding: 10px 12px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1c2f5a, stop:1 #12213f);
            border-color: #3b82f6;
        }
        QPushButton:pressed { background:#0b1730; border-color:#0b1730; }
        QPushButton#emergency {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #991b1b, stop:1 #7f1d1d);
            border: 2px solid #b91c1c; color:#fee2e2;
            font-size: 18px; border-radius: 18px; padding:14px;
        }
        QPushButton#emergency:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #dc2626, stop:1 #b91c1c);
            border: 3px solid #ef4444; color:#fff;
        }
        QPushButton#laser {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #7c2d12, stop:1 #7f1d1d);
            border: 1px solid #b45309;
        }
        QPushButton#laser:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ea580c, stop:1 #b45309);
            border: 2px solid #f59e0b; color:#fff;
        }
        QLCDNumber {
            background:#0b1325; color:#22d3ee;
            border:1px solid #1e335a; border-radius:10px;
        }
        QLabel[class~="camera-tile"] {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0b1730, stop:1 #0b1120);
            border:1px solid #1e335a; border-radius:16px;
        }
        #BottomBar {
            background: rgba(2,6,23,.6);
            border-top: 1px solid #1f2a44;
        }
        QProgressBar {
            background: #0b1325; border:1px solid #1e335a;
            border-radius:8px; color:#e5e7eb; text-align:center;
        }
        QProgressBar::chunk { background:#16a34a; border-radius:8px; }
        """

    def glass_qss(self):
        return """
        * { font-family: 'Segoe UI', 'Inter', 'Arial'; }
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0f172a, stop:1 #111827);
        }
        #TopBar {
            background: rgba(255,255,255,.06);
            border-bottom: 1px solid rgba(255,255,255,.08);
        }
        QLabel#Title { color:#f8fafc; font-weight:900; font-size:18px; letter-spacing:.8px; }
        QLabel#Badge {
            color:#e5e7eb; background: rgba(255,255,255,.08);
            padding:6px 10px; border-radius:999px; border:1px solid rgba(255,255,255,.12);
            font-weight:700; font-size:12px;
        }
        QPushButton#TopBtn {
            background: rgba(255,255,255,.06);
            border: 1px solid rgba(255,255,255,.12);
            color:#e5e7eb; border-radius: 10px; padding:8px 12px; font-weight:700;
        }
        QPushButton#TopBtn:hover { background: rgba(255,255,255,.1); }
        QGroupBox {
            color:#f3f4f6; font-weight:900; font-size:16px;
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 20px; margin-top: 18px; padding-top: 20px;
            background: rgba(255,255,255,.06);
        }
        QGroupBox::title {
            subcontrol-origin: margin; left:16px; padding:0 10px;
            background: rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.12);
            border-radius:10px;
        }
        QLabel { color:#e2e8f0; font-weight:800; font-size:14px; }
        QPushButton {
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 12px; color:#f8fafc; font-weight:900; padding:10px 12px;
        }
        QPushButton:hover { background: rgba(255,255,255,.14); }
        QPushButton:pressed { background: rgba(255,255,255,.2); }
        QPushButton#emergency {
            background: rgba(239,68,68,.2); border-color: rgba(239,68,68,.5);
            color:#fee2e2; font-size:18px; border-radius:18px; padding:14px;
        }
        QPushButton#laser {
            background: rgba(234,88,12,.2); border-color: rgba(234,88,12,.5);
        }
        QPushButton#emergency:checked {
            background: rgba(239,68,68,.35); border-color: rgba(239,68,68,.7);
            color:#fff;
        }
        QPushButton#laser:checked {
            background: rgba(234,88,12,.35); border-color: rgba(234,88,12,.7);
            color:#fff;
        }
        QLCDNumber {
            background: rgba(2,6,23,.6); color:#22d3ee;
            border: 1px solid rgba(255,255,255,.12); border-radius: 10px;
        }
        QLabel[class~="camera-tile"] {
            background: rgba(255,255,255,.06);
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 18px;
        }
        #BottomBar {
            background: rgba(255,255,255,.06);
            border-top: 1px solid rgba(255,255,255,.12);
        }
        QProgressBar {
            background: rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12);
            border-radius:8px; color:#e5e7eb; text-align:center;
        }
        QProgressBar::chunk { background: rgba(34,197,94,.9); border-radius:8px; }
        """

    def apply_theme(self, name: str):
        if name == "NeoDark":
            self.setStyleSheet(self.neo_dark_qss())
        else:
            self.setStyleSheet(self.glass_qss())

    # ---------- UI KURULUMU ----------
    def build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        # ORTA BÖLGE — 2 sütun
        middle_wrap = QWidget()
        middle = QHBoxLayout(middle_wrap)
        middle.setContentsMargins(12, 12, 12, 12)
        middle.setSpacing(20)

        # Sol: Kameralar
        left = self.create_camera_panel()
        middle.addWidget(left, 4)

        # Sağ: Kontroller + Sensörler
        right = self.create_control_panel()
        middle.addWidget(right, 1)

        # Topla
        root.addWidget(middle_wrap, 1)

        # İlk gösterimde düzeni zorla ve animasyonu daha sonra başlatmak için referansı sakla
        self._middle_wrap = middle_wrap

    def reveal_anim(self, widget):
        anim = QPropertyAnimation(widget, b"geometry")
        start_rect = QRect(widget.x(), widget.y() + 30, widget.width(), widget.height())
        anim.setDuration(380)
        anim.setStartValue(start_rect)
        anim.setEndValue(widget.geometry())
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._reveal_anim = anim  # referansı sakla

    def _force_initial_layout(self):
        # Pencere gösterildikten sonra düzeni etkinleştirip boyutlandırmayı kesinleştir
        if self._middle_wrap is not None:
            lay = self._middle_wrap.layout()
            if lay is not None:
                lay.activate()
        self.updateGeometry()
        QApplication.processEvents()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, "_first_shown"):
            self._first_shown = True
            # Düzenin tamamlanması ve doğru ölçümlerin alınması için bir sonraki döngüde çalıştır
            QTimer.singleShot(0, lambda: (self._force_initial_layout(), self.reveal_anim(self._middle_wrap)))

    # ---------- Paneller ----------
    def create_camera_panel(self):
        panel = QGroupBox("📹 Kamera Görüntüleri")
        layout = QVBoxLayout(panel)
        layout.setSpacing(14)

        # Üst satır: ön kamera (geniş) + sağda dar vites kutusu
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        self.front_camera = CameraPanel("Ön Kamera")
        self.front_camera.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        top_row.addWidget(self.front_camera, 1)

        self.gear_group = self.create_gear_group()
        self.gear_group.setMaximumWidth(140)
        top_row.addWidget(self.gear_group, 0)

        layout.addLayout(top_row)

        # Alt satır: lazer ve arka kamera yan yana eşit genişlikte
        grid = QGridLayout()
        grid.setSpacing(14)

        self.laser_camera = CameraPanel("Lazer Atış Kamera")
        self.back_camera = CameraPanel("Arka Kamera")
        self.laser_camera.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.back_camera.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        grid.addWidget(self.laser_camera, 0, 0)
        grid.addWidget(self.back_camera, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        layout.addLayout(grid)
        return panel

    def create_gear_group(self):
        group = QGroupBox("Vites")
        g = QGridLayout(group); g.setSpacing(6)

        # 1, 2, B (Boş), G (Geri)
        self.gear1_btn = QPushButton("1"); self.gear1_btn.setMinimumSize(70, 40); self.gear1_btn.setCheckable(True)
        self.gear2_btn = QPushButton("2"); self.gear2_btn.setMinimumSize(70, 40); self.gear2_btn.setCheckable(True)
        self.gearB_btn = QPushButton("B"); self.gearB_btn.setMinimumSize(70, 40); self.gearB_btn.setCheckable(True)
        self.gearG_btn = QPushButton("G"); self.gearG_btn.setMinimumSize(90, 60); self.gearG_btn.setCheckable(True)

        for btn, gr in [
            (self.gear1_btn, "1"),
            (self.gear2_btn, "2"),
            (self.gearB_btn, "B"),
            (self.gearG_btn, "G"),
        ]:
            btn.setStyleSheet("font-size:14px;font-weight:900;")
            btn.clicked.connect(lambda _, gear=gr: self.set_gear(gear))

        # Dikey dizilim ve altta büyük G
        g.addWidget(self.gear1_btn, 0, 0)
        g.addWidget(self.gear2_btn, 1, 0)
        g.addWidget(self.gearB_btn, 2, 0)
        g.addWidget(self.gearG_btn, 3, 0)
        return group

    def create_sensor_panel(self):
        panel = QGroupBox("Sensör Verileri")
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        panel.setStyleSheet("QLabel { font-size:12px; }")

        # IMU (ivme verileri kaldırıldı) — başlıksız, kompakt
        imu_group = QWidget()
        imu = QGridLayout(imu_group); imu.setSpacing(6); imu.setContentsMargins(0, 0, 0, 0)

        self.roll_lcd = QLCDNumber(); self.roll_lcd.setDigitCount(6)
        self.pitch_lcd = QLCDNumber(); self.pitch_lcd.setDigitCount(6)
        self.yaw_lcd = QLCDNumber(); self.yaw_lcd.setDigitCount(6)

        imu.addWidget(QLabel("Roll (°):"), 0, 0); imu.addWidget(self.roll_lcd, 0, 1)
        imu.addWidget(QLabel("Pitch (°):"), 1, 0); imu.addWidget(self.pitch_lcd, 1, 1)
        imu.addWidget(QLabel("Yaw (°):"), 2, 0); imu.addWidget(self.yaw_lcd, 2, 1)

        layout.addWidget(imu_group)

        # GPS — başlıksız, kompakt
        gps_group = QWidget()
        gps = QGridLayout(gps_group); gps.setSpacing(6); gps.setContentsMargins(0, 0, 0, 0)

        self.lat_lcd = QLCDNumber(); self.lat_lcd.setDigitCount(9)
        self.lon_lcd = QLCDNumber(); self.lon_lcd.setDigitCount(9)
        self.alt_lcd = QLCDNumber(); self.alt_lcd.setDigitCount(6)
        self.speed_lcd = QLCDNumber(); self.speed_lcd.setDigitCount(6)

        gps.addWidget(QLabel("Latitude:"), 0, 0); gps.addWidget(self.lat_lcd, 0, 1)
        gps.addWidget(QLabel("Longitude:"), 1, 0); gps.addWidget(self.lon_lcd, 1, 1)
        gps.addWidget(QLabel("Altitude (m):"), 2, 0); gps.addWidget(self.alt_lcd, 2, 1)
        gps.addWidget(QLabel("Speed (km/h):"), 3, 0); gps.addWidget(self.speed_lcd, 3, 1)

        layout.addWidget(gps_group)
        layout.addStretch()
        return panel

    def create_control_panel(self):
        panel = QGroupBox("Kontrol Paneli")
        layout = QVBoxLayout(panel)
        layout.setSpacing(6)

        # Acil Durdur
        self.emergency_btn = QPushButton("🚨 ACİL DURDUR")
        self.emergency_btn.setObjectName("emergency")
        self.emergency_btn.setCheckable(True)
        self.emergency_btn.clicked.connect(self.emergency_stop)
        layout.addWidget(self.emergency_btn)

        # Modlar
        mode_group = QGroupBox("Kontrol Modu")
        mode_l = QHBoxLayout(mode_group); mode_l.setSpacing(8)

        self.manual_btn = QPushButton("Manuel"); self.manual_btn.setCheckable(True); self.manual_btn.setChecked(True)
        self.semi_auto_btn = QPushButton("Yarı Otonom"); self.semi_auto_btn.setCheckable(True)
        self.auto_btn = QPushButton("Otonom"); self.auto_btn.setCheckable(True)

        self.manual_btn.clicked.connect(lambda: self.set_control_mode("manual"))
        self.semi_auto_btn.clicked.connect(lambda: self.set_control_mode("semi"))
        self.auto_btn.clicked.connect(lambda: self.set_control_mode("auto"))

        mode_l.addWidget(self.manual_btn)
        mode_l.addWidget(self.semi_auto_btn)
        mode_l.addWidget(self.auto_btn)
        layout.addWidget(mode_group)

        # Lazer Toggle
        self.laser_btn = QPushButton("LAZER ATIŞ MODU")
        self.laser_btn.setObjectName("laser")
        self.laser_btn.setCheckable(True)
        self.laser_btn.clicked.connect(self.toggle_laser_mode)
        layout.addWidget(self.laser_btn)

        # Yön kontrol
        self.direction_group = QGroupBox("Yön Kontrolü")
        d = QGridLayout(self.direction_group); d.setSpacing(6)
        d.setContentsMargins(0, 0, 0, 0)
        d.setRowStretch(3, 1)

        self.up_btn = QPushButton("▲\nİleri"); self.up_btn.setMinimumSize(70, 70)
        self.down_btn = QPushButton("▼\nGeri"); self.down_btn.setMinimumSize(70, 70)
        self.left_btn = QPushButton("◄\nSol"); self.left_btn.setMinimumSize(70, 70)
        self.right_btn = QPushButton("►\nSağ"); self.right_btn.setMinimumSize(70, 70)

        for b, name in [(self.up_btn,"up"),(self.down_btn,"down"),(self.left_btn,"left"),(self.right_btn,"right")]:
            b.setStyleSheet("font-size:14px;font-weight:900;")
            b.clicked.connect(lambda _, nm=name: self.direction_pressed(nm))

        d.addWidget(self.up_btn, 0, 1)
        d.addWidget(self.left_btn, 1, 0)
        d.addWidget(self.right_btn, 1, 2)
        d.addWidget(self.down_btn, 2, 1)
        layout.addWidget(self.direction_group)

        # Vites kontrolü artık kamera paneline taşındı

        # Lazer yön kontrol (başta gizli)
        self.laser_direction_group = QGroupBox("Lazer Yön Kontrolü")
        ld = QGridLayout(self.laser_direction_group); ld.setSpacing(6)

        self.laser_up_btn = QPushButton("▲\nLazer Yukarı"); self.laser_up_btn.setMinimumSize(70, 70)
        self.laser_down_btn = QPushButton("▼\nLazer Aşağı"); self.laser_down_btn.setMinimumSize(70, 70)
        self.laser_left_btn = QPushButton("◄\nLazer Sol"); self.laser_left_btn.setMinimumSize(70, 70)
        self.laser_right_btn = QPushButton("►\nLazer Sağ"); self.laser_right_btn.setMinimumSize(70, 70)
        self.laser_fire_btn = QPushButton("🔥\nATEŞ!"); self.laser_fire_btn.setMinimumSize(70, 70)

        redish = "font-size:12px;font-weight:900;"
        for b, nm in [
            (self.laser_up_btn,"up"), (self.laser_down_btn,"down"),
            (self.laser_left_btn,"left"), (self.laser_right_btn,"right")
        ]:
            b.setStyleSheet(redish)
            b.clicked.connect(lambda _, name=nm: self.laser_direction_pressed(name))

        self.laser_fire_btn.setStyleSheet("font-size:14px;font-weight:1000;")
        self.laser_fire_btn.clicked.connect(self.laser_fire)

        ld.addWidget(self.laser_up_btn, 0, 1)
        ld.addWidget(self.laser_left_btn, 1, 0)
        ld.addWidget(self.laser_fire_btn, 1, 1)
        ld.addWidget(self.laser_right_btn, 1, 2)
        ld.addWidget(self.laser_down_btn, 2, 1)

        layout.addWidget(self.laser_direction_group)
        self.laser_direction_group.hide()

        # Sensör verileri kontrol panelinin altına eklendi
        sensor_panel = self.create_sensor_panel()
        layout.addWidget(sensor_panel)

        layout.addStretch()

        return panel

    # ---------- Klavye Kısayolları ----------
    def setup_shortcuts(self):
        # Yön tuşlarını hem normal sürüşte hem lazer modunda kullan
        self._sc_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self._sc_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self._sc_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self._sc_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        for sc in [self._sc_up, self._sc_down, self._sc_left, self._sc_right]:
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)

        self._sc_up.activated.connect(lambda: self._arrow_trigger("up"))
        self._sc_down.activated.connect(lambda: self._arrow_trigger("down"))
        self._sc_left.activated.connect(lambda: self._arrow_trigger("left"))
        self._sc_right.activated.connect(lambda: self._arrow_trigger("right"))

        # Vites kısayolları: 1,2,3 ve G
        self._sc_1 = QShortcut(QKeySequence(Qt.Key.Key_1), self)
        self._sc_2 = QShortcut(QKeySequence(Qt.Key.Key_2), self)
        self._sc_b = QShortcut(QKeySequence(Qt.Key.Key_B), self)
        self._sc_g = QShortcut(QKeySequence(Qt.Key.Key_G), self)
        for sc in [self._sc_1, self._sc_2, self._sc_b, self._sc_g]:
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)

        self._sc_1.activated.connect(lambda: self._gear_trigger("1"))
        self._sc_2.activated.connect(lambda: self._gear_trigger("2"))
        self._sc_b.activated.connect(lambda: self._gear_trigger("B"))
        self._sc_g.activated.connect(lambda: self._gear_trigger("G"))

    def _arrow_trigger(self, direction: str):
        # Lazer modu açıkken lazer yön komutlarını, değilken normal yön komutlarını gönder
        if self.laser_mode:
            self.laser_direction_pressed(direction)
        else:
            self.direction_pressed(direction)

    def _gear_trigger(self, gear: str):
        self.set_gear(gear)

    # ---------- Sensörler ----------
    def build_sensors(self):
        self.sensor_thread = SensorThread()
        self.sensor_thread.sensor_data.connect(self.update_sensor_data)
        self.sensor_thread.start()

    def update_sensor_data(self, data):
        self.roll_lcd.display(f"{data['imu']['roll']:.1f}")
        self.pitch_lcd.display(f"{data['imu']['pitch']:.1f}")
        self.yaw_lcd.display(f"{data['imu']['yaw']:.1f}")

        self.lat_lcd.display(f"{data['gps']['latitude']:.6f}")
        self.lon_lcd.display(f"{data['gps']['longitude']:.6f}")
        self.alt_lcd.display(f"{data['gps']['altitude']:.1f}")
        self.speed_lcd.display(f"{data['gps']['speed']:.1f}")

    # ---------- Firebase Entegrasyonu ----------
    def init_firebase(self):
        # Firebase thread'ini başlat (şimdilik devre dışı)
        if FIREBASE_AVAILABLE:
            try:
                self.firebase_thread = FirebaseThread()
                self.firebase_thread.data_received.connect(self.handle_firebase_data)
                self.firebase_thread.start()
                
                # Firebase başlatma
                if self.initialize_firebase():
                    print("✅ Firebase ana thread'de başarıyla başlatıldı!")
                else:
                    print("❌ Firebase ana thread'de başlatılamadı!")
            except Exception as e:
                print(f"⚠️ Firebase thread başlatılamadı: {e}")
                print("📱 Uygulama simülasyon modunda çalışacak")
        else:
            print("📱 Firebase olmadan simülasyon modunda çalışıyor")
    
    def initialize_firebase(self):
        """Firebase'i başlat"""
        if not FIREBASE_AVAILABLE:
            print("⚠️ Firebase yüklü değil; bağlantı kapalı")
            self.firebase_initialized = False
            return False
            
        try:
            # Mevcut Firebase uygulamalarını temizle
            if firebase_admin._apps:
                print("🔄 Mevcut Firebase uygulamaları temizleniyor...")
                for app in firebase_admin._apps.copy().values():
                    firebase_admin.delete_app(app)
            
            # Firebase'i başlat
            cred = credentials.Certificate('firebase-credentials.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://ikaarayu-default-rtdb.firebaseio.com/'
            })
            self.firebase_initialized = True
            print("✅ Firebase başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            print(f"❌ Firebase başlatma hatası: {e}")
            self.firebase_initialized = False
            return False
    
    def send_to_firebase(self, path, data):
        """Firebase'e veri gönder"""
        if not FIREBASE_AVAILABLE:
            print(f"⚠️ Firebase kütüphanesi yüklü değil, veri simüle ediliyor: {path} = {data}")
            return True
            
        if not self.firebase_initialized:
            print(f"⚠️ Firebase bağlantısı yok, veri simüle ediliyor: {path} = {data}")
            return True
            
        try:
            # Acil durum verisi sadece boolean gönderir, zaman damgası ekleme
            if path != 'emergency':
                data['timestamp'] = time.time()
            
            ref = db.reference(path)
            ref.set(data)
            print(f"✅ Firebase'e gönderildi: {path} = {data}")
            return True
        except Exception as e:
            print(f"❌ Firebase veri gönderme hatası: {e}")
            print(f"📝 Veri simüle ediliyor: {path} = {data}")
            return True  # Hata olsa bile uygulamayı çalışmaya devam ettir
    
    def handle_firebase_data(self, firebase_data):
        """Firebase'den gelen verileri işle"""
        data_type = firebase_data.get('type')
        data = firebase_data.get('data')
        
        print(f"📊 Firebase'den veri alındı: Type={data_type}, Data={data}")
        
        if data_type == 'sensors' and data:
            # Firebase'den gelen sensör verilerini UI'da göster
            print(f"📊 Sensör verileri işleniyor: {data}")
            self.update_sensor_data(data)
            
        elif data_type == 'control' and data:
            # Kontrol modunu güncelle
            mode = data.get('mode')
            if mode is not None:
                if mode == 'manual':
                    self.manual_btn.setChecked(True)
                    self.semi_auto_btn.setChecked(False)
                    self.auto_btn.setChecked(False)
                elif mode == 'semi_auto':
                    self.manual_btn.setChecked(False)
                    self.semi_auto_btn.setChecked(True)
                    self.auto_btn.setChecked(False)
                elif mode == 'auto':
                    self.manual_btn.setChecked(False)
                    self.semi_auto_btn.setChecked(False)
                    self.auto_btn.setChecked(True)

        elif data_type == 'gear' and data:
            # Gear düğümü string ya da dict olabilir
            if isinstance(data, dict):
                gear = data.get('gear')
            else:
                gear = str(data)

            if gear is not None:
                mapping = {
                    "1": self.gear1_btn,
                    "2": self.gear2_btn,
                    "B": self.gearB_btn,
                    "G": self.gearG_btn,
                }
                for key, btn in mapping.items():
                    btn.setChecked(key == gear)
        
        elif data_type == 'commands' and data:
            # Yön komutlarını işle
            command = data.get('command', '')
            print(f"🎮 Firebase'den yön komutu: {command}")
        
        elif data_type == 'laser' and data:
            # Lazer komutlarını işle
            command = data.get('command', '')
            print(f"🎯 Firebase'den lazer komutu: {command}")
        
        elif data_type == 'emergency' and data is not None:
            # Acil durum komutunu işle — sadece UI durumunu güncelle, DB'ye tekrar yazma
            val = bool(data.get('emergency', False)) if isinstance(data, dict) else bool(data)
            # Sinyal tetiklenmesini önlemek için geçici bağlantı kesme gerekmiyor;
            # burada sadece görsel durumu set ediyoruz, click sinyali tetiklenmez.
            self.emergency_btn.setChecked(val)
            self.emergency_btn.setText("🚨 ACİL DURDUR AKTİF" if val else "🚨 ACİL DURDUR")

    # ---------- Kontroller ----------
    def emergency_stop(self):
        # Toggle davranışı: buton check durumuna göre True/False gönder
        is_active = self.emergency_btn.isChecked()
        self.emergency_btn.setText("🚨 ACİL DURDUR AKTİF" if is_active else "🚨 ACİL DURDUR")
        if is_active:
            print("🚨 ACİL DURDURMA AKTİF! 🚨")
        else:
            print("✅ Acil durdurma devre dışı")
        self.send_to_firebase('emergency', {'emergency': bool(is_active)})

    def set_control_mode(self, mode):
        if mode == "manual":
            self.semi_auto_btn.setChecked(False)
            self.auto_btn.setChecked(False)
            print("👤 Manuel kontrol modu aktif")
            self.send_to_firebase('control', {'mode': 'manual'})
        elif mode == "semi":
            self.manual_btn.setChecked(False)
            self.auto_btn.setChecked(False)
            print("🤖 Yarı otonom kontrol modu aktif")
            self.send_to_firebase('control', {'mode': 'semi_auto'})
        elif mode == "auto":
            self.manual_btn.setChecked(False)
            self.semi_auto_btn.setChecked(False)
            print("🛰️ Otonom kontrol modu aktif")
            self.send_to_firebase('control', {'mode': 'auto'})

    def toggle_laser_mode(self):
        # Checkable butona bağla: true ise lazer modu
        self.laser_mode = self.laser_btn.isChecked()
        if self.laser_mode:
            self.direction_group.hide()
            self.laser_direction_group.show()
            self.laser_btn.setText("🔄 NORMAL MODA DÖN")
            print("Lazer atış modu aktif")
        else:
            self.laser_direction_group.hide()
            self.direction_group.show()
            self.laser_btn.setText("LAZER ATIŞ MODU")
            print("Normal moda dönüldü")

    def direction_pressed(self, direction):
        print(f"Yön komutu: {direction}")
        # Firebase'e yön komutu gönder
        self.send_to_firebase('commands', {'command': direction})
        self._flash_title(f"Yön: {direction}")

    def set_gear(self, gear: str):
        # Görsel geri bildirim: sadece seçilen vites aktif
        mapping = {
            "1": self.gear1_btn,
            "2": self.gear2_btn,
            "B": self.gearB_btn,
            "G": self.gearG_btn,
        }
        for key, btn in mapping.items():
            btn.setChecked(key == gear)

        print(f"Vites seçildi: {gear}")
        # Firebase'e vites bilgisini ayrı 'gear' düğümüne gönder
        self.send_to_firebase('gear', {'gear': gear})
        self._flash_title(f"Vites: {gear}")

    def _flash_title(self, text: str):
        # Durumu kısa süre pencerede göster, sonra geri al
        self.setWindowTitle(f"{self._base_title} — {text}")
        QTimer.singleShot(1500, lambda: self.setWindowTitle(self._base_title))

    def laser_direction_pressed(self, direction):
        print(f" Lazer yön komutu: {direction}")
        # Firebase'e lazer yön komutu gönder
        self.send_to_firebase('laser', {'command': direction})

    def laser_fire(self):
        print(" LAZER ATEŞLENDİ! ")
        # Firebase'e lazer ateşleme komutu gönder
        self.send_to_firebase('laser', {'command': 'fire'})

    def toggle_theme(self):
        self.current_theme = "Glass" if self.current_theme == "NeoDark" else "NeoDark"
        self.apply_theme(self.current_theme)

    def closeEvent(self, event):
        self.sensor_thread.stop()
        self.firebase_thread.stop()
        self.sensor_thread.wait()
        self.firebase_thread.wait()
        event.accept()

    def test_firebase_connection(self):
        """Firebase bağlantısını test et"""
        if not self.firebase_initialized:
            print("❌ Firebase bağlantısı yok!")
            return False
            
        try:
            # Test verisi gönder
            test_data = {'test': True, 'timestamp': time.time()}
            ref = db.reference('test_connection')
            ref.set(test_data)
            print("✅ Firebase bağlantı testi başarılı!")
            
            # Test verisini sil
            ref.delete()
            return True
        except Exception as e:
            print(f"❌ Firebase bağlantı testi başarısız: {e}")
            return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = IKADashboard()
    win.show()
    sys.exit(app.exec())
