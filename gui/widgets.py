import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon

class WidgetAppInstalada(QFrame):
    def __init__(self, nombre, ruta_desktop, icono_ref, callback_borrar, lang, tipo_app):
        super().__init__()
        self.setFixedHeight(75) 
        self.setObjectName("widget_app")
        
        # Layout Principal (Horizontal)
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 5, 15, 5)
        layout_principal.setSpacing(15)

        # --- 1. ICONO (Recuperado y Asegurado) ---
        self.lbl_icono = QLabel()
        self.lbl_icono.setFixedSize(40, 40) # Un poco más grande para que se vea bien
        self.lbl_icono.setAlignment(Qt.AlignCenter)
        
        pixmap = None
        # Intentamos cargar la ruta absoluta (para Snaps y Flatpaks)
        if icono_ref and os.path.isabs(str(icono_ref)) and os.path.exists(str(icono_ref)):
            pixmap = QPixmap(icono_ref)
        # Si no, buscamos en el tema del sistema (para apps System)
        elif icono_ref:
            nombre_limpio = os.path.splitext(str(icono_ref))[0]
            icon_theme = QIcon.fromTheme(nombre_limpio)
            if not icon_theme.isNull():
                pixmap = icon_theme.pixmap(40, 40)

        # Aplicamos el pixmap o el icono por defecto
        if pixmap and not pixmap.isNull():
            self.lbl_icono.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_icono.setText("📦")
            self.lbl_icono.setStyleSheet("font-size: 20px;")
        
        layout_principal.addWidget(self.lbl_icono)

        # --- 2. CONTENEDOR DE TEXTO (Nombre arriba, Badge abajo) ---
        layout_texto = QVBoxLayout()
        layout_texto.setSpacing(2)
        layout_texto.setAlignment(Qt.AlignVCenter) # Centra el bloque de texto verticalmente

        self.lbl_nombre = QLabel(nombre) 
        self.lbl_nombre.setObjectName("lbl_nombre_app")
        
        # Limitamos el ancho para que el nombre largo no eche al botón fuera
        self.lbl_nombre.setMaximumWidth(220) 
        
        self.lbl_badge = QLabel(tipo_app.upper())
        self.lbl_badge.setObjectName("badge_tipo")
        self.lbl_badge.setProperty("class", tipo_app.lower()) 
        self.lbl_badge.setFixedSize(65, 18) # Tamaño fijo para consistencia
        self.lbl_badge.setAlignment(Qt.AlignCenter)
        
        layout_texto.addWidget(self.lbl_nombre)
        layout_texto.addWidget(self.lbl_badge)
        
        layout_principal.addLayout(layout_texto)
        
        # Este espacio empuja el botón a la derecha
        layout_principal.addStretch()

        # --- 3. BOTÓN ELIMINAR ---
        texto_boton = lang.get("btn_delete", "Eliminar")
        btn_eliminar = QPushButton(texto_boton)
        btn_eliminar.setObjectName("btn_eliminar_app")
        btn_eliminar.setFixedSize(80, 32) # Tamaño fijo para que no baile
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        
        btn_eliminar.clicked.connect(lambda: callback_borrar(nombre, ruta_desktop, tipo_app))
        layout_principal.addWidget(btn_eliminar)