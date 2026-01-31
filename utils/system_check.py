import shutil
import platform
import subprocess

class SystemChecker:
    @staticmethod
    def esta_instalado(motor):
        """Verifica si el binario del motor existe en el sistema."""
        binarios = {
            "deb": "dpkg",
            "flatpak": "flatpak",
            "snap": "snap",
            "appimage": "chmod"
        }
        binario = binarios.get(motor.lower())
        return shutil.which(binario) is not None

    @staticmethod
    def obtener_arquitectura_sistema():
        """Detecta si el PC es x86_64, aarch64 (ARM), i386, etc."""
        return platform.machine().lower()

    @staticmethod
    def obtener_arquitectura_archivo(ruta, motor):
        """Extrae la arquitectura requerida por el instalador."""
        try:
            if motor == "deb":
                # Preguntamos al .deb qué arquitectura pide
                cmd = f"dpkg-deb -f '{ruta}' Architecture"
                return subprocess.check_output(cmd, shell=True, text=True).strip().lower()
            
            # Nota: Flatpak y Snap gestionan esto internamente, 
            # AppImage es más complejo de leer pero suele ser x86_64.
            return "all" 
        except:
            return "unknown"

    @staticmethod
    def es_compatible(arch_sistema, arch_archivo):
        """Lógica de compatibilidad cruzada."""
        if arch_archivo in ["all", "any", "unknown"]:
            return True
        
        # Mapeo de nombres comunes
        # x86_64 (64 bits normal)
        if arch_sistema == "x86_64":
            return arch_archivo in ["amd64", "x86_64", "i386", "i686"]
        
        # aarch64 (ARM 64 bits como los Mac M1/M2 o Raspberry Pi)
        if arch_sistema == "aarch64":
            return arch_archivo in ["arm64", "aarch64"]

        # i386 / i686 (32 bits antiguo)
        if arch_sistema in ["i386", "i686"]:
            return arch_archivo in ["i386", "i686"]
            
        return arch_sistema == arch_archivo