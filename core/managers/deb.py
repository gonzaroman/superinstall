import os
import subprocess
from .base import BaseManager

class DebManager(BaseManager):
    def obtener_datos(self, ruta_archivo):
        """Extrae el nombre del paquete y la versión usando dpkg-deb."""
        try:
            cmd = f"dpkg-deb -f '{ruta_archivo}' Package Version"
            salida = subprocess.check_output(cmd, shell=True, text=True)
            datos = {l.split(': ')[0]: l.split(': ')[1] for l in salida.strip().split('\n') if ': ' in l}
            return datos.get('Package', 'App'), datos.get('Version', '0.0')
        except:
            return "Archivo", "???"

    def buscar_icono(self, ruta_deb):
        """Extrae el icono del paquete .deb."""
        ruta_temp = "/tmp/instalador_icono_deb"
        if not os.path.exists(ruta_temp):
            os.makedirs(ruta_temp)
            
        try:
            # Intento 1: Buscar iconos de alta resolución
            cmd = f"dpkg-deb -c '{ruta_deb}' | grep -E '256|128|scalable' | grep -E '.png|.svg' | head -n 1"
            linea = subprocess.getoutput(cmd)
            
            # Intento 2: Si falla, buscar cualquier cosa que parezca un icono
            if not linea:
                cmd = f"dpkg-deb -c '{ruta_deb}' | grep -E '.png|.svg' | grep -E 'icon|logo' | head -n 1"
                linea = subprocess.getoutput(cmd)
            
            if linea:
                ruta_en_deb = linea.split()[-1].lstrip('.')
                ruta_final_icono = f"{ruta_temp}/icon.png"
                # Extraer el archivo específico del tar del deb
                subprocess.run(f"dpkg-deb --fsys-tarfile '{ruta_deb}' | tar -xOf - '.{ruta_en_deb}' > {ruta_final_icono}", shell=True, timeout=5)
                self.comunicador.icono_listo.emit(ruta_final_icono)
        except Exception as e:
            print(f"Error extrayendo icono DEB: {e}")

    def instalar(self, ruta_archivo):
        """Instala el paquete usando pkexec y apt."""
        try:
            # Comando que ya tenías configurado
            comando = f'pkexec apt-get install -y "{ruta_archivo}"'
            res = subprocess.run(comando, shell=True, capture_output=True)
            
            if res.returncode == 0:
                self.comunicador.instalacion_completada.emit(True, "Instalado correctamente en el sistema")
            else:
                self.comunicador.instalacion_completada.emit(False, "La instalación fue cancelada o falló")
        except Exception as e:
            self.comunicador.instalacion_completada.emit(False, str(e))

    def desinstalar(self, ruta_desktop):
        """Identifica el paquete a través del archivo .desktop y lo elimina."""
        try:
            # Tu lógica para encontrar qué paquete instaló ese archivo .desktop
            res = subprocess.getoutput(f"dpkg -S '{ruta_desktop}'")
            if ":" in res:
                pkg = res.split(":")[0]
                # Eliminación silenciosa
                subprocess.run(f"pkexec apt-get remove -y {pkg}", shell=True)
                return True
        except:
            # Si falla dpkg, intentamos borrar el acceso directo al menos
            subprocess.run(f"pkexec rm '{ruta_desktop}'", shell=True)
        return False
    
    def esta_instalado(self, ruta_archivo):
        nombre_pkg, _ = self.obtener_datos(ruta_archivo)
        # Ejecutamos dpkg -s para ver si el paquete está instalado
        res = subprocess.run(["dpkg", "-s", nombre_pkg], capture_output=True)
        return res.returncode == 0