import os
import threading
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QPushButton, QFileDialog, QHBoxLayout, 
                             QMessageBox, QProgressBar, QScrollArea, QLineEdit, QStackedWidget, QToolButton)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QIcon

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
        
        self.lang = cargar_traducciones()
        # Usamos el texto del JSON para el título
        self.setWindowTitle(self.lang.get("window_title", "SuperInstall v3.0"))
        self.resize(950, 650)
        self.setMinimumSize(850, 550)
        self.setAcceptDrops(True)
        
        # Managers
        self.comunicador = Comunicador()
        self.mgr_deb = DebManager(self.comunicador)
        self.mgr_appimage = AppImageManager(self.comunicador)
        self.mgr_flatpak = FlatpakManager(self.comunicador)
        self.mgr_snap = SnapManager(self.comunicador)
        
        # Señales
        self.comunicador.icono_listo.connect(self.actualizar_icono_visual)
        self.comunicador.progreso_actualizado.connect(self.actualizar_progreso)
        self.comunicador.instalacion_completada.connect(self.mostrar_resultado)

        # UI
        self.setup_ui_base()
        self.cargar_estilos()
        
        self.ruta_archivo = ""
        self.manager_actual = None

    def xsetup_ui_base(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout_principal = QHBoxLayout(self.central_widget)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # --- SIDEBAR (Barra Lateral) ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        ly_sidebar = QVBoxLayout(self.sidebar)
        ly_sidebar.setContentsMargins(15, 40, 15, 20)
        ly_sidebar.setSpacing(10)

        self.btn_nav_instalar = QPushButton(f"  {self.lang.get('btn_install_nav', 'Instalar')}")
        self.btn_nav_instalar.setObjectName("btn_nav")
        self.btn_nav_instalar.setProperty("active", True)
        
        # --- AÑADIR ICONO ---
        self.btn_nav_instalar.setIcon(QIcon("assets/icons/nav_install.png"))
        self.btn_nav_instalar.setIconSize(QSize(20, 20)) # Tamaño ideal para sidebar
        
        self.btn_nav_instalar.clicked.connect(lambda: self.cambiar_vista(0))

        # 2. Botón Gestionar
        self.btn_nav_gestionar = QPushButton(f"  {self.lang.get('btn_manage_nav', 'Gestionar')}")
        self.btn_nav_gestionar.setObjectName("btn_nav")
        
        # --- AÑADIR ICONO ---
        self.btn_nav_gestionar.setIcon(QIcon("assets/icons/nav_manage.png"))
        self.btn_nav_gestionar.setIconSize(QSize(20, 20))
        
        self.btn_nav_gestionar.clicked.connect(lambda: self.cambiar_vista(1))

        # Botones de navegación usando las llaves CORRECTAS del JSON
        self.btn_nav_instalar = QPushButton(self.lang.get("btn_install_nav", "Instalar"))
        self.btn_nav_instalar.setObjectName("btn_nav")
        self.btn_nav_instalar.setProperty("active", True)
        self.btn_nav_instalar.clicked.connect(lambda: self.cambiar_vista(0))

        self.btn_nav_gestionar = QPushButton(self.lang.get("btn_manage_nav", "Gestionar"))
        self.btn_nav_gestionar.setObjectName("btn_nav")
        self.btn_nav_gestionar.clicked.connect(lambda: self.cambiar_vista(1))

        ly_sidebar.addWidget(self.btn_nav_instalar)
        ly_sidebar.addWidget(self.btn_nav_gestionar)
        ly_sidebar.addStretch()

        # --- CONTENIDO ---
        self.stack = QStackedWidget()
        self.vista_instalacion = QWidget()
        self.setup_view_instalar()
        self.vista_gestor = QWidget()
        self.setup_view_gestionar()

        self.stack.addWidget(self.vista_instalacion)
        self.stack.addWidget(self.vista_gestor)

        self.layout_principal.addWidget(self.sidebar)
        self.layout_principal.addWidget(self.stack)

    def setup_ui_base(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout_principal = QHBoxLayout(self.central_widget)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # --- SIDEBAR (Panel Lateral Robusto) ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220) # Ensanchamos la barra lateral
        ly_sidebar = QVBoxLayout(self.sidebar)
        ly_sidebar.setContentsMargins(15, 50, 15, 20) # Más aire arriba
        ly_sidebar.setSpacing(25) # Más espacio entre los dos botones

        # 1. BOTÓN INSTALAR
        self.btn_nav_instalar = QToolButton()
        self.btn_nav_instalar.setText(self.lang.get('btn_install_nav', 'Instalar'))
        self.btn_nav_instalar.setObjectName("btn_nav")
        self.btn_nav_instalar.setProperty("active", True)
        self.btn_nav_instalar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.btn_nav_instalar.setIcon(QIcon("assets/icons/nav_install.png"))
        
        # DIMENSIONES IMPACTANTES
        self.btn_nav_instalar.setIconSize(QSize(120, 120)) # Icono grande
        self.btn_nav_instalar.setFixedSize(180, 190)     # Baldosa grande
        
        self.btn_nav_instalar.setCursor(Qt.PointingHandCursor)
        self.btn_nav_instalar.clicked.connect(lambda: self.cambiar_vista(0))

        # 2. BOTÓN GESTIONAR
        self.btn_nav_gestionar = QToolButton()
        self.btn_nav_gestionar.setText(self.lang.get('btn_manage_nav', 'Gestionar'))
        self.btn_nav_gestionar.setObjectName("btn_nav")
        self.btn_nav_gestionar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.btn_nav_gestionar.setIcon(QIcon("assets/icons/nav_manage.png"))
        
        self.btn_nav_gestionar.setIconSize(QSize(120, 120)) 
        self.btn_nav_gestionar.setFixedSize(180, 190)
        
        self.btn_nav_gestionar.setCursor(Qt.PointingHandCursor)
        self.btn_nav_gestionar.clicked.connect(lambda: self.cambiar_vista(1))

        # Añadimos al layout (centrados en la sidebar)
        ly_sidebar.addWidget(self.btn_nav_instalar, alignment=Qt.AlignCenter)
        ly_sidebar.addWidget(self.btn_nav_gestionar, alignment=Qt.AlignCenter)
        ly_sidebar.addStretch()

        # --- CONTENIDO ---
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
        layout = QVBoxLayout(self.vista_instalacion)
        # 1. Quitamos layout.setAlignment(Qt.AlignCenter) de aquí.
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(15)

        # Botón Volver (arriba a la derecha)
        self.btn_volver = QPushButton("✕")
        self.btn_volver.setObjectName("btn_volver")
        self.btn_volver.setFixedSize(35, 35)
        self.btn_volver.hide()
        lt = QHBoxLayout(); lt.addStretch(); lt.addWidget(self.btn_volver)
        layout.addLayout(lt)

        # --- ESPACIADOR SUPERIOR ---
        layout.addStretch()

        # CONTENEDOR DEL ICONO
        self.contenedor_icono = QWidget()
        self.contenedor_icono.setObjectName("contenedor_icono")
        self.contenedor_icono.setFixedSize(180, 180)
        ly_ico = QVBoxLayout(self.contenedor_icono)
        ly_ico.setContentsMargins(0, 0, 0, 0)
        self.label_icono = QLabel()
        self.label_icono.setObjectName("label_logo_principal")
        self.label_icono.setAlignment(Qt.AlignCenter)
        self.set_main_logo("🚀")
        ly_ico.addWidget(self.label_icono)
        layout.addWidget(self.contenedor_icono, alignment=Qt.AlignCenter)

        # NOMBRE DE LA APP
        self.label_nombre = QLabel(self.lang.get("welcome_msg", "Bienvenido"))
        self.label_nombre.setObjectName("label_nombre")
        self.label_nombre.setAlignment(Qt.AlignCenter) # Centra el texto dentro
        self.label_nombre.setWordWrap(True)
        # Añadimos sin el segundo parámetro para que ocupe todo el ancho
        layout.addWidget(self.label_nombre) 

        # DESCRIPCIÓN (La que se veía pequeña)
        self.label_version = QLabel(self.lang.get("drag_drop_info", "Arrastra un archivo"))
        self.label_version.setObjectName("label_version")
        self.label_version.setAlignment(Qt.AlignCenter) # Centra el texto dentro
        self.label_version.setWordWrap(True)
        # Al no poner alignment=Qt.AlignCenter aquí, la etiqueta es tan ancha como la ventana
        layout.addWidget(self.label_version) 

        # BARRA DE PROGRESO
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setObjectName("barra_progreso")
        self.barra_progreso.setFixedHeight(6)
        self.barra_progreso.setFixedWidth(300)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.hide()
        layout.addWidget(self.barra_progreso, alignment=Qt.AlignCenter)

        # BOTONES
        self.btn_abrir = QPushButton(self.lang.get("btn_select", "Seleccionar"))
        self.btn_abrir.setObjectName("btn_abrir")
        self.btn_abrir.setFixedSize(220, 48)
        layout.addWidget(self.btn_abrir, alignment=Qt.AlignCenter)

        self.btn_instalar = QPushButton(self.lang.get("btn_install", "Instalar"))
        self.btn_instalar.setObjectName("btn_instalar")
        self.btn_instalar.setFixedSize(220, 48)
        self.btn_instalar.hide()
        layout.addWidget(self.btn_instalar, alignment=Qt.AlignCenter)

        # --- ESPACIADOR INFERIOR ---
        layout.addStretch()

    def setup_view_gestionar(self):
        layout = QVBoxLayout(self.vista_gestor)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(20)
        
        # Título TRADUCIDO
        lbl_t = QLabel(self.lang.get("title_gestor", "Apps Instaladas"))
        lbl_t.setObjectName("titulo_gestor")
        layout.addWidget(lbl_t)

        # Buscador TRADUCIDO
        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText(self.lang.get("search_placeholder", "Buscar..."))
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

    # --- LÓGICA DE ICONOS Y NAVEGACIÓN ---

    def set_main_logo(self, fallback_emoji):
        ruta_logo = os.path.join("assets", "icons", "logo_bellota.png")
        if os.path.exists(ruta_logo):
            pix = QPixmap(ruta_logo)
            # Hacemos el logo un poco más pequeño dentro del contenedor
            self.label_icono.setPixmap(pix.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.label_icono.setText("")
        else:
            self.label_icono.setPixmap(QPixmap())
            self.label_icono.setText(fallback_emoji)
            self.label_icono.setStyleSheet("font-size: 90px;")

    def cambiar_vista(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_nav_instalar.setProperty("active", index == 0)
        self.btn_nav_gestionar.setProperty("active", index == 1)
        
        # Refresco de estilos
        self.btn_nav_instalar.style().unpolish(self.btn_nav_instalar)
        self.btn_nav_instalar.style().polish(self.btn_nav_instalar)
        self.btn_nav_gestionar.style().unpolish(self.btn_nav_gestionar)
        self.btn_nav_gestionar.style().polish(self.btn_nav_gestionar)
        
        if index == 1:
            self.cargar_lista_apps()

    def estado_inicial(self):
        """Reset total al estado de bienvenida."""
        self.ruta_archivo = ""; self.manager_actual = None
        self.btn_abrir.show(); self.btn_instalar.hide(); self.btn_volver.hide()
        # Textos TRADUCIDOS al resetear
        self.label_nombre.setText(self.lang.get("welcome_msg", "Bienvenido"))
        self.label_version.setText(self.lang.get("drag_drop_info", "Arrastra un archivo"))
        self.set_main_logo("🚀")
        self.barra_progreso.hide(); self.barra_progreso.setValue(0)

    
    # --- LÓGICA ORIGINAL ---

    def cargar_lista_apps(self):
        while self.lista_layout.count():
            item = self.lista_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        self.cargar_apps_desktop()
        try:
            for app in self.mgr_flatpak.listar_instalados():
                self.lista_layout.addWidget(WidgetAppInstalada(app['nombre'], app['id'], app['icono'], self.confirmar_borrado, self.lang, "flatpak"))
        except: pass
        try:
            for app in self.mgr_snap.listar_instalados():
                self.lista_layout.addWidget(WidgetAppInstalada(app['nombre'], app['id'], app['icono'], self.confirmar_borrado, self.lang, "snap"))
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
                        elif l.startswith("Icon="): icono = l.split('=', 1)[1].strip()
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
        if QMessageBox.question(self, "Delete", f"Delete {nombre}?") == QMessageBox.Yes:
            exito = False
            if tipo_app == "flatpak": exito = self.mgr_flatpak.desinstalar(ruta_o_id)
            elif tipo_app == "snap": exito = self.mgr_snap.desinstalar(ruta_o_id)
            elif tipo_app == "appimage": exito = self.mgr_appimage.desinstalar(ruta_o_id)
            else: exito = self.mgr_deb.desinstalar(ruta_o_id)
            if exito: QTimer.singleShot(500, self.cargar_lista_apps)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            # Efecto hover cuando arrastras archivo
            self.contenedor_icono.setProperty("drag_active", True)
            self.contenedor_icono.setStyleSheet("""
                #contenedor_icono {
                    background-color: rgba(72, 126, 176, 0.15);
                    border: 3px solid #487eb0;
                    border-radius: 20px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.contenedor_icono.setStyleSheet("")

    def dropEvent(self, event):
        self.contenedor_icono.setStyleSheet("")
        self.cambiar_vista(0)
        archivo = event.mimeData().urls()[0].toLocalFile()
        self.preparar_archivo(archivo)

    def seleccionar_archivo(self):
        # Filtro ampliado para incluir .flatpakref
        filtro = "Apps (*.deb *.AppImage *.flatpak *.flatpakref *.snap)"
        archivo, _ = QFileDialog.getOpenFileName(self, "Open", "", filtro)
        if archivo: 
            self.preparar_archivo(archivo)

    def preparar_archivo(self, archivo):
        self.ruta_archivo = archivo
        ext = archivo.lower() # Pasamos a minúsculas para evitar errores
        
        if ext.endswith(".deb"): 
            self.manager_actual = self.mgr_deb
        elif ext.endswith(".appimage"): 
            self.manager_actual = self.mgr_appimage
        # Aceptamos AMBOS tipos de Flatpak
        elif ext.endswith(".flatpak") or ext.endswith(".flatpakref"): 
            self.manager_actual = self.mgr_flatpak
        elif ext.endswith(".snap"): 
            self.manager_actual = self.mgr_snap
        else: 
            return # Si no es ninguno, salimos

        # Obtener datos (El manager de Flatpak ahora recibirá el archivo correctamente)
        nombre, info_key = self.manager_actual.obtener_datos(archivo)

        self.btn_abrir.hide()
        self.btn_instalar.show()
        self.btn_instalar.setEnabled(True)
        self.btn_volver.show()
        
        self.label_nombre.setText(nombre)
        self.label_version.setText(self.lang.get(info_key, info_key))
        
        # Ponemos la Bellota o el Cohete plano mientras carga
        self.set_main_logo("🚀")
        
        # Lanzamos el hilo para buscar el icono real si está disponible
        threading.Thread(target=self.manager_actual.buscar_icono, args=(archivo,), daemon=True).start()

    # --- NAVEGACIÓN CORREGIDA ---

    def cambiar_vista(self, index):
        self.stack.setCurrentIndex(index)
        # Actualizar visualmente los botones de la sidebar
        self.btn_nav_instalar.setProperty("active", index == 0)
        self.btn_nav_gestionar.setProperty("active", index == 1)
        
        # Forzar recarga de estilos
        for btn in [self.btn_nav_instalar, self.btn_nav_gestionar]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        if index == 1:
            self.cargar_lista_apps()


    def iniciar_instalacion(self):
        if not self.manager_actual: return
        self.btn_instalar.setEnabled(False)
        self.barra_progreso.show()
        threading.Thread(target=self.manager_actual.instalar, args=(self.ruta_archivo,), daemon=True).start()

    def actualizar_icono_visual(self, ruta):
        if ruta and os.path.exists(ruta):
            self.label_icono.setText("")
            self.label_icono.setPixmap(QPixmap(ruta).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def actualizar_progreso(self, v):
        self.barra_progreso.setValue(v)

    def mostrar_resultado(self, exito, mensaje_key):
        self.barra_progreso.setValue(100)
        QMessageBox.information(self, "SuperInstall", mensaje_key)
        self.estado_inicial()

    def cargar_estilos(self):
        ruta = os.path.join("assets", "styles", "style.qss")
        if os.path.exists(ruta):
            with open(ruta, "r") as f:
                self.setStyleSheet(f.read())