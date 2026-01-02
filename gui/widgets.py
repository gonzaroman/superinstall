import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon

class WidgetAppInstalada(QFrame):
    # Añadimos 'lang' como quinto argumento (el sexto contando 'self')
    def __init__(self, nombre, ruta_desktop, icono_ref, callback_borrar, lang):
        super().__init__()
        self.setFixedHeight(65)
        self.setObjectName("widget_app")
        
        layout = QHBoxLayout(self)
        
        # --- ICONO ---
        self.lbl_icono = QLabel()
        self.lbl_icono.setObjectName("lbl_icono_app")
        self.lbl_icono.setFixedSize(35, 35)
        self.lbl_icono.setAlignment(Qt.AlignCenter)
        
        pixmap = None
        if os.path.isabs(icono_ref) and os.path.exists(icono_ref):
            pixmap = QPixmap(icono_ref)
        else:
            nombre_limpio = os.path.splitext(icono_ref)[0]
            icon_theme = QIcon.fromTheme(nombre_limpio)
            if not icon_theme.isNull():
                pixmap = icon_theme.pixmap(35, 35)
            else:
                for ruta_sys in ["/usr/share/pixmaps", "/usr/share/icons/hicolor/48x48/apps"]:
                    busqueda = os.path.join(ruta_sys, f"{nombre_limpio}.png")
                    if os.path.exists(busqueda):
                        pixmap = QPixmap(busqueda)
                        break

        if pixmap and not pixmap.isNull():
            self.lbl_icono.setPixmap(pixmap.scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_icono.setText("📦")
            
        layout.addWidget(self.lbl_icono)

        # --- NOMBRE ---
        lbl_nombre = QLabel(nombre)
        lbl_nombre.setObjectName("lbl_nombre_app")
        lbl_nombre.setWordWrap(True)
        layout.addWidget(lbl_nombre)
        
        layout.addStretch()
        
        # --- BOTÓN ELIMINAR (TRADUCIDO) ---
        # Buscamos 'btn_delete' en el diccionario, si no existe ponemos 'Delete'
        texto_boton = lang.get("btn_delete", "Delete")
        btn_eliminar = QPushButton(texto_boton)
        btn_eliminar.setObjectName("btn_eliminar_app")
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        
        btn_eliminar.clicked.connect(lambda: callback_borrar(nombre, ruta_desktop))
        layout.addWidget(btn_eliminar)