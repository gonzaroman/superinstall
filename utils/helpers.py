import os
import json
import locale

def cargar_traducciones():
    """
    Detecta el idioma del sistema y carga el JSON. 
    Usa rutas absolutas para evitar errores según dónde se abra la terminal.
    """
    # 1. Detectar idioma de forma más segura
    try:
        idioma_sistema, _ = locale.getdefaultlocale()
        codigo_iso = idioma_sistema.split('_')[0].lower() if idioma_sistema else "en"
    except Exception:
        codigo_iso = "en"

    # 2. Definir rutas ABSOLUTAS (Esto evita que falle al ejecutar el programa)
    # Buscamos la carpeta 'assets/locales' relativa a este archivo helpers.py
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_base = os.path.join(directorio_actual, "..", "assets", "locales")
    
    ruta_idioma = os.path.join(ruta_base, f"{codigo_iso}.json")
    ruta_default = os.path.join(ruta_base, "en.json")

    # 3. Lógica de carga con "doble red de seguridad"
    archivo_a_cargar = ruta_idioma if os.path.exists(ruta_idioma) else ruta_default
    
    # Si ni siquiera existe el inglés (en.json), devolvemos algo para que la App no muera
    if not os.path.exists(archivo_a_cargar):
        print(f"⚠️ Alerta: No se encontró ningún archivo de idioma en {ruta_base}")
        return {}

    try:
        with open(archivo_a_cargar, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error crítico leyendo JSON: {e}")
        return {}