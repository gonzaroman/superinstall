import os
import json
import locale

def cargar_traducciones():
    """
    Detecta el idioma del sistema y carga el archivo JSON correspondiente.
    Si el idioma no existe, carga el inglés por defecto.
    """
    # 1. Detectar idioma (ej: 'es_ES', 'en_US')
    idioma_sistema, _ = locale.getdefaultlocale()
    codigo_iso = idioma_sistema.split('_')[0] if idioma_sistema else "en"

    # 2. Definir rutas
    ruta_base = os.path.join("assets", "locales")
    ruta_idioma = os.path.join(ruta_base, f"{codigo_iso}.json")
    ruta_default = os.path.join(ruta_base, "en.json")

    # 3. Cargar el archivo
    archivo_a_cargar = ruta_idioma if os.path.exists(ruta_idioma) else ruta_default
    
    try:
        with open(archivo_a_cargar, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando traducciones: {e}")
        return {}