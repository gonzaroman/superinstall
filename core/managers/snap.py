import subprocess
import os
import threading
from .base import BaseManager

class SnapManager(BaseManager):
    def __init__(self, comunicador):
        super().__init__(comunicador)

    def obtener_datos(self, ruta_archivo):
        """Extrae el nombre legible del archivo .snap."""
        base = os.path.basename(ruta_archivo).replace(".snap", "")
        # Limpiamos posibles versiones (ej: spotify_1.0 -> Spotify)
        nombre = base.split('_')[0].split('-')[0]
        return nombre.capitalize(), "snap_info"

    def buscar_icono(self, ruta_archivo):
        """Para instalaciones nuevas desde archivo, usamos el cohete."""
        self.comunicador.icono_listo.emit("")

    def esta_instalado(self, app_id):
        """Verifica si el snap está en la lista de instalados."""
        try:
            res = subprocess.run(["snap", "list", app_id], capture_output=True)
            return res.returncode == 0
        except: return False

    def instalar(self, ruta_archivo):
        """
        Instala un paquete Snap local capturando el progreso en tiempo real.
        """
        # 1. Comando como cadena (string) para que funcione con shell=True en BaseManager
        # Usamos pkexec para la elevación de privilegios
        comando = f"pkexec snap install --dangerous {ruta_archivo}"
        
        # 2. Definimos el patrón para buscar el porcentaje (ejemplo: "Mounting snap 15%")
        patron_snap = r"(\d+)%"
        
        # 3. Llamamos al método del padre que ya tiene toda la lógica de lectura
        # NOTA: No hace falta crear un Thread aquí porque main_window ya lo lanza en uno
        exito = self.ejecutar_comando_con_progreso(comando, patron_snap)
        
        # 4. Emitimos el resultado final
        if exito:
            self.comunicador.instalacion_completada.emit(True, "install_success")
        else:
            self.comunicador.instalacion_completada.emit(False, "install_error")

    def buscar_icono(self, ruta_archivo):
        """Si es un archivo .snap externo, usamos el logo de Snap."""
        # Puedes descargar un logo de snap y ponerlo en assets/snap_logo.png
        # Por ahora, enviamos vacío para que use el cohete o un icono por defecto
        self.comunicador.icono_listo.emit("")

    def listar_instalados(self):
        apps = []
        ruta_iconos_sistema = "/var/lib/snapd/desktop/icons/"
        
        try:
            res = subprocess.run(["snap", "list"], capture_output=True, text=True)
            if res.returncode == 0:
                lineas = res.stdout.strip().split('\n')[1:]
                for line in lineas:
                    parts = line.split()
                    if not parts: continue
                    snap_id = parts[0]
                    
                    if snap_id in ["core", "core18", "core20", "core22", "bare", "gtk-common-themes", "snapd"]:
                        continue

                    # BUSCADOR DE ICONOS MEJORADO
                    ruta_icono_final = "preferences-desktop-apps"
                    encontrado = False

                    # OPCIÓN 1: La ruta interna del snap (Suele ser la más fiable)
                    # /snap/nombre-app/current/meta/gui/icon.png
                    posibles_internos = [
                        f"/snap/{snap_id}/current/meta/gui/icon.png",
                        f"/snap/{snap_id}/current/meta/gui/icon.svg"
                    ]
                    for p in posibles_internos:
                        if os.path.exists(p):
                            ruta_icono_final = p
                            encontrado = True
                            break

                    # OPCIÓN 2: Buscar en la carpeta de iconos de snapd
                    if not encontrado and os.path.exists(ruta_iconos_sistema):
                        for f in os.listdir(ruta_iconos_sistema):
                            if f.startswith(snap_id) and (f.endswith(".png") or f.endswith(".svg")):
                                ruta_icono_final = os.path.join(ruta_iconos_sistema, f)
                                encontrado = True
                                break
                    
                    apps.append({
                        "nombre": snap_id.capitalize(),
                        "id": snap_id,
                        "icono": ruta_icono_final
                    })
        except Exception as e:
            print(f"Error en motor Snap: {e}")
        return apps

    def desinstalar(self, app_id):
        try:
            print(f"Iniciando comando: pkexec snap remove {app_id}")
            # Añadimos capture_output=True y text=True para leer el error real
            res = subprocess.run(
                ["pkexec", "snap", "remove", app_id], 
                capture_output=True, 
                text=True
            )
            
            if res.returncode == 0:
                print(f"Snap {app_id} eliminado correctamente.")
                return True
            else:
                # Esto nos dirá en la terminal por qué no se borró
                print(f"Error al eliminar Snap: {res.stderr}")
                return False
        except Exception as e:
            print(f"Excepción en SnapManager: {e}")
            return False