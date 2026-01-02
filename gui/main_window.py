import os
import threading
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QPushButton, QFileDialog, QHBoxLayout, 
                             QMessageBox, QProgressBar, QScrollArea)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from utils.signals import Comunicador
from gui.widgets import WidgetAppInstalada
from core.managers.deb import DebManager
from core.managers.appimage import AppImageManager

class InstaladorPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperInstall v3.0 - Modular")
        self.setFixedSize(450, 620)
        self.setAcceptDrops(True)
        
        # 1. Cargamos estilos externos
        self.cargar_estilos()

        # 2. Inicializamos mensajería y managers
        self.comunicador = Comunicador()
        self.mgr_deb = DebManager(self.comunicador)
        self.mgr_appimage = AppImageManager(self.comunicador)
        
        # Conexión de señales
        self.comunicador.icono_listo.connect(self.actualizar_icono_visual)
        self.comunicador.progreso_actualizado.connect(self.actualizar_progreso)
        self.comunicador.instalacion_completada.connect(self.mostrar_resultado)

        self.setup_ui()
        
        self.ruta_archivo = ""
        self.manager_actual = None

    def setup_ui(self):
        """Configuración de la interfaz de usuario"""
        self.stack_widget = QWidget()
        self.setCentralWidget(self.stack_widget)
        self.layout_stack = QVBoxLayout(self.stack_widget)
        self.layout_stack.setContentsMargins(0,0,0,0)

        # --- VISTA 1: EL INSTALADOR ---
        self.vista_instalacion = QWidget()
        self.layout_principal = QVBoxLayout(self.vista_instalacion)
        self.layout_principal.setAlignment(Qt.AlignCenter)
        self.layout_principal.setContentsMargins(30, 20, 30, 20)

        self.btn_volver = QPushButton("✕")
        self.btn_volver.setObjectName("btn_volver")
        self.btn_volver.setFixedSize(32, 32)
        self.btn_volver.clicked.connect(self.estado_inicial)
        self.btn_volver.hide()
        
        lt = QHBoxLayout(); lt.addStretch(); lt.addWidget(self.btn_volver)
        self.layout_principal.addLayout(lt)

        self.contenedor_icono = QWidget()
        self.contenedor_icono.setObjectName("contenedor_icono")
        self.contenedor_icono.setFixedSize(180, 180)
        ly_ico = QVBoxLayout(self.contenedor_icono)
        self.label_icono = QLabel("📦")
        self.label_icono.setObjectName("label_icono")
        self.label_icono.setAlignment(Qt.AlignCenter)
        ly_ico.addWidget(self.label_icono)
        self.layout_principal.addWidget(self.contenedor_icono, alignment=Qt.AlignCenter)

        self.label_nombre = QLabel("Bienvenido")
        self.label_nombre.setObjectName("label_nombre")
        self.layout_principal.addWidget(self.label_nombre, alignment=Qt.AlignCenter)

        self.label_version = QLabel("Arrastra un .deb o .AppImage")
        self.label_version.setObjectName("label_version")
        self.label_version.setAlignment(Qt.AlignCenter)
        self.layout_principal.addWidget(self.label_version, alignment=Qt.AlignCenter)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setObjectName("barra_progreso")
        self.barra_progreso.setFixedHeight(8)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.hide()
        self.layout_principal.addWidget(self.barra_progreso)

        self.btn_abrir = QPushButton("Seleccionar archivo")
        self.btn_abrir.setObjectName("btn_abrir")
        self.btn_abrir.setFixedHeight(44)
        self.btn_abrir.clicked.connect(self.seleccionar_archivo)
        self.layout_principal.addWidget(self.btn_abrir, alignment=Qt.AlignCenter)

        self.btn_instalar = QPushButton("Instalar Ahora")
        self.btn_instalar.setObjectName("btn_instalar")
        self.btn_instalar.setFixedHeight(44)
        self.btn_instalar.hide()
        self.btn_instalar.clicked.connect(self.iniciar_instalacion)
        self.layout_principal.addWidget(self.btn_instalar, alignment=Qt.AlignCenter)

        self.btn_gestionar = QPushButton("Gestionar aplicaciones instaladas")
        self.btn_gestionar.setObjectName("btn_gestionar")
        self.btn_gestionar.clicked.connect(self.mostrar_gestor)
        self.layout_principal.addWidget(self.btn_gestionar, alignment=Qt.AlignCenter)

        # --- VISTA 2: EL GESTOR ---
        self.vista_gestor = QWidget()
        self.vista_gestor.hide()
        ly_g = QVBoxLayout(self.vista_gestor)
        
        lbl_t = QLabel("Aplicaciones Instaladas")
        lbl_t.setObjectName("titulo_gestor")
        ly_g.addWidget(lbl_t)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("scroll_area")
        self.scroll.setWidgetResizable(True)
        self.contenedor_lista = QWidget()
        self.contenedor_lista.setObjectName("contenedor_lista")
        self.lista_layout = QVBoxLayout(self.contenedor_lista)
        self.lista_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.contenedor_lista)
        ly_g.addWidget(self.scroll)

        btn_v_gestor = QPushButton("Volver")
        btn_v_gestor.setObjectName("btn_volver_gestor")
        btn_v_gestor.clicked.connect(self.estado_inicial)
        ly_g.addWidget(btn_v_gestor)

        self.layout_stack.addWidget(self.vista_instalacion)
        self.layout_stack.addWidget(self.vista_gestor)

    # --- LÓGICA DE EVENTOS Y ARCHIVOS ---

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()

    def dropEvent(self, event):
        archivo = event.mimeData().urls()[0].toLocalFile()
        self.preparar_archivo(archivo)

    def seleccionar_archivo(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "Apps (*.deb *.AppImage)")
        if archivo: self.preparar_archivo(archivo)

    def preparar_archivo(self, archivo):
        self.ruta_archivo = archivo
        if archivo.endswith(".deb"): self.manager_actual = self.mgr_deb
        elif archivo.endswith(".AppImage"): self.manager_actual = self.mgr_appimage
        else: return

        self.btn_abrir.hide()
        self.btn_instalar.show()
        self.btn_instalar.setEnabled(True)
        self.btn_volver.show()
        self.btn_gestionar.hide()
        
        nombre, info = self.manager_actual.obtener_datos(archivo)
        self.label_nombre.setText(nombre)
        self.label_version.setText(info)
        self.label_icono.setText("📦")
        
        threading.Thread(target=self.manager_actual.buscar_icono, args=(archivo,), daemon=True).start()

    def iniciar_instalacion(self):
        if not self.manager_actual: return
        if self.manager_actual.esta_instalado(self.ruta_archivo):
            pregunta = QMessageBox.question(self, "Ya instalado", "¿Reinstalar aplicación?", QMessageBox.Yes | QMessageBox.No)
            if pregunta == QMessageBox.No: return

        self.btn_instalar.setEnabled(False)
        self.barra_progreso.show()
        self.simular_progreso()
        threading.Thread(target=self.manager_actual.instalar, args=(self.ruta_archivo,), daemon=True).start()

    def mostrar_gestor(self):
        self.vista_instalacion.hide(); self.vista_gestor.show(); self.cargar_lista_apps()

    def cargar_lista_apps(self):
        for i in reversed(range(self.lista_layout.count())): 
            self.lista_layout.itemAt(i).widget().setParent(None)
        
        rutas = [os.path.expanduser("~/.local/share/applications/"), "/usr/share/applications/"]
        for r in rutas:
            if not os.path.exists(r): continue
            for f in sorted(os.listdir(r)):
                if f.endswith(".desktop"):
                    if any(x in f.lower() for x in ["gnome", "nautilus", "mime"]): continue
                    self.procesar_archivo_desktop(os.path.join(r, f))

    def procesar_archivo_desktop(self, path):
        nombre, icono = "App", "system-run"
        try:
            with open(path, 'r') as file:
                for l in file:
                    if l.startswith("Name="): nombre = l.split('=')[1].strip()
                    if l.startswith("Icon="): icono = l.split('=')[1].strip()
        except: pass
        self.lista_layout.addWidget(WidgetAppInstalada(nombre, path, icono, self.confirmar_borrado))

    def confirmar_borrado(self, nombre, ruta):
        if QMessageBox.question(self, "Eliminar", f"¿Desinstalar {nombre}?") == QMessageBox.Yes:
            manager = self.mgr_appimage if "/home/" in ruta else self.mgr_deb
            if manager.desinstalar(ruta):
                QTimer.singleShot(1000, self.cargar_lista_apps)

    def estado_inicial(self):
        self.ruta_archivo = ""; self.manager_actual = None
        self.vista_gestor.hide(); self.vista_instalacion.show()
        self.btn_abrir.show(); self.btn_instalar.hide(); self.btn_volver.hide(); self.btn_gestionar.show()
        self.label_nombre.setText("Bienvenido"); self.label_icono.setPixmap(QPixmap()); self.label_icono.setText("📦")
        self.barra_progreso.hide(); self.barra_progreso.setValue(0)

    # --- MÉTODOS DE ACTUALIZACIÓN VISUAL ---

    def cargar_estilos(self):
        ruta = os.path.join("assets", "styles", "style.qss")
        if os.path.exists(ruta):
            with open(ruta, "r") as f: self.setStyleSheet(f.read())

    def simular_progreso(self):
        def act():
            v = self.barra_progreso.value()
            if v < 90: self.barra_progreso.setValue(v + 5); QTimer.singleShot(200, act)
        act()

    def actualizar_icono_visual(self, ruta):
        pix = QPixmap(ruta)
        if not pix.isNull():
            self.label_icono.setText("")
            self.label_icono.setPixmap(pix.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def actualizar_progreso(self, v): self.barra_progreso.setValue(v)

    def mostrar_resultado(self, exito, mensaje):
        self.barra_progreso.setValue(100)
        if exito:
            QMessageBox.information(self, "SuperInstall", mensaje)
            self.estado_inicial()
        else:
            QMessageBox.critical(self, "Error", mensaje)
            self.btn_instalar.setEnabled(True)