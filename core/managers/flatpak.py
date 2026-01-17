import subprocess
import os
import re
from .base import BaseManager

class FlatpakManager(BaseManager):
    def __init__(self, comunicador):
        super().__init__(comunicador)

    def obtener_datos(self, ruta_archivo):
        """Extrae el nombre legible para la interfaz."""
        base = os.path.basename(ruta_archivo).replace(".flatpakref", "").replace(".flatpak", "")
        partes = base.split('.')
        
        if len(partes) > 1:
            nombre = partes[-1]
            if nombre.lower() in ["app", "desktop", "auth"] and len(partes) > 2:
                nombre = partes[-2]
        else:
            nombre = partes[0]

        return nombre.capitalize(), "APP Flatpak • lista para instalar"

    def buscar_icono(self, ruta_archivo):
        self.comunicador.icono_listo.emit("")

    def obtener_id_desde_archivo(self, ruta_archivo):
        """
        Extrae el ID real (io.github.X) tanto de .flatpakref como de .flatpak binarios.
        """
        if ruta_archivo.endswith(".flatpakref"):
            try:
                with open(ruta_archivo, 'r') as f:
                    for linea in f:
                        if linea.startswith('Application=') or linea.startswith('Name='):
                            return linea.split('=')[1].strip()
            except: return None
        
        elif ruta_archivo.endswith(".flatpak"):
            try:
                # Truco profesional: preguntamos al binario por su propio ID
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
        """Detecta si la app ya existe usando el ID real del sistema."""
        app_id = self.obtener_id_desde_archivo(ruta_archivo)
        if not app_id:
            # Fallback al nombre del archivo si falla la extracción
            app_id = os.path.basename(ruta_archivo).split('.')[0]
        
        try:
            # Buscamos específicamente en el sistema
            res = subprocess.run(["flatpak", "info", "--system", app_id], capture_output=True)
            return res.returncode == 0
        except: return False

    def instalar(self, ruta_archivo):
        """Instala o actualiza el paquete capturando el progreso real."""
        comando = f"pkexec flatpak install --system -y --noninteractive --or-update {ruta_archivo}"
        patron_progreso = r"(\d+)%"
        
        # Ejecutamos el motor de la clase base
        exito = self.ejecutar_comando_con_progreso(comando, patron_progreso)
        
        # --- EL TRUCO MAESTRO ---
        # Si el comando falla, comprobamos si es simplemente porque ya estaba instalado
        if not exito:
            if self.esta_instalado(ruta_archivo):
                print("DEBUG: Flatpak dio error pero la app ya existe. Marcamos como éxito.")
                exito = True 

        if exito:
            self.comunicador.instalacion_completada.emit(True, "install_success")
        else:
            self.comunicador.instalacion_completada.emit(False, "install_error")

    

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