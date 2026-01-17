import shutil

class SystemChecker:
    @staticmethod
    def esta_instalado(motor):
        # Mapeamos extensiones/nombres a binarios reales de Linux
        binarios = {
            "deb": "dpkg",
            "flatpak": "flatpak",
            "snap": "snap",
            "appimage": "chmod" # AppImage solo necesita permisos, siempre True
        }
        binario = binarios.get(motor.lower())
        return shutil.which(binario) is not None