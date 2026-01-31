# 🚀 SuperInstall: El Instalador Universal Definitivo para Linux

**¿Cansado de pelearte con la terminal o de buscar instaladores diferentes para cada formato?** SuperInstall es la herramienta "todo en uno" que transforma la forma en que instalas software en Linux. Arrastra, suelta y disfruta.

[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](#)
[![Linux](https://img.shields.io/badge/Platform-Linux-blue?logo=linux)](#)
[![Easy](https://img.shields.io/badge/User--Experience-Very--Easy-brightgreen)](#)

---

## 🧐 ¿Por qué SuperInstall?

Instalar programas en Linux suele ser un caos: que si un `.deb`, que si un `Flatpak`, que si falta soporte para `Snap`... **SuperInstall unifica todo eso en una sola ventana elegante.**

### 🔥 Lo que lo hace único:

* **🛠️ Instalador Universal:** Olvida los formatos. Soporta `.deb`, `.AppImage`, `.flatpak` y `.snap` bajo el mismo techo.
* **🩺 Modo Médico (Auto-Diagnóstico):** ¿Tu sistema no tiene soporte para Flatpak o Snap? SuperInstall lo detecta y te ofrece activarlo con un clic. Él se encarga de la configuración pesada por ti.
* **🚫 Adiós a los Errores de Arquitectura:** ¿Alguna vez has bajado algo que no era para tu procesador? SuperInstall comprueba si el archivo es compatible con tu CPU (x64, ARM, etc.) antes de intentar instalarlo. **Cero frustración.**
* **📈 Barra de Progreso Honesta:** Nada de cargas infinitas. Lee el progreso real de la terminal para que sepas exactamente cuánto falta.
* **🌍 Habla tu Idioma:** Totalmente traducido al Español, Inglés, Italiano, Francés, Alemán, Portugués y Ruso.

---

## 🖥️ Una interfaz diseñada para humanos

Inspirado en la estética limpia de Zorin OS y Ubuntu, SuperInstall ofrece una experiencia visual de alto nivel:

1. **Pestaña de Instalación:** Un área de Drop-Zone intuitiva para tus archivos.
2. **Gestor de Apps:** Busca y desinstala cualquier programa (del sistema, Snap o Flatpak) desde una lista unificada y limpia. No más aplicaciones perdidas.



---

## ⚡ Instalación Rápida

### Para Usuarios (Binario)
*Próximamente: Descarga el .deb de lanzamiento desde la pestaña de Releases.*

### Para Desarrolladores (Código Fuente)
```bash
# 1. Clona
git clone [https://github.com/gonzaroman/superinstall.git](https://github.com/gonzaroman/superinstall.git) && cd superinstall

# 2. Prepara el entorno
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. ¡Lánzalo!
python3 main.py