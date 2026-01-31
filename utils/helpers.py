import os
import sys
import json
import locale

def obtener_ruta_recurso(ruta_relativa):
    """ Función necesaria para que PyInstaller encuentre los JSON e iconos """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)

def cargar_traducciones():
    lang_code = "en" # Idioma base por defecto

    try:
        # 1. Intento PRO: Mirar variables de entorno de Linux (las más fiables)
        # Esto detectará "it", "fr", "ru" incluso si no están instalados en el sistema
        for env_var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            val = os.environ.get(env_var)
            if val:
                lang_code = val.split('_')[0].split('.')[0].lower()
                break
        
        # 2. Intento de respaldo: Usar la librería locale estándar
        if lang_code == "en":
            sys_lang, _ = locale.getdefaultlocale()
            if sys_lang:
                lang_code = sys_lang[:2].lower()
    except:
        lang_code = "en"

    # 3. Definir rutas
    ruta_locales = obtener_ruta_recurso(os.path.join("assets", "locales"))
    archivo_sistema = os.path.join(ruta_locales, f"{lang_code}.json")
    archivo_ingles = os.path.join(ruta_locales, "en.json")

    # 4. Lógica de carga con "Fallback" automático
    # Si existe el del usuario (ej: ru.json), se usa. Si no, al inglés.
    ruta_final = archivo_sistema if os.path.exists(archivo_sistema) else archivo_ingles

    try:
        with open(ruta_final, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error crítico cargando traducciones: {e}")
        # Retorno de emergencia para que la app no explote si el JSON está roto
        return {"window_title": "SuperInstall", "welcome_msg": "Welcome"}