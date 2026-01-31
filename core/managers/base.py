import os
import signal
import subprocess
import re
from abc import ABC, abstractmethod
from utils.signals import Comunicador

class BaseManager(ABC):
    def __init__(self, comunicador, lang): # <-- Añadimos lang aquí
        self.comunicador = comunicador
        self.lang = lang # <-- Ahora todos los managers conocen el idioma
        self.proceso_actual = None
    
    

    
    def ejecutar_comando_con_progreso(self, comando, patron_regex):
        try:
            # CORRECCIÓN: Un solo Popen y lo guardamos en self.proceso_actual
            self.proceso_actual = subprocess.Popen(
                comando,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                start_new_session=True
            )

            # Leemos línea a línea desde self.proceso_actual
            for linea in self.proceso_actual.stdout:
                linea_limpia = linea.strip()
                print(linea_limpia) # Debug
                
                match = re.search(patron_regex, linea_limpia)
                if match:
                    try:
                        valor = int(match.group(1))
                        self.comunicador.progreso_actualizado.emit(valor)
                    except (ValueError, IndexError):
                        pass

            self.proceso_actual.wait()
            return self.proceso_actual.returncode == 0
        
            
        except Exception as e:
            print(f"Error ejecutando comando: {e}")
            return False

    def cancelar_operacion(self):
        if self.proceso_actual:
            try:
                # Usamos SIGKILL (señal 9) para forzar el cierre inmediato
                # de pkexec y todos sus hijos (apt, dpkg, etc.)
                os.killpg(os.getpgid(self.proceso_actual.pid), signal.SIGKILL)
                print(">>> Proceso ELIMINADO forzosamente por el usuario.")
            except ProcessLookupError:
                pass 
            except Exception as e:
                print(f"Error al cancelar: {e}")
            finally:
                self.proceso_actual = None
                
    def obtener_tamano_archivo(self, ruta_archivo):
        """Devuelve el tamaño del archivo en formato legible (MB/KB)."""
        try:
            bytes_size = os.path.getsize(ruta_archivo)
            if bytes_size < 1024 * 1024:
                return f"{bytes_size / 1024:.1f} KB"
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        except:
            return self.lang.get("unknown_size", "Unknown size")

    # --- MÉTODOS ABSTRACTOS (A implementar por cada hijo) ---
    @abstractmethod
    def obtener_datos(self, ruta_archivo): pass

    @abstractmethod
    def buscar_icono(self, ruta_archivo): pass

    @abstractmethod
    def instalar(self, ruta_archivo): pass

    @abstractmethod
    def desinstalar(self, identificador): pass

    @abstractmethod
    def esta_instalado(self, ruta_archivo): pass