import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon

class WidgetAppInstalada(QFrame):
    def __init__(self, nombre, ruta_desktop, icono_ref, callback_borrar):
        super().__init__()
        self.setFixedHeight(65)
        
        # Asignamos un ID para el CSS
        self.setObjectName("widget_app")
        
        layout = QHBoxLayout(self)
        
        # --- ICONO ---
        self.lbl_icono = QLabel()
        self.lbl_icono.setObjectName("lbl_icono_app") # ID para CSS
        self.lbl_icono.setFixedSize(35, 35)
        self.lbl_icono.setAlignment(Qt.AlignCenter)
        
        pixmap = None
        if os.path.isabs(icono_ref) and os.path.exists(icono_ref):
            pixmap = QPixmap(icono_ref)
        else:
            pixmap = QIcon.fromTheme(icono_ref).pixmap(35, 35)
            
        if pixmap and not pixmap.isNull():
            self.lbl_icono.setPixmap(pixmap.scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_icono.setText("📦")
            
        layout.addWidget(self.lbl_icono)

        # --- NOMBRE ---
        lbl_nombre = QLabel(nombre)
        lbl_nombre.setObjectName("lbl_nombre_app") # ID para CSS
        lbl_nombre.setWordWrap(True)
        layout.addWidget(lbl_nombre)
        
        layout.addStretch()
        
        # --- BOTÓN ELIMINAR ---
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setObjectName("btn_eliminar_app") # ID para CSS
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        
        btn_eliminar.clicked.connect(lambda: callback_borrar(nombre, ruta_desktop))
        layout.addWidget(btn_eliminar)