import os
import shutil
import subprocess
from .base import BaseManager

class AppImageManager(BaseManager):
    def __init__(self, comunicador):
        super().__init__(comunicador)
        self.ruta_icono_extraido = ""  # Aquí guardaremos la ruta para el .desktop

    def obtener_datos(self, ruta_archivo):
        nombre = os.path.basename(ruta_archivo).replace(".AppImage", "").split("-")[0]
        return nombre.capitalize(), "appimage_info" # <--- Enviamos la clave

    def buscar_icono(self, ruta_appimage):
        """Tu lógica original exacta de extracción de iconos"""
        ruta_temp = "/tmp/superinstall_appdir"
        if os.path.exists(ruta_temp):
            try: shutil.rmtree(ruta_temp)
            except: pass
        os.makedirs(ruta_temp, exist_ok=True)
        
        try:
            os.chmod(ruta_appimage, 0o755)
            comandos_rapidos = [
                [ruta_appimage, "--appimage-extract", ".DirIcon"],
                [ruta_appimage, "--appimage-extract", "*.png"],
                [ruta_appimage, "--appimage-extract", "*.svg"],
            ]
            icono_encontrado = False
            root_extract = os.path.join(ruta_temp, "squashfs-root")
            
            for cmd in comandos_rapidos:
                if icono_encontrado: break
                try:
                    subprocess.run(cmd, cwd=ruta_temp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                    if os.path.exists(root_extract):
                        icono = self._buscar_mejor_icono_rapido_ORIGINAL(root_extract)
                        if icono:
                            icono_encontrado = True
                            break
                except: continue
            
            if not icono_encontrado:
                try:
                    subprocess.run([ruta_appimage, "--appimage-extract"], cwd=ruta_temp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                except: return
            
            if not os.path.exists(root_extract): return
            
            icono = self._buscar_mejor_icono_rapido_ORIGINAL(root_extract)
            if icono:
                ext = os.path.splitext(icono)[1]
                ruta_preview = f"/tmp/appimage_last_icon{ext}"
                shutil.copy2(icono, ruta_preview)
                self.ruta_icono_extraido = ruta_preview # Guardamos para instalar()
                self.comunicador.icono_listo.emit(ruta_preview) # Enviamos a la GUI
        except: pass

    def _buscar_mejor_icono_rapido_ORIGINAL(self, root_extract):
        """Tu función original de búsqueda con os.walk"""
        rutas_prioritarias = [".DirIcon", "usr/share/icons/hicolor/256x256/apps", "usr/share/icons/hicolor/scalable/apps", "usr/share/pixmaps", "."]
        for ruta_rel in rutas_prioritarias:
            ruta_busqueda = os.path.join(root_extract, ruta_rel)
            if not os.path.exists(ruta_busqueda): continue
            try:
                if os.path.isfile(ruta_busqueda): archivos = [ruta_busqueda]
                else: archivos = [os.path.join(ruta_busqueda, f) for f in os.listdir(ruta_busqueda) if f.lower().endswith(('.png', '.svg'))]
                for archivo in archivos:
                    nombre = os.path.basename(archivo).lower()
                    if any(x in nombre for x in [".diricon", "icon", "logo"]) and archivo.endswith('.png'):
                        if os.path.getsize(archivo) > 1000: return archivo
            except: continue
        
        candidatos = []
        for root, dirs, files in os.walk(root_extract):
            nivel = root.replace(root_extract, '').count(os.sep)
            if nivel > 2:
                dirs[:] = []
                continue
            for f in files:
                if f.lower().endswith(('.png', '.svg')):
                    ruta_full = os.path.join(root, f)
                    try:
                        tam = os.path.getsize(ruta_full)
                        if tam > 1000: candidatos.append((tam, ruta_full))
                        if len(candidatos) >= 10: break
                    except: continue
            if len(candidatos) >= 10: break
        
        if candidatos:
            candidatos.sort(reverse=True)
            return candidatos[0][1]
        return None

    def instalar(self, ruta_archivo):
        """Usa la ruta_icono_extraido que encontró buscar_icono"""
        dest_bin = os.path.expanduser("~/Applications")
        dest_apps = os.path.expanduser("~/.local/share/applications")
        dest_icons = os.path.expanduser("~/.local/share/icons")
        for d in [dest_bin, dest_apps, dest_icons]: os.makedirs(d, exist_ok=True)
        
        nombre_app = os.path.basename(ruta_archivo).replace(".AppImage", "").split("-")[0].capitalize()
        nombre_limpio = nombre_app.lower().replace(" ", "_")
        ruta_ejecutable = os.path.join(dest_bin, os.path.basename(ruta_archivo))
        
        try:
            shutil.copy2(ruta_archivo, ruta_ejecutable)
            os.chmod(ruta_ejecutable, 0o755)
            
            ruta_icon_final = "system-run"
            if self.ruta_icono_extraido:
                ruta_icon_final = os.path.join(dest_icons, f"{nombre_limpio}{os.path.splitext(self.ruta_icono_extraido)[1]}")
                shutil.copy2(self.ruta_icono_extraido, ruta_icon_final)
            
            with open(os.path.join(dest_apps, f"{nombre_limpio}.desktop"), "w") as f:
                f.write(f"[Desktop Entry]\nType=Application\nName={nombre_app}\nExec=\"{ruta_ejecutable}\"\nIcon={ruta_icon_final}\nTerminal=false\nCategories=Utility;\n")
            
            self.comunicador.instalacion_completada.emit(True, "install_success")
        except Exception as e:
            self.comunicador.instalacion_completada.emit(False, "install_error")

    def desinstalar(self, ruta_desktop):
        """Tu lógica original de borrado de archivos de usuario"""
        try:
            rb, ri = "", ""
            with open(ruta_desktop, 'r') as f:
                c = f.read()
                for l in c.split('\n'):
                    if l.startswith("Exec="): rb = l.split('=')[1].strip('"').split()[0]
                    if l.startswith("Icon="): ri = l.split('=')[1]
            if os.path.exists(rb) and "Applications" in rb: os.remove(rb)
            if os.path.exists(ri) and ".local" in ri: os.remove(ri)
            if os.path.exists(ruta_desktop): os.remove(ruta_desktop)
            return True
        except: return False
    
    def esta_instalado(self, ruta_archivo):
        dest_bin = os.path.expanduser("~/Applications")
        ruta_ejecutable = os.path.join(dest_bin, os.path.basename(ruta_archivo))
        return os.path.exists(ruta_ejecutable)