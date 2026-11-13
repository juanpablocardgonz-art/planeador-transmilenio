# =============================================================================
# rendimiento/generar_red.py
# -----------------------------------------------------------------------------
# Genera redes MÁS GRANDES a partir de la red real, para medir cómo crece el
# tiempo de cada operación (R11). Es el mismo método del profesor: "duplicar
# la red y medir".
#
# ¿Cómo se agranda? Con 'factor' copias de la red. La copia i (i >= 2) le
# agrega " #i" a cada nombre de estación y de ruta:
#     "RICAURTE" -> "RICAURTE #2", "B11-1" -> "B11-1 #2"
# Así, con factor 2 hay el DOBLE de estaciones, rutas y horarios, pero cada
# ruta individual sigue teniendo el mismo largo (como pasaría si la ciudad
# creciera con más troncales).
#
# Este archivo está FUERA de motor/, así que puede usar cualquier librería.
# =============================================================================

import csv
import os


def _leer(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        lector = csv.reader(f)
        encabezado = next(lector)
        return encabezado, [fila for fila in lector if fila]


def _sufijo(copia):
    # La copia 1 conserva los nombres originales.
    return "" if copia == 1 else f" #{copia}"


def generar_red(carpeta_origen, factor, carpeta_destino):
    """Escribe en carpeta_destino una red 'factor' veces más grande."""
    os.makedirs(carpeta_destino, exist_ok=True)

    # Para cada archivo: qué columnas son nombres de estación o de ruta.
    archivos = {
        "estaciones.csv": {"nombre": "estacion"},
        "rutas.csv": {"ruta": "ruta", "estacion": "estacion"},
        "horarios.csv": {"ruta": "ruta", "estacion": "estacion"},
    }
    for archivo, columnas in archivos.items():
        encabezado, filas = _leer(os.path.join(carpeta_origen, archivo))
        posiciones = [i for i, c in enumerate(encabezado) if c.strip().lower() in columnas]
        with open(os.path.join(carpeta_destino, archivo), "w", encoding="utf-8", newline="") as f:
            escritor = csv.writer(f)
            escritor.writerow(encabezado)
            for copia in range(1, factor + 1):
                sufijo = _sufijo(copia)
                for fila in filas:
                    nueva = list(fila)
                    for p in posiciones:
                        nueva[p] = nueva[p] + sufijo
                    escritor.writerow(nueva)
    return carpeta_destino
