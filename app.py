# =============================================================================
# app.py  —  COMANDO ÚNICO para arrancar la aplicación:
#
#     python app.py                 (abre en http://localhost:8000)
#     python app.py --puerto 8080   (otro puerto)
#     python app.py --datos otra/carpeta
#
# No requiere instalar nada: usa solo la librería estándar de Python 3.9+.
# =============================================================================

import argparse
import os
import webbrowser
import threading

from frontend.servidor import iniciar

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Planeador TransMilenio")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--datos", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos"))
    parser.add_argument("--sin-navegador", action="store_true", help="no abrir el navegador")
    args = parser.parse_args()
    if not args.sin_navegador:
        # Abrimos el navegador un segundo después, cuando el servidor ya esté.
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{args.puerto}")).start()
    iniciar(args.puerto, args.datos)
