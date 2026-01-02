from PySide6.QtCore import QObject, Signal

class Comunicador(QObject):
    """
    Sistema de mensajería centralizado. 
    Permite que cualquier Manager envíe actualizaciones a la UI.
    """
    icono_listo = Signal(str)            # Ruta del icono extraído
    progreso_actualizado = Signal(int)    # Porcentaje 0-100
    instalacion_completada = Signal(bool, str) # (Éxito, Mensaje)