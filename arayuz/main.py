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

def _noop_print(*args, **kwargs):
    pass

# Tüm print'leri sustur
print = _noop_print

# Firebase kütüphanelerini import edin (simülasyon modu)
try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

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
# Sensör verisi üretici thread (Firebase entegrasyonu ile)
# -----------------------------
class SensorThread(QThread):
    sensor_data = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = True
        self.firebase_initialized = False
        
    def run(self):
        while self.running:
            # Firebase'den sensör verilerini almaya çalış
            if FIREBASE_AVAILABLE and self.firebase_initialized:
                try:
                    # Firebase'den sensör verilerini çek
                    ref = db.reference('sensors')
                    firebase_data = ref.get()
                    
                    if firebase_data:
                        self.sensor_data.emit(firebase_data)
                        
                except Exception as e:
                    pass
            
            self.msleep(1000)  # 1 saniye bekle
    

    
    def set_firebase_initialized(self, status: bool):
        """Firebase durumunu güncelle"""
        self.firebase_initialized = status

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
            return False
            
        try:
            # Firebase zaten başlatılmışsa sadece bağlantıyı kontrol et
            if firebase_admin._apps:
                self.firebase_initialized = True
                return True
                
            # Firebase'i başlat
            cred = credentials.Certificate('ika-db-eb609-firebase-adminsdk-fbsvc-96c3b83edc.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://ika-db-eb609-default-rtdb.europe-west1.firebasedatabase.app/'
            })
            self.firebase_initialized = True
            return True
        except Exception as e:
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
                    else:
                        # Sensör verisi yoksa bunu bildir
                        self.data_received.emit({'type': 'sensors_empty', 'data': None})
                    
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

        self.left_btn = QPushButton("◄\nSol"); self.left_btn.setMinimumSize(70, 70)
        self.right_btn = QPushButton("►\nSağ"); self.right_btn.setMinimumSize(70, 70)

        for b, name in [(self.up_btn,"up"),(self.left_btn,"left"),(self.right_btn,"right")]:
            b.setStyleSheet("font-size:14px;font-weight:900;")
            b.clicked.connect(lambda _, nm=name: self.direction_pressed(nm))

        d.addWidget(self.up_btn, 0, 1)
        d.addWidget(self.left_btn, 1, 0)
        d.addWidget(self.right_btn, 1, 2)
        layout.addWidget(self.direction_group)

        # Vites kontrolü artık kamera paneline taşındı

        # Lazer yön kontrol (başta gizli)
        self.laser_direction_group = QGroupBox("Lazer Yön Kontrolü")
        ld = QGridLayout(self.laser_direction_group); ld.setSpacing(6)

        self.laser_up_btn = QPushButton("▲\nYukarı"); self.laser_up_btn.setMinimumSize(70, 70)
        self.laser_down_btn = QPushButton("▼\nAşağı"); self.laser_down_btn.setMinimumSize(70, 70)
        self.laser_left_btn = QPushButton("◄\nSol"); self.laser_left_btn.setMinimumSize(70, 70)
        self.laser_right_btn = QPushButton("►\nSağ"); self.laser_right_btn.setMinimumSize(70, 70)
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

        self._sc_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self._sc_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        for sc in [self._sc_up, self._sc_left, self._sc_right]:
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)

        self._sc_up.activated.connect(lambda: self._arrow_trigger("up"))

        self._sc_left.activated.connect(lambda: self._arrow_trigger("left"))
        self._sc_right.activated.connect(lambda: self._arrow_trigger("right"))

        # Vites kısayolları: 1,2,B ve G
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

        # Lazer ateşleme kısayolu: Space (Boşluk)
        self._sc_fire = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self._sc_fire.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._sc_fire.activated.connect(self._fire_trigger)

        # Lazer modu toggle: L tuşu
        self._sc_laser = QShortcut(QKeySequence(Qt.Key.Key_L), self)
        self._sc_laser.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._sc_laser.activated.connect(self._laser_toggle_trigger)

        # Acil durdurma: E tuşu
        self._sc_emergency = QShortcut(QKeySequence(Qt.Key.Key_E), self)
        self._sc_emergency.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._sc_emergency.activated.connect(self._emergency_trigger)

        # Kontrol modları: M (Manuel), S (Semi), A (Auto)
        self._sc_manual = QShortcut(QKeySequence(Qt.Key.Key_M), self)
        self._sc_semi = QShortcut(QKeySequence(Qt.Key.Key_S), self)
        self._sc_auto = QShortcut(QKeySequence(Qt.Key.Key_A), self)
        
        for sc in [self._sc_manual, self._sc_semi, self._sc_auto]:
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        self._sc_manual.activated.connect(lambda: self._control_mode_trigger("manual"))
        self._sc_semi.activated.connect(lambda: self._control_mode_trigger("semi"))
        self._sc_auto.activated.connect(lambda: self._control_mode_trigger("auto"))

    def _arrow_trigger(self, direction: str):
        # Lazer modu açıkken lazer yön komutlarını, değilken normal yön komutlarını gönder
        if self.laser_mode:
            self.laser_direction_pressed(direction)
        else:
            self.direction_pressed(direction)
        
        # Görsel geri bildirim - ilgili butonu vurgula
        self._highlight_button(direction)

    def _highlight_button(self, direction: str):
        """Tuşa basınca ilgili butonu vurgula"""
        # Buton eşleştirmeleri
        button_map = {
            'up': self.up_btn,
            'left': self.left_btn,
            'right': self.right_btn
        }
        
        if direction in button_map:
            button = button_map[direction]
            # Butonu kısa süre vurgula - hover efekti gibi kenarlık
            original_style = button.styleSheet()
            button.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            
            # 200ms sonra normal haline döndür
            QTimer.singleShot(200, lambda: button.setStyleSheet(original_style))

    def _gear_trigger(self, gear: str):
        self.set_gear(gear)
        
        # Görsel geri bildirim - ilgili vites butonunu vurgula
        self._highlight_gear_button(gear)

    def _highlight_gear_button(self, gear: str):
        """Vites tuşuna basınca ilgili butonu vurgula"""
        # Vites buton eşleştirmeleri
        gear_button_map = {
            '1': self.gear1_btn,
            '2': self.gear2_btn,
            'B': self.gearB_btn,
            'G': self.gearG_btn
        }
        
        if gear in gear_button_map:
            button = gear_button_map[gear]
            # Butonu kısa süre vurgula - hover efekti gibi kenarlık
            original_style = button.styleSheet()
            button.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            
            # 200ms sonra normal haline döndür
            QTimer.singleShot(200, lambda: button.setStyleSheet(original_style))

    def _fire_trigger(self):
        """Lazer ateşleme kısayolu"""
        if self.laser_mode:
            self.laser_fire()
            # Görsel geri bildirim
            self._highlight_laser_fire_button()

    def _highlight_laser_fire_button(self):
        """Lazer ateşleme butonunu vurgula"""
        if hasattr(self, 'laser_fire_btn'):
            original_style = self.laser_fire_btn.styleSheet()
            self.laser_fire_btn.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            QTimer.singleShot(200, lambda: self.laser_fire_btn.setStyleSheet(original_style))

    def _laser_toggle_trigger(self):
        """Lazer modu toggle kısayolu"""
        self.laser_btn.click()
        # Görsel geri bildirim
        self._highlight_laser_toggle_button()

    def _highlight_laser_toggle_button(self):
        """Lazer toggle butonunu vurgula"""
        original_style = self.laser_btn.styleSheet()
        self.laser_btn.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
        QTimer.singleShot(200, lambda: self.laser_btn.setStyleSheet(original_style))

    def _emergency_trigger(self):
        """Acil durdurma kısayolu"""
        self.emergency_btn.click()
        # Görsel geri bildirim
        self._highlight_emergency_button()

    def _highlight_emergency_button(self):
        """Acil durdurma butonunu vurgula"""
        original_style = self.emergency_btn.styleSheet()
        self.emergency_btn.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
        QTimer.singleShot(200, lambda: self.emergency_btn.setStyleSheet(original_style))

    def _control_mode_trigger(self, mode: str):
        """Kontrol modu kısayolu"""
        self.set_control_mode(mode)
        # Görsel geri bildirim
        self._highlight_control_mode_button(mode)

    def _highlight_control_mode_button(self, mode: str):
        """Kontrol modu butonunu vurgula"""
        mode_button_map = {
            'manual': self.manual_btn,
            'semi': self.semi_auto_btn,
            'auto': self.auto_btn
        }
        
        if mode in mode_button_map:
            button = mode_button_map[mode]
            original_style = button.styleSheet()
            button.setStyleSheet(original_style + "; border: 3px solid #4ecdc4; border-radius: 8px;")
            QTimer.singleShot(200, lambda: button.setStyleSheet(original_style))



    # ---------- Sensörler ----------
    def build_sensors(self):
        self.sensor_thread = SensorThread()
        self.sensor_thread.sensor_data.connect(self.update_sensor_data)
        # Başlangıçta simülasyon modunda başla
        self.sensor_thread.set_firebase_initialized(False)
        self.sensor_thread.start()

    def update_sensor_data(self, data):
        """Sensör verilerini UI'da güncelle"""
        try:
            # IMU verilerini güncelle
            if 'imu' in data and isinstance(data['imu'], dict):
                imu = data['imu']
                if 'roll' in imu:
                    self.roll_lcd.display(f"{float(imu['roll']):.1f}")
                if 'pitch' in imu:
                    self.pitch_lcd.display(f"{float(imu['pitch']):.1f}")
                if 'yaw' in imu:
                    self.yaw_lcd.display(f"{float(imu['yaw']):.1f}")
            
            # GPS verilerini güncelle
            if 'gps' in data and isinstance(data['gps'], dict):
                gps = data['gps']
                if 'latitude' in gps:
                    self.lat_lcd.display(f"{float(gps['latitude']):.6f}")
                if 'longitude' in gps:
                    self.lon_lcd.display(f"{float(gps['longitude']):.6f}")
                if 'altitude' in gps:
                    self.alt_lcd.display(f"{float(gps['altitude']):.1f}")
                if 'speed' in gps:
                    self.speed_lcd.display(f"{float(gps['speed']):.1f}")
            
            
        except Exception as e:
            pass

    # ---------- Firebase Entegrasyonu ----------
    def init_firebase(self):
        # Firebase thread'ini başlat
        if FIREBASE_AVAILABLE:
            try:
                self.firebase_thread = FirebaseThread()
                self.firebase_thread.data_received.connect(self.handle_firebase_data)
                self.firebase_thread.start()
                
                # Firebase başlatma
                if self.initialize_firebase():
                    # SensorThread'e Firebase durumunu bildir
                    if hasattr(self, 'sensor_thread'):
                        self.sensor_thread.set_firebase_initialized(True)
                else:
                    # SensorThread'e Firebase durumunu bildir
                    if hasattr(self, 'sensor_thread'):
                        self.sensor_thread.set_firebase_initialized(False)
            except Exception as e:
                # SensorThread'e Firebase durumunu bildir
                if hasattr(self, 'sensor_thread'):
                    self.sensor_thread.set_firebase_initialized(False)
        else:
            # SensorThread'e Firebase durumunu bildir
            if hasattr(self, 'sensor_thread'):
                self.sensor_thread.set_firebase_initialized(False)
    
    def initialize_firebase(self):
        """Firebase'i başlat"""
        if not FIREBASE_AVAILABLE:
            self.firebase_initialized = False
            return False
            
        try:
            # Mevcut Firebase uygulamalarını temizle
            if firebase_admin._apps:
                for app in firebase_admin._apps.copy().values():
                    firebase_admin.delete_app(app)
            
            # Firebase'i başlat
            cred = credentials.Certificate('ika-db-eb609-firebase-adminsdk-fbsvc-96c3b83edc.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://ika-db-eb609-default-rtdb.europe-west1.firebasedatabase.app/'
            })
            self.firebase_initialized = True
            return True
            
        except Exception as e:
            self.firebase_initialized = False
            return False
    
    def send_to_firebase(self, path, data):
        """Firebase'e veri gönder"""
        if not FIREBASE_AVAILABLE:
            return True
            
        if not self.firebase_initialized:
            return True
            
        try:
            # Acil durum verisi sadece boolean gönderir, zaman damgası ekleme
            if path != 'emergency':
                data['timestamp'] = time.time()
            
            ref = db.reference(path)
            ref.set(data)
            return True
        except Exception as e:
            return True  # Hata olsa bile uygulamayı çalışmaya devam ettir
    
    def handle_firebase_data(self, firebase_data):
        """Firebase'den gelen verileri işle"""
        data_type = firebase_data.get('type')
        data = firebase_data.get('data')
        
        
        if data_type == 'sensors' and data:
            # Firebase'den gelen sensör verilerini UI'da göster
            self.update_sensor_data(data)
            
            # SensorThread'e de bildir (eğer Firebase'de veri varsa simülasyonu durdur)
            if hasattr(self, 'sensor_thread'):
                self.sensor_thread.set_firebase_initialized(True)
                
        elif data_type == 'sensors_empty':
            # Firebase'de sensör verisi yok, simülasyon moduna geç
            if hasattr(self, 'sensor_thread'):
                self.sensor_thread.set_firebase_initialized(False)
            
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
        
        elif data_type == 'laser' and data:
            # Lazer komutlarını işle
            command = data.get('command', '')
        
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

        self.send_to_firebase('emergency', {'emergency': bool(is_active)})

    def set_control_mode(self, mode):
        if mode == "manual":
            self.semi_auto_btn.setChecked(False)
            self.auto_btn.setChecked(False)
            self.send_to_firebase('control', {'mode': 'manual'})
        elif mode == "semi":
            self.manual_btn.setChecked(False)
            self.auto_btn.setChecked(False)
            self.send_to_firebase('control', {'mode': 'semi_auto'})
        elif mode == "auto":
            self.manual_btn.setChecked(False)
            self.semi_auto_btn.setChecked(False)
            self.send_to_firebase('control', {'mode': 'auto'})

    def toggle_laser_mode(self):
        # Checkable butona bağla: true ise lazer modu
        self.laser_mode = self.laser_btn.isChecked()
        if self.laser_mode:
            self.direction_group.hide()
            self.laser_direction_group.show()
            self.laser_btn.setText("🔄 NORMAL MODA DÖN")
            # Firebase'e lazer modu aktif bilgisini gönder
            self.send_to_firebase('laser_mode', {'active': True})
        else:
            self.laser_direction_group.hide()
            self.direction_group.show()
            self.laser_btn.setText("LAZER ATIŞ MODU")
            # Firebase'e lazer modu pasif bilgisini gönder
            self.send_to_firebase('laser_mode', {'active': False})

    def direction_pressed(self, direction):
        # İleri tuşu ayrı dalda, sağ/sol aynı dalda
        if direction == 'up':
            self.send_to_firebase('forward', {'command': 'forward'})
        else:
            self.send_to_firebase('steering', {'command': direction})
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

        # Firebase'e vites bilgisini ayrı 'gear' düğümüne gönder
        self.send_to_firebase('gear', {'gear': gear})
        self._flash_title(f"Vites: {gear}")

    def _flash_title(self, text: str):
        # Durumu kısa süre pencerede göster, sonra geri al
        self.setWindowTitle(f"{self._base_title} — {text}")
        QTimer.singleShot(1500, lambda: self.setWindowTitle(self._base_title))

    def laser_direction_pressed(self, direction):
        # Firebase'e lazer yön komutu gönder
        self.send_to_firebase('laser', {'command': direction})

    def laser_fire(self):
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
            return False
            
        try:
            # Test verisi gönder
            test_data = {'test': True, 'timestamp': time.time()}
            ref = db.reference('test_connection')
            ref.set(test_data)
            
            # Test verisini sil
            ref.delete()
            return True
        except Exception as e:
            return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = IKADashboard()
    win.show()
    sys.exit(app.exec())
