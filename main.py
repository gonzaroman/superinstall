import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import InstaladorPro

def main():
    """Punto de entrada principal de la aplicación."""
    # 1. Crear la instancia de la aplicación
    app = QApplication(sys.argv)
    
    # 2. Configurar el nombre de la organización y la app (útil para el sistema)
    app.setApplicationName("SuperInstall")
    app.setOrganizationName("GonzaRoman")

    # 3. Crear y mostrar la ventana principal
    window = InstaladorPro()
    window.show()

    # 4. Ejecutar el bucle de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    main()