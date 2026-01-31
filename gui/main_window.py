import os
import threading
import subprocess
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QPushButton, QFileDialog, QHBoxLayout, 
                             QMessageBox, QProgressBar, QScrollArea, QLineEdit, QStackedWidget, QToolButton)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QIcon

from utils.system_check import SystemChecker
from utils.signals import Comunicador
from gui.widgets import WidgetAppInstalada
from core.managers.deb import DebManager
from core.managers.appimage import AppImageManager
from core.managers.flatpak import FlatpakManager
from core.managers.snap import SnapManager
from utils.helpers import cargar_traducciones

class InstaladorPro(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. CARGA DE IDIOMA (Inglés por defecto si no hay JSON del sistema)
        self.lang = cargar_traducciones()
        
        self.setWindowTitle(self.lang.get("window_title", "SuperInstall v3.0"))
        self.resize(950, 650)
        self.setMinimumSize(850, 550)
        self.setAcceptDrops(True)
        self.instalando = False
        
        # 2. MANAGERS (Ahora les pasamos self.lang)
        self.comunicador = Comunicador()
        self.mgr_deb = DebManager(self.comunicador, self.lang)
        self.mgr_appimage = AppImageManager(self.comunicador, self.lang)
        self.mgr_flatpak = FlatpakManager(self.comunicador, self.lang)
        self.mgr_snap = SnapManager(self.comunicador, self.lang)
        
        # 3. SEÑALES
        self.comunicador.icono_listo.connect(self.actualizar_icono_visual)
        self.comunicador.progreso_actualizado.connect(self.actualizar_progreso)
        self.comunicador.instalacion_completada.connect(self.mostrar_resultado)

        # 4. UI Y ESTADO
        self.setup_ui_base()
        self.cargar_estilos()
        self.ruta_archivo = ""
        self.manager_actual = None

    def setup_ui_base(self):
        """Configura la estructura principal: Sidebar + Contenido"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout_principal = QHBoxLayout(self.central_widget)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        ly_sidebar = QVBoxLayout(self.sidebar)
        ly_sidebar.setContentsMargins(15, 50, 15, 20)
        ly_sidebar.setSpacing(25)

        # Botón Instalar
        self.btn_nav_instalar = QToolButton()
        self.btn_nav_instalar.setText(self.lang.get('btn_install_nav', 'Install'))
        self.btn_nav_instalar.setObjectName("btn_nav")
        self.btn_nav_instalar.setProperty("active", True)
        self.btn_nav_instalar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.btn_nav_instalar.setIcon(QIcon("assets/icons/nav_install.png"))
        self.btn_nav_instalar.setIconSize(QSize(120, 120))
        self.btn_nav_instalar.setFixedSize(180, 190)
        self.btn_nav_instalar.setCursor(Qt.PointingHandCursor)
        self.btn_nav_instalar.clicked.connect(lambda: self.cambiar_vista(0))

        # Botón Gestionar
        self.btn_nav_gestionar = QToolButton()
        self.btn_nav_gestionar.setText(self.lang.get('btn_manage_nav', 'Manage'))
        self.btn_nav_gestionar.setObjectName("btn_nav")
        self.btn_nav_gestionar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.btn_nav_gestionar.setIcon(QIcon("assets/icons/nav_manage.png"))
        self.btn_nav_gestionar.setIconSize(QSize(120, 120)) 
        self.btn_nav_gestionar.setFixedSize(180, 190)
        self.btn_nav_gestionar.setCursor(Qt.PointingHandCursor)
        self.btn_nav_gestionar.clicked.connect(lambda: self.cambiar_vista(1))

        ly_sidebar.addWidget(self.btn_nav_instalar, alignment=Qt.AlignCenter)
        ly_sidebar.addWidget(self.btn_nav_gestionar, alignment=Qt.AlignCenter)
        ly_sidebar.addStretch()

        # --- CONTENIDO (STACKED WIDGET) ---
        self.stack = QStackedWidget()
        self.vista_instalacion = QWidget()
        self.setup_view_instalar()
        self.vista_gestor = QWidget()
        self.setup_view_gestionar()

        self.stack.addWidget(self.vista_instalacion)
        self.stack.addWidget(self.vista_gestor)

        self.layout_principal.addWidget(self.sidebar)
        self.layout_principal.addWidget(self.stack)

    def setup_view_instalar(self):
        """Vista principal de Drag & Drop e instalación"""
        layout = QVBoxLayout(self.vista_instalacion)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(15)

        # Botón Volver
        self.btn_volver = QPushButton("✕")
        self.btn_volver.setObjectName("btn_volver")
        self.btn_volver.setFixedSize(35, 35)
        self.btn_volver.clicked.connect(self.estado_inicial)
        self.btn_volver.setCursor(Qt.PointingHandCursor)
        self.btn_volver.hide()
        
        lt = QHBoxLayout(); lt.addStretch(); lt.addWidget(self.btn_volver)
        layout.addLayout(lt)
        layout.addStretch()

        # Contenedor Icono
        self.contenedor_icono = QWidget()
        self.contenedor_icono.setObjectName("contenedor_icono")
        self.contenedor_icono.setFixedSize(180, 180)
        ly_ico = QVBoxLayout(self.contenedor_icono)
        self.label_icono = QLabel()
        self.label_icono.setObjectName("label_logo_principal")
        self.label_icono.setAlignment(Qt.AlignCenter)
        self.set_main_logo("+")
        ly_ico.addWidget(self.label_icono)
        layout.addWidget(self.contenedor_icono, alignment=Qt.AlignCenter)

        # Etiquetas de Texto
        self.label_nombre = QLabel(self.lang.get("welcome_msg", "Welcome"))
        self.label_nombre.setObjectName("label_nombre")
        self.label_nombre.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_nombre) 

        self.label_version = QLabel(self.lang.get("drag_drop_info", "Drag and drop a file"))
        self.label_version.setObjectName("label_version")
        self.label_version.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_version) 

        # Barra de progreso
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setObjectName("barra_progreso")
        self.barra_progreso.setFixedHeight(6)
        self.barra_progreso.setFixedWidth(300)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.hide()
        layout.addWidget(self.barra_progreso, alignment=Qt.AlignCenter)

        # Botones de Acción
        self.btn_abrir = QPushButton(self.lang.get("btn_select", "Select File"))
        self.btn_abrir.setObjectName("btn_abrir")
        self.btn_abrir.setFixedSize(220, 48)
        self.btn_abrir.clicked.connect(self.seleccionar_archivo)
        layout.addWidget(self.btn_abrir, alignment=Qt.AlignCenter)

        self.btn_instalar = QPushButton(self.lang.get("btn_install", "Install Now"))
        self.btn_instalar.setObjectName("btn_instalar")
        self.btn_instalar.setFixedSize(220, 48)
        self.btn_instalar.clicked.connect(self.iniciar_instalacion)
        self.btn_instalar.hide()
        layout.addWidget(self.btn_instalar, alignment=Qt.AlignCenter)

        layout.addStretch()

    def setup_view_gestionar(self):
        """Vista del gestor de aplicaciones instaladas"""
        layout = QVBoxLayout(self.vista_gestor)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(20)
        
        lbl_t = QLabel(self.lang.get("title_gestor", "Installed Apps"))
        lbl_t.setObjectName("titulo_gestor")
        layout.addWidget(lbl_t)

        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText(self.lang.get("search_placeholder", "Search..."))
        self.txt_busqueda.setObjectName("barra_busqueda")
        self.txt_busqueda.setFixedHeight(45)
        self.txt_busqueda.textChanged.connect(self.filtrar_aplicaciones)
        layout.addWidget(self.txt_busqueda)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("scroll_area")
        self.contenedor_lista = QWidget()
        self.lista_layout = QVBoxLayout(self.contenedor_lista)
        self.lista_layout.setAlignment(Qt.AlignTop)
        self.lista_layout.setSpacing(10)
        self.scroll.setWidget(self.contenedor_lista)
        layout.addWidget(self.scroll)

    def cambiar_vista(self, index):
        """Cambia entre pestañas y refresca la sidebar"""
        self.stack.setCurrentIndex(index)
        self.btn_nav_instalar.setProperty("active", index == 0)
        self.btn_nav_gestionar.setProperty("active", index == 1)
        
        for btn in [self.btn_nav_instalar, self.btn_nav_gestionar]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        if index == 1:
            self.cargar_lista_apps()

    def estado_inicial(self):
        """Reset total a la pantalla de bienvenida"""
        self.ruta_archivo = ""; 
        self.manager_actual = None
        self.instalando = False
        self.btn_abrir.show(); 
        self.btn_instalar.hide(); 
        self.btn_volver.hide()
        self.label_nombre.setText(self.lang.get("welcome_msg", "Welcome"))
        self.label_version.setText(self.lang.get("drag_drop_info", "Drag and drop a file"))
        self.set_main_logo("+")
        self.barra_progreso.hide(); 
        self.barra_progreso.setValue(0)
        self.btn_instalar.setStyleSheet("") 

    def preparar_archivo(self, archivo):
        """Detecta el motor adecuado y verifica soporte del sistema"""
        self.ruta_archivo = archivo
        ext = archivo.lower()
        
        motores = {
            ".deb": (self.mgr_deb, "deb"),
            ".appimage": (self.mgr_appimage, "appimage"),
            ".flatpak": (self.mgr_flatpak, "flatpak"),
            ".flatpakref": (self.mgr_flatpak, "flatpak"),
            ".snap": (self.mgr_snap, "snap")
        }

        # 1. Identificamos el motor
        self.manager_actual = None
        motor_nombre = ""
        for k, v in motores.items():
            if ext.endswith(k):
                self.manager_actual, motor_nombre = v
                break
        
        if not self.manager_actual: return

        # 2. Verificación de Soporte de Binarios (¿Está instalado flatpak/snap?)
        if not SystemChecker.esta_instalado(motor_nombre):
            self.preparar_ui_soporte_faltante(motor_nombre)
            return

        # 3. COMPROBACIÓN DE ARQUITECTURA (Lo movemos aquí arriba)
        arch_pc = SystemChecker.obtener_arquitectura_sistema()
        arch_app = SystemChecker.obtener_arquitectura_archivo(archivo, motor_nombre)

        if not SystemChecker.es_compatible(arch_pc, arch_app):
            # Si no es compatible, avisamos inmediatamente y bloqueamos todo
            msg_error = self.lang.get("arch_error", "Incompatible architecture")
            self.label_nombre.setText(os.path.basename(archivo))
            self.label_version.setText(f"⚠️ {msg_error}: {arch_app}")
            self.set_main_logo("🚫")
            
            self.btn_abrir.hide()
            self.btn_instalar.show()
            self.btn_instalar.setEnabled(False)
            self.btn_instalar.setStyleSheet("background-color: #7f8c8d; color: #bdc3c7;")
            self.btn_volver.show()
            return # Aquí termina todo si la arquitectura falla

        # 4. Flujo Normal (Solo llegamos aquí si la arquitectura es OK)
        ya_existe = self.manager_actual.esta_instalado(archivo)
        nombre, info_texto = self.manager_actual.obtener_datos(archivo)

        self.btn_abrir.hide()
        self.btn_instalar.show()
        self.btn_instalar.setEnabled(True)
        self.btn_volver.show()
        self.label_nombre.setText(nombre)
        self.set_main_logo("📦")
        
        # UI según si ya existe o no
        if ya_existe:
            self.btn_instalar.setText(self.lang.get("btn_reinstall", "Reinstall"))
            self.btn_instalar.setStyleSheet("background-color: #f39c12; color: white;")
            msg_suffix = self.lang.get("already_installed", "(Already installed)")
            self.label_version.setText(f"{info_texto} {msg_suffix}")
        else:
            self.btn_instalar.setText(self.lang.get("btn_install", "Install Now"))
            self.btn_instalar.setStyleSheet("") 
            self.label_version.setText(info_texto)

        # Buscar icono en segundo plano (Solo si la arquitectura era correcta)
        threading.Thread(target=self.manager_actual.buscar_icono, args=(archivo,), daemon=True).start()
    
    def preparar_ui_soporte_faltante(self, motor):
        """Ofrece instalar el motor (Flatpak/Snap) si no existe"""
        txt_not_detected = self.lang.get("support_not_detected", "Support not detected")
        txt_needs = self.lang.get("system_needs", "Your system needs")
        
        self.label_nombre.setText(f"{motor.capitalize()} {txt_not_detected}")
        self.label_version.setText(f"{txt_needs} {motor}.")
        self.set_main_logo("⚠️")
        
        self.btn_abrir.hide()
        self.btn_instalar.show()
        self.btn_instalar.setText(f"{self.lang.get('btn_activate', 'Activate')} {motor.capitalize()}")
        self.btn_instalar.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        
        try: self.btn_instalar.clicked.disconnect()
        except: pass
        self.btn_instalar.clicked.connect(lambda: self.activar_soporte_sistema(motor))
        self.btn_volver.show()

    def activar_soporte_sistema(self, motor):
        """Lógica para instalar motores faltantes vía pkexec"""
        comando = ""
        if motor == "flatpak":
            comando = "pkexec apt-get update && pkexec apt-get install -y flatpak"
        elif motor == "snap":
            comando = "pkexec apt-get update && pkexec apt-get install -y snapd"
            
        if comando:
            self.btn_instalar.setEnabled(False)
            self.label_version.setText(self.lang.get("msg_activating", "Activating support... please wait."))
            
            def tarea():
                res = subprocess.run(comando, shell=True)
                # Al terminar, refrescamos la UI
                QTimer.singleShot(0, lambda: self.preparar_archivo(self.ruta_archivo))

            threading.Thread(target=tarea, daemon=True).start()

    def iniciar_instalacion(self):
        """Lanza el proceso de instalación o cancela si ya está en curso"""
        if not self.instalando:
            self.instalando = True
            self.barra_progreso.show()
            self.barra_progreso.setValue(0)
            self.btn_instalar.setText(self.lang.get("btn_cancel", "Cancel Installation"))
            self.btn_instalar.setStyleSheet("background-color: #e74c3c; color: white;") 
            
            threading.Thread(target=self.manager_actual.instalar, args=(self.ruta_archivo,), daemon=True).start()
        else:
            self.manager_actual.cancelar_operacion()
            self.estado_inicial()

    def mostrar_resultado(self, exito, mensaje_key):
        """Muestra el popup final y resetea la UI"""
        self.barra_progreso.setValue(100 if exito else 0)
        texto_mensaje = self.lang.get(mensaje_key, mensaje_key)
        QMessageBox.information(self, "SuperInstall", texto_mensaje)
        self.instalando = False
        self.estado_inicial()

    # --- UTILIDADES DE UI ---

    def set_main_logo(self, fallback_emoji):
        ruta_logo = os.path.join("assets", "icons", "logo_bellota.png")
        if os.path.exists(ruta_logo):
            pix = QPixmap(ruta_logo)
            self.label_icono.setPixmap(pix.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.label_icono.setText("")
        else:
            self.label_icono.setPixmap(QPixmap())
            self.label_icono.setText(fallback_emoji)
            self.label_icono.setStyleSheet("font-size: 90px;")

    def actualizar_icono_visual(self, ruta):
        if ruta and os.path.exists(ruta):
            self.label_icono.setText("")
            self.label_icono.setPixmap(QPixmap(ruta).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def actualizar_progreso(self, v):
        self.barra_progreso.setValue(v)

    def cargar_estilos(self):
        ruta = os.path.join("assets", "styles", "style.qss")
        if os.path.exists(ruta):
            with open(ruta, "r") as f:
                self.setStyleSheet(f.read())

    # --- GESTOR DE APPS INSTALADAS ---

    def cargar_lista_apps(self):
        # Limpiar lista actual
        while self.lista_layout.count():
            item = self.lista_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

        # Cargar de sistema y Managers
        self.cargar_apps_desktop()
        for mgr, tipo in [(self.mgr_flatpak, "flatpak"), (self.mgr_snap, "snap")]:
            try:
                for app in mgr.listar_instalados():
                    self.lista_layout.addWidget(WidgetAppInstalada(app['nombre'], app['id'], app['icono'], self.confirmar_borrado, self.lang, tipo))
            except: pass

    def cargar_apps_desktop(self):
        rutas = [os.path.expanduser("~/.local/share/applications/"), "/usr/share/applications/"]
        for r in rutas:
            if os.path.exists(r):
                for f in sorted(os.listdir(r)):
                    if f.endswith(".desktop"):
                        self.procesar_archivo_desktop(os.path.join(r, f))

    def procesar_archivo_desktop(self, path):
        nombre, icono = "App", "system-run"
        try:
            with open(path, 'r', errors='ignore') as file:
                en_seccion = False
                for l in file:
                    l = l.strip()
                    if l == "[Desktop Entry]": en_seccion = True
                    elif en_seccion and l.startswith("["): break
                    if en_seccion:
                        if l.startswith("Name="): nombre = l.split('=', 1)[1].strip()
                        elif l.startswith("Icon="): icono = self.resolver_ruta_icono(l.split('=', 1)[1].strip())
        except: pass

        if nombre != "App":
            tipo = "appimage" if "/home/" in path else "system"
            self.lista_layout.addWidget(WidgetAppInstalada(nombre, path, icono, self.confirmar_borrado, self.lang, tipo))

    def filtrar_aplicaciones(self, texto):
        texto = texto.lower()
        for i in range(self.lista_layout.count()):
            widget = self.lista_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(texto in widget.lbl_nombre.text().lower())

    def confirmar_borrado(self, nombre, ruta_o_id, tipo_app):
        # Traducción del diálogo de borrado
        msg = f"{self.lang.get('msg_confirm_delete', 'Delete')} {nombre}?"
        if QMessageBox.question(self, self.lang.get("title_delete", "Delete"), msg) == QMessageBox.Yes:
            exito = False
            if tipo_app == "flatpak": exito = self.mgr_flatpak.desinstalar(ruta_o_id)
            elif tipo_app == "snap": exito = self.mgr_snap.desinstalar(ruta_o_id)
            elif tipo_app == "appimage": exito = self.mgr_appimage.desinstalar(ruta_o_id)
            else: exito = self.mgr_deb.desinstalar(ruta_o_id)
            if exito: QTimer.singleShot(500, self.cargar_lista_apps)

    def resolver_ruta_icono(self, nombre_icono):
        if os.path.isabs(nombre_icono) and os.path.exists(nombre_icono): return nombre_icono
        rutas_sistema = ["/usr/share/pixmaps", "/usr/share/icons/hicolor/scalable/apps", "/usr/share/icons/hicolor/48x48/apps", "/usr/share/icons/hicolor/128x128/apps", os.path.expanduser("~/.local/share/icons")]
        for ruta in rutas_sistema:
            for ext in [".png", ".svg", ".xpm"]:
                posible = os.path.join(ruta, f"{nombre_icono}{ext}")
                if os.path.exists(posible): return posible
        return nombre_icono

    # --- EVENTOS DRAG & DROP ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.contenedor_icono.setStyleSheet("background-color: rgba(72, 126, 176, 0.15); border: 3px solid #487eb0; border-radius: 20px;")

    def dragLeaveEvent(self, event):
        self.contenedor_icono.setStyleSheet("")

    def dropEvent(self, event):
        self.contenedor_icono.setStyleSheet("")
        self.cambiar_vista(0)
        archivo = event.mimeData().urls()[0].toLocalFile()
        self.preparar_archivo(archivo)

    def seleccionar_archivo(self):
        filtro = "Apps (*.deb *.AppImage *.flatpak *.flatpakref *.snap)"
        archivo, _ = QFileDialog.getOpenFileName(self, self.lang.get("btn_select", "Open"), "", filtro)
        if archivo: self.preparar_archivo(archivo)