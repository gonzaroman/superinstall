import subprocess
import os
import re
from .base import BaseManager

class FlatpakManager(BaseManager):
    def __init__(self, comunicador, lang):
        super().__init__(comunicador, lang)
        
        self.lang = lang # Recibimos las traducciones desde la App principal

    def obtener_datos(self, ruta_archivo):
        """Extrae el nombre legible y el peso, usando traducciones."""
        base = os.path.basename(ruta_archivo).replace(".flatpakref", "").replace(".flatpak", "")
        partes = base.split('.')
        
        if len(partes) > 1:
            nombre = partes[-1]
            if nombre.lower() in ["app", "desktop", "auth"] and len(partes) > 2:
                nombre = partes[-2]
        else:
            nombre = partes[0]
        
        peso = self.obtener_tamano_archivo(ruta_archivo)
        
        # TRADUCCIONES: Usamos llaves del JSON
        txt_tipo = self.lang.get("type_flatpak", "Flatpak App")
        txt_estado = self.lang.get("ready_to_install", "ready to install")

        return nombre.capitalize(), f"{txt_tipo} • {peso} • {txt_estado}"

    def obtener_id_desde_archivo(self, ruta_archivo):
        """Extrae el ID real (io.github.X) de .flatpakref o binarios .flatpak."""
        if ruta_archivo.endswith(".flatpakref"):
            try:
                with open(ruta_archivo, 'r') as f:
                    for linea in f:
                        if linea.startswith(('Application=', 'Name=')):
                            return linea.split('=')[1].strip()
            except: return None
        
        elif ruta_archivo.endswith(".flatpak"):
            try:
                res = subprocess.run(
                    ["flatpak", "info", "--show-metadata", ruta_archivo], 
                    capture_output=True, text=True
                )
                for linea in res.stdout.split('\n'):
                    if linea.startswith('name='):
                        return linea.split('=')[1].strip()
            except: return None
        return None

    def esta_instalado(self, ruta_archivo):
        """Detecta si la app ya existe en el sistema."""
        app_id = self.obtener_id_desde_archivo(ruta_archivo)
        if not app_id:
            app_id = os.path.basename(ruta_archivo).split('.')[0]
        
        try:
            res = subprocess.run(["flatpak", "info", "--system", app_id], capture_output=True)
            return res.returncode == 0
        except: return False
        

    def instalar(self, ruta_archivo):
        """Instala el paquete capturando el progreso real."""
        comando = f"pkexec flatpak install --system -y --noninteractive --or-update '{ruta_archivo}'"
        patron_progreso = r"(\d+)%"
        
        exito = self.ejecutar_comando_con_progreso(comando, patron_progreso)
        
        # Si falla pero ya existe, lo damos por bueno
        if not exito and self.esta_instalado(ruta_archivo):
            exito = True 

        # Enviamos la LLAVE del mensaje, no el texto
        self.comunicador.instalacion_completada.emit(exito, "install_success" if exito else "install_error")

    def buscar_icono(self, ruta_archivo):
        """Busca el icono antes de instalar. Flatpak no lo permite fácilmente sin instalar,
        así que enviamos un icono genérico o vacío."""
        # Podrías poner una ruta a un logo de flatpak aquí si lo tienes
        self.comunicador.icono_listo.emit("")
    
    def listar_instalados(self):
        """Lista apps instaladas y busca sus iconos de forma inteligente."""
        apps = []
        bases = [
            os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor"),
            "/var/lib/flatpak/exports/share/icons/hicolor"
        ]
        tamanos = ["scalable/apps", "128x128/apps", "64x64/apps", "48x48/apps", "32x32/apps"]

        try:
            res = subprocess.run(
                ["flatpak", "list", "--app", "--columns=name,application"], 
                capture_output=True, text=True
            )
            if res.returncode == 0:
                for line in res.stdout.strip().split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        app_id = parts[1]
                        ruta_icono = self._buscar_icono_sistema(app_id, bases, tamanos)
                        
                        apps.append({
                            "nombre": parts[0], 
                            "id": app_id, 
                            "icono": ruta_icono
                        })
        except Exception as e:
            print(f"Error listing Flatpaks: {e}")
        return apps

    def _buscar_icono_sistema(self, app_id, bases, tamanos):
        """Método privado para no repetir la lógica del buscador de iconos."""
        for base in bases:
            for tam in tamanos:
                carpeta = os.path.join(base, tam)
                if not os.path.exists(carpeta): continue
                for ext in [".png", ".svg"]:
                    posible = os.path.join(carpeta, f"{app_id}{ext}")
                    if os.path.exists(posible):
                        return posible
        return "preferences-desktop-apps"

    def desinstalar(self, app_id):
        """Desinstala la aplicación del sistema."""
        try:
            comando = ["flatpak", "uninstall", "-y", "--noninteractive", app_id]
            res = subprocess.run(comando, capture_output=True, text=True)
            return res.returncode == 0
        except:
            return False