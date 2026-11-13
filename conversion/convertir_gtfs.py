# =============================================================================
# conversion/convertir_gtfs.py
# -----------------------------------------------------------------------------
# Convierte el GTFS de TransMilenio (zip de ~54 MB, julio 2021) en los tres
# CSV que lee el motor:
#
#   estaciones.csv   nombre
#   rutas.csv        ruta, orden, estacion
#   horarios.csv     ruta, estacion, hora
#
# Uso:
#     python conversion/convertir_gtfs.py ruta/al/gtfs.zip datos/
#
# Este script está FUERA de motor/, así que podría usar cualquier librería
# (pandas, etc.). Usamos solo la librería estándar para que no haya que
# instalar nada.
#
# ARCHIVOS DEL GTFS QUE USAMOS (es un estándar):
#   stops.txt       stop_id, stop_name, parent_station   -> paradas y estaciones
#   routes.txt      route_id, route_short_name           -> nombre de la ruta
#   trips.txt       trip_id, route_id, direction_id      -> cada viaje de un bus
#   stop_times.txt  trip_id, stop_id, stop_sequence,
#                   departure_time                       -> a qué hora pasa
#
# DECISIONES (van también en el README):
#   1. NOMBRES: mayúsculas, sin tildes, espacios normalizados. Si una parada
#      tiene 'parent_station' (un vagón dentro de una estación), usamos el
#      nombre de la estación padre: así cada estación aparece una sola vez.
#   2. RUTAS: "cada ruta va en un solo sentido". Agrupamos los viajes por
#      (route_short_name, secuencia exacta de estaciones). Cada secuencia
#      distinta es una ruta: "B11-1", "B11-2", ... (numeradas por orden de
#      aparición en el GTFS).
#   3. HORAS >= 24: el GTFS escribe "25:10" para la 1:10 a.m. del día
#      siguiente (el servicio que empezó el día anterior). Las pasamos a
#      módulo 24 ("01:10") porque el enunciado exige HH:MM válido. Efecto:
#      esos buses aparecen al inicio del día en próximo_bus.
#   4. Paradas repetidas seguidas en un viaje (dos vagones de la misma
#      estación) se cuentan una sola vez.
#   5. Horarios repetidos (misma ruta, estación y hora) se escriben una vez.
#
# ⚠️  Probado con un GTFS pequeño de ejemplo (pruebas/test_conversion.py).
#     Hay que correrlo con el zip real y comparar contra los CSV de datos/.
# =============================================================================

import csv
import io
import os
import sys
import unicodedata
import zipfile


def normalizar(nombre):
    """'Calle 26 ' -> 'CALLE 26';  'Héroes' -> 'HEROES'."""
    # NFD separa cada letra de su tilde ("é" -> "e" + "´"); luego quitamos
    # los caracteres de tipo "marca" (Mn), que son las tildes.
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", nombre)
                         if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.upper().split())


def hora_valida(texto):
    """'25:10:00' -> '01:10'. Devuelve None si el texto no es una hora."""
    partes = texto.strip().split(":")
    if len(partes) < 2 or not partes[0].isdigit() or not partes[1].isdigit():
        return None
    horas, minutos = int(partes[0]) % 24, int(partes[1])
    return f"{horas:02d}:{minutos:02d}"


def leer(zip_gtfs, archivo):
    """Itera las filas (como dict) de un archivo .txt dentro del zip."""
    with zip_gtfs.open(archivo) as crudo:
        yield from csv.DictReader(io.TextIOWrapper(crudo, encoding="utf-8-sig"))


def convertir(ruta_zip, carpeta_salida):
    os.makedirs(carpeta_salida, exist_ok=True)
    with zipfile.ZipFile(ruta_zip) as z:
        # --- 1. Paradas -> nombre de estación --------------------------------
        filas_paradas = list(leer(z, "stops.txt"))
        nombre_de = {f["stop_id"]: normalizar(f["stop_name"]) for f in filas_paradas}
        estacion_de = {}
        for f in filas_paradas:
            padre = (f.get("parent_station") or "").strip()
            estacion_de[f["stop_id"]] = nombre_de.get(padre, nombre_de[f["stop_id"]]) if padre else nombre_de[f["stop_id"]]

        # --- 2. Viajes -> nombre corto de su ruta --------------------------------
        corto = {f["route_id"]: (f.get("route_short_name") or f["route_id"]).strip()
                 for f in leer(z, "routes.txt")}
        ruta_del_viaje = {f["trip_id"]: corto.get(f["route_id"], f["route_id"])
                          for f in leer(z, "trips.txt")}

        # --- 3. Horarios de cada viaje (secuencia, estación, hora) -----------------
        paradas_del_viaje = {}
        for f in leer(z, "stop_times.txt"):
            hora = hora_valida(f.get("departure_time") or f.get("arrival_time") or "")
            estacion = estacion_de.get(f["stop_id"])
            if hora is None or estacion is None:
                continue
            paradas_del_viaje.setdefault(f["trip_id"], []).append(
                (int(f["stop_sequence"]), estacion, hora))

    # --- 4. Agrupar viajes en rutas de un solo sentido -----------------------------
    variante_de = {}          # (nombre_corto, secuencia) -> "B11-1"
    contador = {}             # nombre_corto -> cuántas variantes lleva
    horarios = set()          # (ruta, estacion, hora), set = sin repetidos
    for viaje, paradas in paradas_del_viaje.items():
        paradas.sort()
        secuencia, horas = [], []
        for _, estacion, hora in paradas:
            if not secuencia or secuencia[-1] != estacion:   # decisión 4
                secuencia.append(estacion)
                horas.append(hora)
        if len(secuencia) < 2:
            continue
        corto_ruta = ruta_del_viaje.get(viaje, "SIN-RUTA")
        clave = (corto_ruta, tuple(secuencia))
        if clave not in variante_de:
            contador[corto_ruta] = contador.get(corto_ruta, 0) + 1
            variante_de[clave] = f"{corto_ruta}-{contador[corto_ruta]}"
        ruta = variante_de[clave]
        for estacion, hora in zip(secuencia, horas):
            horarios.add((ruta, estacion, hora))

    # --- 5. Escribir los tres CSV ------------------------------------------------------
    estaciones = sorted({e for (_, sec) in variante_de for e in sec})
    with open(os.path.join(carpeta_salida, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre"])
        w.writerows([e] for e in estaciones)
    with open(os.path.join(carpeta_salida, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "orden", "estacion"])
        for (_, secuencia), ruta in sorted(variante_de.items(), key=lambda x: x[1]):
            for orden, estacion in enumerate(secuencia, start=1):
                w.writerow([ruta, orden, estacion])
    with open(os.path.join(carpeta_salida, "horarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "estacion", "hora"])
        w.writerows(sorted(horarios))
    return len(estaciones), len(variante_de), len(horarios)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python conversion/convertir_gtfs.py gtfs.zip carpeta_salida")
        sys.exit(1)
    e, r, h = convertir(sys.argv[1], sys.argv[2])
    print(f"Listo: {e} estaciones, {r} rutas, {h} horarios -> {sys.argv[2]}")
