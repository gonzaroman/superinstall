import os
import subprocess
from .base import BaseManager

class DebManager(BaseManager):

    def __init__(self, comunicador, lang):
        super().__init__(comunicador, lang)


    def obtener_datos(self, ruta_archivo):
        """Extrae el nombre, versión y peso del archivo .deb."""
        try:
            # 1. Extraemos versión y nombre interno del paquete
            cmd = f"dpkg-deb -f '{ruta_archivo}' Package Version"
            salida = subprocess.check_output(cmd, shell=True, text=True)
            datos = {l.split(': ')[0]: l.split(': ')[1].strip() for l in salida.strip().split('\n') if ': ' in l}
            
            nombre = datos.get('Package', 'App')
            version = datos.get('Version', '0.0')
            
            # 2. Obtenemos el peso usando el método de la clase padre
            peso = self.obtener_tamano_archivo(ruta_archivo)
            
            # 3. Formateamos la descripción final
            # Ejemplo: "APP Debian • v0.0.28 • 85.2 MB • lista para instalar"
            txt_tipo = self.lang.get("type_debian", "Debian Package")
            txt_estado = self.lang.get("ready_to_install", "ready to install")
        
            return nombre.capitalize(), f"{txt_tipo} • v{version} • {peso} • {txt_estado}"
            
        except Exception as e:
            peso_error = self.obtener_tamano_archivo(ruta_archivo)
            txt_deb = self.lang.get("type_debian", "Debian Package")
            txt_err = self.lang.get("error_metadata", "Error reading metadata")
            return txt_deb, f"{txt_err} • {peso_error}"

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
        """
        Instala un archivo .deb usando apt-get para resolver dependencias 
        y captura el progreso real de la instalación.
        """
        # 1. Usamos apt-get en lugar de dpkg porque apt-get descarga dependencias faltantes.
        # El parámetro -o Dpkg::Progress-Fancy=1 fuerza a APT a mostrar la barra de progreso.
        comando = f"pkexec apt-get install -y -o Dpkg::Progress-Fancy=1 '{ruta_archivo}'"
        
        # 2. El patrón para APT es un poco distinto. 
        # Suele mostrar: "Progress: [ 25%]"
        patron_deb = r"Progress: \[ *(\d+)%\]"
        
        # 3. Ejecutamos usando la maquinaria del padre (BaseManager)
        exito = self.ejecutar_comando_con_progreso(comando, patron_deb)
        
        # 4. Resultado a la UI
        if exito:
            self.comunicador.instalacion_completada.emit(True, "install_success")
        else:
            self.comunicador.instalacion_completada.emit(False, "install_error")

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