# =============================================================================
# motor/carga.py
# -----------------------------------------------------------------------------
# Lectura de los tres CSV del enunciado:
#
#   estaciones.csv   nombre
#   rutas.csv        ruta, orden, estacion
#   horarios.csv     ruta, estacion, hora
#
# Usamos el módulo csv (permitido). OJO: NO usamos csv.DictReader porque
# devuelve un dict por fila y dict está prohibido en motor/. Con csv.reader
# cada fila es una lista, y buscamos en el encabezado en qué columna está
# cada campo (así no importa el orden de las columnas).
#
# Complejidad: O(filas del archivo).
# =============================================================================

import csv


def _abrir(ruta_archivo):
    # encoding "utf-8-sig" ignora el BOM que a veces agrega Excel al inicio.
    # newline="" es lo que recomienda la documentación del módulo csv.
    return open(ruta_archivo, "r", encoding="utf-8-sig", newline="")


def _posicion_columna(encabezado, nombre_columna, ruta_archivo):
    """Busca a mano (sin .index) en qué posición está una columna."""
    for i in range(len(encabezado)):
        if encabezado[i].strip().lower() == nombre_columna:
            return i
    raise ValueError(f"{ruta_archivo}: falta la columna '{nombre_columna}'")


def leer_tabla(ruta_archivo, columnas):
    """
    Lee un CSV y devuelve una lista de filas, donde cada fila es una lista
    con los valores de 'columnas' en ese orden (ya sin espacios sobrantes).
    Las filas vacías o incompletas se ignoran.
    """
    filas = []
    with _abrir(ruta_archivo) as archivo:
        lector = csv.reader(archivo)
        encabezado = next(lector, None)
        if encabezado is None:
            return filas  # archivo vacío
        # 1. Averiguamos la posición de cada columna pedida.
        posiciones = []
        for col in columnas:
            posiciones.append(_posicion_columna(encabezado, col, ruta_archivo))
        # 2. Recorremos las filas tomando solo esas posiciones.
        for fila in lector:
            valores = []
            completa = True
            for p in posiciones:
                if p >= len(fila) or fila[p].strip() == "":
                    completa = False
                    break
                valores.append(fila[p].strip())
            if completa:
                filas.append(valores)
    return filas
