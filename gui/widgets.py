import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSize
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

        #
        # --- 1. ICONO (Versión Ultra-Compatible) ---
        self.lbl_icono = QLabel()
        self.lbl_icono.setFixedSize(48, 48) 
        self.lbl_icono.setAlignment(Qt.AlignCenter)
        self.lbl_icono.setObjectName("lbl_icono_app")

        
        
        pixmap = None
        icono_str = str(icono_ref) if icono_ref else ""

        # A. Intentar como RUTA FÍSICA absoluta
        if os.path.isabs(icono_str) and os.path.exists(icono_str):
            pixmap = QPixmap(icono_str)
        
        # B. Intentar como NOMBRE DE TEMA (Ej: "discord", "spotify")
        if (not pixmap or pixmap.isNull()) and icono_str:
            # Quitamos la extensión y la ruta por si acaso viene sucio
            nombre_icon_tema = os.path.basename(icono_str).split('.')[0]
            icon_theme = QIcon.fromTheme(nombre_icon_tema)
            
            if not icon_theme.isNull():
                # Pedimos el pixmap al tema del sistema (Zorin/Ubuntu)
                pixmap = icon_theme.pixmap(QSize(44, 44))

        # C. APLICAR O FALLBACK
        if pixmap and not pixmap.isNull():
            self.lbl_icono.setPixmap(pixmap.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Fallback elegante: Si no hay icono, usamos uno genérico del sistema
            icon_fallback = QIcon.fromTheme("application-x-executable")
            if not icon_fallback.isNull():
                self.lbl_icono.setPixmap(icon_fallback.pixmap(44, 44))
            else:
                self.lbl_icono.setText("📦")
                self.lbl_icono.setStyleSheet("font-size: 24px;")
        
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
        btn_eliminar.setFixedSize(90, 32) # Tamaño fijo para que no baile
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        
        btn_eliminar.clicked.connect(lambda: callback_borrar(nombre, ruta_desktop, tipo_app))
        layout_principal.addWidget(btn_eliminar)