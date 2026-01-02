import subprocess
import os
import threading
from .base import BaseManager

class FlatpakManager(BaseManager):
    def __init__(self, comunicador):
        super().__init__(comunicador)

    def obtener_datos(self, ruta_archivo):
        """Extrae el nombre de la app intentando evitar prefijos como 'io.github'."""
        base = os.path.basename(ruta_archivo).replace(".flatpakref", "").replace(".flatpak", "")
        
        # Dividimos por puntos
        partes = base.split('.')
        
        # Si tiene puntos, solemos querer la última o penúltima parte
        # Ejemplo: io.ente.auth -> 'Auth' | Poliedros.flatpak -> 'Poliedros'
        if len(partes) > 1:
            nombre = partes[-1]
            if nombre.lower() in ["app", "desktop", "auth"] and len(partes) > 2:
                nombre = partes[-2]
        else:
            nombre = partes[0]

        return nombre.capitalize(), "flatpak_info"

    def buscar_icono(self, ruta_archivo):
        # Mantenemos el cohete 🚀 para archivos externos
        self.comunicador.icono_listo.emit("")

    def esta_instalado(self, app_id):
        try:
            id_limpio = app_id.split('/')[-1].replace(".flatpakref", "").replace(".flatpak", "")
            res = subprocess.run(["flatpak", "info", id_limpio], capture_output=True)
            return res.returncode == 0
        except: return False

    def instalar(self, ruta_archivo):
        def proceso():
            try:
                # Añadimos --or-update para que no dé error si ya existe
                comando = ["flatpak", "install", "--user", "-y", "--or-update", ruta_archivo]
                
                print(f"Ejecutando: {' '.join(comando)}")
                
                process = subprocess.run(comando, capture_output=True, text=True)
                
                if process.returncode == 0:
                    self.comunicador.instalacion_completada.emit(True, "install_success")
                else:
                    # Ahora solo veremos errores reales (como falta de internet)
                    print(f"--- ERROR DE FLATPAK ---")
                    print(process.stderr)
                    self.comunicador.instalacion_completada.emit(False, "install_error")
            except Exception as e:
                print(f"CRASH: {e}")
                self.comunicador.instalacion_completada.emit(False, "install_error")
        
        threading.Thread(target=proceso, daemon=True).start()

    def listar_instalados(self):
        apps = []
        # Directorios base de Flatpak
        bases = [
            os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor"),
            "/var/lib/flatpak/exports/share/icons/hicolor"
        ]
        # Tamaños de carpeta a buscar, de mayor a menor calidad
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
                        ruta_icono_final = "preferences-desktop-apps" # Icono por defecto

                        # BUSCADOR INTELIGENTE
                        encontrado = False
                        for base in bases:
                            if encontrado: break
                            for tam in tamanos:
                                if encontrado: break
                                carpeta = os.path.join(base, tam)
                                if not os.path.exists(carpeta): continue
                                
                                # Probamos con .png y con .svg
                                for ext in [".png", ".svg"]:
                                    posible = os.path.join(carpeta, f"{app_id}{ext}")
                                    if os.path.exists(posible):
                                        ruta_icono_final = posible
                                        encontrado = True
                                        break
                        
                        apps.append({
                            "nombre": parts[0], 
                            "id": app_id, 
                            "icono": ruta_icono_final
                        })
        except Exception as e:
            print(f"Error en motor Flatpak: {e}")
        return apps

    def desinstalar(self, app_id):
        try:
            # We remove --user so Flatpak searches in BOTH system and user folders.
            # This fixes the "No installed refs found" error.
            comando = ["flatpak", "uninstall", "-y", "--noninteractive", app_id]
            
            res = subprocess.run(comando, capture_output=True, text=True)
            
            if res.returncode == 0:
                print(f"Successfully uninstalled: {app_id}")
                return True
            else:
                # If it still fails, it might be a permission issue
                print(f"Flatpak Uninstall Error: {res.stderr}")
                return False
        except Exception as e:
            print(f"Uninstall Crash: {e}")
            return False

    def obtener_id_desde_archivo(self, ruta_archivo):
        """Busca la línea Application= o Name= dentro del archivo .flatpakref"""
        if not ruta_archivo.endswith(".flatpakref"): return None
        try:
            with open(ruta_archivo, 'r') as f:
                for linea in f:
                    if linea.startswith('Application=') or linea.startswith('Name='):
                        return linea.split('=')[1].strip()
        except: return None