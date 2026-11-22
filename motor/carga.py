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
    Recorre un CSV fila por fila y ENTREGA (yield) cada fila como una lista
    con los valores de 'columnas' en ese orden (ya sin espacios sobrantes).
    Las filas vacías o incompletas se ignoran.

    ¿Por qué un GENERADOR (yield) y no devolver una lista con todas las filas?
    Con la red de 80.000 estaciones, horarios.csv tiene ~2.5 millones de
    filas. Guardarlas todas en una lista ocupaba casi 1 GB de memoria y hacía
    la carga más lenta de lo lineal (el recolector de basura de Python revisa
    más objetos cuanto más memoria hay). Con yield solo existe UNA fila a la
    vez en memoria: la carga queda O(filas) en tiempo y O(1) extra en memoria.
    """
    with _abrir(ruta_archivo) as archivo:
        lector = csv.reader(archivo)
        encabezado = next(lector, None)
        if encabezado is None:
            return  # archivo vacío: el generador no entrega nada
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
                yield valores
