import os
import threading
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QPushButton, QFileDialog, QHBoxLayout, 
                             QMessageBox, QProgressBar, QScrollArea, QLineEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from utils.signals import Comunicador
from gui.widgets import WidgetAppInstalada
from core.managers.deb import DebManager
from core.managers.appimage import AppImageManager
from core.managers.flatpak import FlatpakManager
from utils.helpers import cargar_traducciones

class InstaladorPro(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.lang = cargar_traducciones()
        self.setWindowTitle(self.lang.get("window_title", "SuperInstall v3.0"))
        self.setFixedSize(450, 620)
        self.setAcceptDrops(True)
        
        self.cargar_estilos()
        self.comunicador = Comunicador()
        self.mgr_deb = DebManager(self.comunicador)
        self.mgr_appimage = AppImageManager(self.comunicador)
        self.mgr_flatpak = FlatpakManager(self.comunicador)
        
        # Conexión de señales
        self.comunicador.icono_listo.connect(self.actualizar_icono_visual)
        self.comunicador.progreso_actualizado.connect(self.actualizar_progreso)
        self.comunicador.instalacion_completada.connect(self.mostrar_resultado)

        self.setup_ui()
        
        self.ruta_archivo = ""
        self.manager_actual = None

    def setup_ui(self):
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

        self.label_nombre = QLabel(self.lang.get("welcome_msg", "Welcome"))
        self.label_nombre.setObjectName("label_nombre")
        self.layout_principal.addWidget(self.label_nombre, alignment=Qt.AlignCenter)

        self.label_version = QLabel(self.lang.get("drag_drop_info", "Drag a .deb or .AppImage"))
        self.label_version.setObjectName("label_version")
        self.label_version.setAlignment(Qt.AlignCenter)
        self.layout_principal.addWidget(self.label_version, alignment=Qt.AlignCenter)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setObjectName("barra_progreso")
        self.barra_progreso.setFixedHeight(8)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.hide()
        self.layout_principal.addWidget(self.barra_progreso)

        self.btn_abrir = QPushButton(self.lang.get("btn_select", "Select file"))
        self.btn_abrir.setObjectName("btn_abrir")
        self.btn_abrir.setFixedHeight(44)
        self.btn_abrir.clicked.connect(self.seleccionar_archivo)
        self.layout_principal.addWidget(self.btn_abrir, alignment=Qt.AlignCenter)

        self.btn_instalar = QPushButton(self.lang.get("btn_install", "Install Now"))
        self.btn_instalar.setObjectName("btn_instalar")
        self.btn_instalar.setFixedHeight(44)
        self.btn_instalar.hide()
        self.btn_instalar.clicked.connect(self.iniciar_instalacion)
        self.layout_principal.addWidget(self.btn_instalar, alignment=Qt.AlignCenter)

        self.btn_gestionar = QPushButton(self.lang.get("btn_manage", "Manage installed apps"))
        self.btn_gestionar.setObjectName("btn_gestionar")
        self.btn_gestionar.clicked.connect(self.mostrar_gestor)
        self.layout_principal.addWidget(self.btn_gestionar, alignment=Qt.AlignCenter)

        # --- VISTA 2: EL GESTOR ---
        self.vista_gestor = QWidget()
        self.vista_gestor.hide()
        ly_g = QVBoxLayout(self.vista_gestor)
        
        lbl_t = QLabel(self.lang.get("title_gestor", "Installed Applications"))
        lbl_t.setObjectName("titulo_gestor")
        ly_g.addWidget(lbl_t)

        # --- BARRA DE BÚSQUEDA ---
        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText(self.lang.get("search_placeholder", "Buscar..."))
        self.txt_busqueda.setObjectName("barra_busqueda")
        # Conectamos el evento de escribir con la función de filtrar
        self.txt_busqueda.textChanged.connect(self.filtrar_aplicaciones)
        ly_g.addWidget(self.txt_busqueda)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("scroll_area")
        self.scroll.setWidgetResizable(True)
        self.contenedor_lista = QWidget()
        self.contenedor_lista.setObjectName("contenedor_lista")
        self.lista_layout = QVBoxLayout(self.contenedor_lista)
        self.lista_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.contenedor_lista)
        ly_g.addWidget(self.scroll)

        btn_v_gestor = QPushButton(self.lang.get("btn_back", "Back"))
        btn_v_gestor.setObjectName("btn_volver_gestor")
        btn_v_gestor.clicked.connect(self.estado_inicial)
        ly_g.addWidget(btn_v_gestor)

        self.layout_stack.addWidget(self.vista_instalacion)
        self.layout_stack.addWidget(self.vista_gestor)

    # --- MÉTODOS DE NAVEGACIÓN ---

    def mostrar_gestor(self):
        self.vista_instalacion.hide()
        self.vista_gestor.show()
        self.cargar_lista_apps()

    def estado_inicial(self):
        self.ruta_archivo = ""; self.manager_actual = None
        self.vista_gestor.hide(); self.vista_instalacion.show()
        self.btn_abrir.show(); self.btn_instalar.hide(); self.btn_volver.hide(); self.btn_gestionar.show()
        self.label_nombre.setText(self.lang.get("welcome_msg", "Welcome"))
        self.label_version.setText(self.lang.get("drag_drop_info", "Drag a file"))
        self.label_icono.setPixmap(QPixmap()); self.label_icono.setText("📦")
        self.barra_progreso.hide(); self.barra_progreso.setValue(0)

    # --- LÓGICA DE GESTIÓN DE APPS (CORREGIDA PARA EVITAR CRASH) ---

    def cargar_lista_apps(self):
        """Director de orquesta: Limpia y pide apps a todos los sistemas."""
        # 1. Limpieza de seguridad
        while self.lista_layout.count():
            item = self.lista_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # 2. Cargar aplicaciones estándar (.desktop)
        self.cargar_apps_desktop()
        
        # 3. Cargar aplicaciones de Flatpak (ACTUALIZADO AQUÍ)
        try:
            apps_flatpak = self.mgr_flatpak.listar_instalados()
            for app in apps_flatpak:
                nombre_label = f"{app['nombre']} (Flatpak)"
                
                # REEMPLAZA TU LÍNEA POR ESTA:
                self.lista_layout.addWidget(
                    WidgetAppInstalada(
                        nombre_label, 
                        app['id'], 
                        "preferences-desktop-apps", 
                        self.confirmar_borrado, 
                        self.lang
                    )
                )
        except Exception as e:
            print(f"Error cargando Flatpaks: {e}")

    def cargar_apps_desktop(self):
        """Busca aplicaciones tradicionales instaladas en el sistema."""
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
            with open(path, 'r', errors='ignore') as file:
                en_seccion_principal = False
                for l in file:
                    l = l.strip()
                    # Solo nos interesa lo que está dentro de [Desktop Entry]
                    if l == "[Desktop Entry]":
                        en_seccion_principal = True
                        continue
                    # Si empieza otra sección (como [Desktop Action]), dejamos de leer
                    if en_seccion_principal and l.startswith("["):
                        break
                    
                    if en_seccion_principal:
                        if l.startswith("Name="):
                            nombre = l.split('=', 1)[1].strip()
                        elif l.startswith("Icon="):
                            icono = l.split('=', 1)[1].strip()
        except: pass
        
        # Evitamos añadir entradas que no tengan nombre real o sean duplicados extraños
        if nombre != "App":
            # PASAMOS self.lang AL FINAL
            self.lista_layout.addWidget(
                WidgetAppInstalada(nombre, path, icono, self.confirmar_borrado, self.lang)
            )

    def confirmar_borrado(self, nombre, ruta_o_id):
        titulo = self.lang.get("btn_back", "Delete")
        pregunta_base = self.lang.get("msg_reinstall_ask", "Delete")
        
        if QMessageBox.question(self, titulo, f"{pregunta_base} {nombre}?") == QMessageBox.Yes:
            # LÓGICA DE DETECCIÓN:
            if "(Flatpak)" in nombre:
                # Si el nombre dice Flatpak, usamos el manager de Flatpak
                exito = self.mgr_flatpak.desinstalar(ruta_o_id)
            else:
                # Si no, decidimos entre AppImage o DEB según la ruta
                manager = self.mgr_appimage if "/home/" in ruta_o_id else self.mgr_deb
                exito = manager.desinstalar(ruta_o_id)
            
            if exito:
                QTimer.singleShot(500, self.cargar_lista_apps)

    # --- LÓGICA DE INSTALACIÓN ---

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()

    def dropEvent(self, event):
        archivo = event.mimeData().urls()[0].toLocalFile()
        self.preparar_archivo(archivo)

    def seleccionar_archivo(self):
        # Añadimos *.flatpak y *.flatpakref al final del filtro
        filtro = "Apps (*.deb *.AppImage *.flatpak *.flatpakref)"
        
        archivo, _ = QFileDialog.getOpenFileName(self, "Open", "", filtro)
        
        if archivo: 
            self.preparar_archivo(archivo)

    def preparar_archivo(self, archivo):
        self.ruta_archivo = archivo
        
        if archivo.endswith(".deb"): 
            self.manager_actual = self.mgr_deb
        elif archivo.endswith(".AppImage"): 
            self.manager_actual = self.mgr_appimage
        elif archivo.endswith(".flatpak") or archivo.endswith(".flatpakref"):
            self.manager_actual = self.mgr_flatpak
        else: 
            return

        nombre, info = self.manager_actual.obtener_datos(archivo)

        # --- CAMBIOS VISUALES INMEDIATOS ---
        self.btn_abrir.hide()
        self.btn_instalar.show()
        self.btn_instalar.setEnabled(True)
        self.btn_volver.show()
        self.btn_gestionar.hide()
        
        self.label_nombre.setText(nombre)
        self.label_version.setText(self.lang.get(info, info))
        
        # AQUÍ ESTÁ EL TRUCO:
        # Primero quitamos cualquier imagen vieja y ponemos el cohete YA.
        self.label_icono.setPixmap(QPixmap()) 
        self.label_icono.setText("🚀") 
        
        # Ahora, mientras el usuario ya ve el cohete, buscamos el icono real
        threading.Thread(target=self.manager_actual.buscar_icono, args=(archivo,), daemon=True).start()

   
   
    def iniciar_instalacion(self):
        if not self.manager_actual: return

        # 1. Obtener identificador (ID para Flatpak o Ruta para otros)
        identificador = self.ruta_archivo
        if hasattr(self.manager_actual, "obtener_id_desde_archivo"):
            id_leido = self.manager_actual.obtener_id_desde_archivo(self.ruta_archivo)
            if id_leido: identificador = id_leido

        # 2. Comprobar si ya existe
        if self.manager_actual.esta_instalado(identificador):
            # Traemos los textos desde el JSON
            titulo = self.lang.get("msg_already_installed_title", "Notice")
            mensaje = self.lang.get("msg_already_installed_body", "Already installed.")
            
            QMessageBox.information(self, titulo, mensaje)
            
            # 3. Resetear al estado inicial
            self.estado_inicial()
            return

        # 4. Instalación normal
        self.btn_instalar.setEnabled(False)
        self.barra_progreso.show()
        self.simular_progreso()
        threading.Thread(target=self.manager_actual.instalar, args=(self.ruta_archivo,), daemon=True).start()
    # --- ACTUALIZACIÓN VISUAL ---

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
        # Si el manager nos manda una ruta vacía o que no existe, dejamos el cohete puesto
        if not ruta or not os.path.exists(ruta):
            return 

        pix = QPixmap(ruta)
        if not pix.isNull():
            # Si la imagen es válida: borramos el texto "🚀" y ponemos el Pixmap
            self.label_icono.setText("")
            self.label_icono.setPixmap(pix.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # Si la imagen es corrupta o nula, no hacemos nada y se queda el cohete

    def actualizar_progreso(self, v): self.barra_progreso.setValue(v)

    def mostrar_resultado(self, exito, mensaje_key):
        self.barra_progreso.setValue(100)
        titulo = self.lang.get("window_title", "Info") if exito else "Error"
        
        # Traducimos el mensaje antes de mostrar la caja
        mensaje_traducido = self.lang.get(mensaje_key, mensaje_key)
        
        QMessageBox.information(self, titulo, mensaje_traducido)
        self.estado_inicial()

    def filtrar_aplicaciones(self, texto):
        """Filtra los widgets de la lista según el texto ingresado."""
        texto = texto.lower()
        # Recorremos todos los widgets que hay en el layout de la lista
        for i in range(self.lista_layout.count()):
            item = self.lista_layout.itemAt(i)
            widget = item.widget()
            if widget:
                # Comparamos el nombre de la app (lbl_nombre) con la búsqueda
                # Nota: Asegúrate que en WidgetAppInstalada el nombre sea accesible
                match = texto in widget.lbl_nombre.text().lower()
                widget.setVisible(match)