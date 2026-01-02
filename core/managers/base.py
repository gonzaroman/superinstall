from abc import ABC, abstractmethod
from utils.signals import Comunicador

class BaseManager(ABC):
    """
    Clase abstracta que define el comportamiento de cualquier gestor de paquetes.
    """
    def __init__(self, comunicador: Comunicador):
        self.comunicador = comunicador

    @abstractmethod
    def obtener_datos(self, ruta_archivo):
        """Extrae nombre y versión del paquete."""
        pass

    @abstractmethod
    def buscar_icono(self, ruta_archivo):
        """Extrae el icono del paquete para mostrarlo en la UI."""
        pass

    @abstractmethod
    def instalar(self, ruta_archivo):
        """Ejecuta la lógica de instalación/integración."""
        pass

    @abstractmethod
    def desinstalar(self, identificador):
        """Lógica para eliminar la aplicación del sistema."""
        pass

    @abstractmethod
    def esta_instalado(self, ruta_archivo):
        """Devuelve True si la aplicación ya existe en el sistema."""
        pass