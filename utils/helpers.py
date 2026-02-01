import os
import sys
import json
import locale

def obtener_ruta_recurso(ruta_relativa):
    """ 
    Función híbrida: Funciona en PyInstaller, Dev (.py) y .DEB instalado 
    """
    try:
        # 1. Si está empaquetado con PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        # 2. Si es un script (.py) o instalado (.deb)
        # Este archivo está en: .../superinstall/utils/helpers.py
        # Queremos la raíz:     .../superinstall/
        utils_folder = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(utils_folder) # Subimos un nivel (..)

    return os.path.join(base_path, ruta_relativa)

def cargar_traducciones():
    lang_code = "en" # Idioma base por defecto

    try:
        # 1. Intento PRO: Mirar variables de entorno de Linux
        for env_var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            val = os.environ.get(env_var)
            if val:
                lang_code = val.split('_')[0].split('.')[0].lower()
                break
        
        # 2. Intento de respaldo: Librería locale
        if lang_code == "en":
            sys_lang, _ = locale.getdefaultlocale()
            if sys_lang:
                lang_code = sys_lang[:2].lower()
    except:
        lang_code = "en"

    # 3. Definir rutas usando la función CORREGIDA
    # Nota: No hace falta poner os.path.join("assets"...) dos veces si la función ya une
    archivo_sistema = obtener_ruta_recurso(os.path.join("assets", "locales", f"{lang_code}.json"))
    archivo_ingles = obtener_ruta_recurso(os.path.join("assets", "locales", "en.json"))
    archivo_espanol = obtener_ruta_recurso(os.path.join("assets", "locales", "es.json"))

    # 4. Lógica de carga con "Fallback" en cascada
    ruta_final = archivo_ingles # Por defecto seguro

    if os.path.exists(archivo_sistema):
        ruta_final = archivo_sistema
    elif os.path.exists(archivo_espanol): # Si falla el sistema (ej: ruso), intentamos español
        ruta_final = archivo_espanol
    
    try:
        with open(ruta_final, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error crítico cargando traducciones desde {ruta_final}: {e}")
        return {"window_title": "SuperInstall", "welcome_msg": "Welcome"}