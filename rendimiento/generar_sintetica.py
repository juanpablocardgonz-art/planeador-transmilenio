# =============================================================================
# rendimiento/generar_sintetica.py
# -----------------------------------------------------------------------------
# Genera redes SINTÉTICAS del tamaño que usa el profesor para medir
# (10.000, 20.000, 40.000 y 80.000 estaciones), con el mismo formato de los
# tres CSV. La red real solo tiene 147 estaciones: copiarla 545 veces no se
# parece a una red grande de verdad, así que la construimos así:
#
#   - n estaciones con nombres tipo "ESTACION 00042 NORTE" (ordenados al
#     azar dentro del CSV, como podría venir la red del profesor).
#   - Cada ruta tiene entre 8 y 30 paradas elegidas al azar, y cada ruta
#     "ida" tiene su ruta "vuelta" con las mismas paradas al revés
#     (cada ruta va en un solo sentido).
#   - Cada estación queda en ~4 rutas, como en la red real (promedio 13
#     paradas/ruta y 1.927 paradas en 147 estaciones).
#   - Cada ruta tiene 'viajes' buses al día; por cada bus se escribe la hora
#     a la que pasa por cada parada (2 minutos entre paradas).
#
# Con la semilla fija, la misma n siempre genera la misma red.
#
# Uso:  python -m rendimiento.generar_sintetica 10000 /ruta/salida
# =============================================================================

import csv
import os
import random
import sys

SECTORES = ("NORTE", "SUR", "CENTRO", "OCCIDENTE", "ORIENTE", "AV.", "CALLE", "PORTAL")


def generar(n, carpeta, viajes=8, semilla=2026):
    """Escribe en 'carpeta' una red de n estaciones. Devuelve (n, rutas, horarios)."""
    os.makedirs(carpeta, exist_ok=True)
    gen = random.Random(semilla)

    # 1. Estaciones (nombres únicos; se escriben en orden aleatorio).
    nombres = [f"{SECTORES[i % len(SECTORES)]} {i:06d}" for i in range(n)]
    gen.shuffle(nombres)

    # 2. Rutas: cada estación debe aparecer en ~4 rutas en total
    #    (2 parejas ida/vuelta). Repartimos un "mazo" con cada estación 2 veces.
    mazo = nombres + nombres
    gen.shuffle(mazo)
    rutas = []
    i = 0
    numero = 0
    while i < len(mazo):
        largo = gen.randint(8, 30)
        paradas = []
        vistos = set()
        while i < len(mazo) and len(paradas) < largo:
            if mazo[i] not in vistos:          # sin estaciones repetidas en una ruta
                paradas.append(mazo[i])
                vistos.add(mazo[i])
            i += 1
        if len(paradas) >= 2:
            numero += 1
            rutas.append((f"R{numero}-1", paradas))
            rutas.append((f"R{numero}-2", paradas[::-1]))

    # 3. Escribir los CSV.
    with open(os.path.join(carpeta, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre"])
        w.writerows([x] for x in nombres)
    total_horarios = 0
    with open(os.path.join(carpeta, "rutas.csv"), "w", newline="", encoding="utf-8") as fr, \
         open(os.path.join(carpeta, "horarios.csv"), "w", newline="", encoding="utf-8") as fh:
        wr, wh = csv.writer(fr), csv.writer(fh)
        wr.writerow(["ruta", "orden", "estacion"])
        wh.writerow(["ruta", "estacion", "hora"])
        for nombre, paradas in rutas:
            for orden, est in enumerate(paradas, start=1):
                wr.writerow([nombre, orden, est])
            # Buses entre las 4:30 y las 22:00, con salidas al azar.
            salidas = sorted(gen.randint(270, 1320) for _ in range(viajes))
            for salida in salidas:
                for k, est in enumerate(paradas):
                    m = min(salida + 2 * k, 23 * 60 + 59)
                    wh.writerow([nombre, est, f"{m // 60:02d}:{m % 60:02d}"])
                    total_horarios += 1
    return n, len(rutas), total_horarios


if __name__ == "__main__":
    n = int(sys.argv[1])
    print(generar(n, sys.argv[2]))
