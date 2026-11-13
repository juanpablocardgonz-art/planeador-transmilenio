# =============================================================================
# rendimiento/medir.py
# -----------------------------------------------------------------------------
# R11: mide cada operación del motor con redes de tamaño n, 2n, 4n, 8n y
# compara el crecimiento MEDIDO con la complejidad ESPERADA.
#
# MÉTODO (el del Taller 1: duplicar n y mirar qué pasa):
#   Si una operación es...      al duplicar n, el tiempo debería...
#     O(1)                       quedarse igual        (razón ~ 1.0)
#     O(log n)                   crecer muy poquito    (razón ~ log(2n)/log(n))
#     O(n)                       duplicarse            (razón ~ 2.0)
#     O(n log n)                 algo más que duplicarse
#
# Para que la medición sea confiable:
#   - Repetimos cada operación muchas veces con entradas aleatorias (pero con
#     semilla fija, para que el experimento sea reproducible) y promediamos.
#   - Usamos time.perf_counter(), el reloj de mayor resolución.
#   - Las operaciones que modifican la red se deshacen después (sin medir eso)
#     para que todas las mediciones arranquen de la misma red.
#
# Uso por consola (guarda rendimiento/resultados.json, que lee la app):
#     python -m rendimiento.medir
# =============================================================================

import json
import math
import os
import random
import shutil
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from motor import Red, simular_fila  # noqa: E402
from rendimiento.generar_red import generar_red  # noqa: E402

DATOS = os.path.join(RAIZ, "datos")
RESULTADOS = os.path.join(RAIZ, "rendimiento", "resultados.json")

# Funciones de crecimiento: f(n). La razón esperada al duplicar es f(2n)/f(n).
CRECIMIENTOS = {
    "O(1)": lambda n: 1.0,
    "O(log n)": lambda n: math.log2(n),
    "O(n)": lambda n: float(n),
    "O(n log n)": lambda n: n * math.log2(n),
}

# Descripción de cada operación medida: requisito, complejidad esperada,
# qué es n y una explicación por si la medición no coincide.
OPERACIONES = [
    ("carga", "Carga", "O(n)", "n = filas de los CSV",
     "Lee cada fila una vez; Merge Sort solo ordena las horas de un mismo par (ruta, estación), cuyo tamaño no crece con la red."),
    ("estado", "R1", "O(1)", "n = estaciones",
     "Tabla hash propia. Puede subir un poco por efectos de caché de memoria al crecer la tabla."),
    ("autocompletar", "R2", "O(log n)", "n = estaciones abiertas (k = 10)",
     "AVL: bajar O(log n) + recorrer k. La parte k es constante."),
    ("rango", "R3", "O(log n)", "n = estaciones abiertas (rango de 1 resultado)",
     "AVL: O(log n + r). Medimos con r = 1 para aislar el log n."),
    ("proximo_bus", "R4", "O(1)", "n = estaciones (h = horas por parada, fijo)",
     "Hash O(1) + búsqueda binaria O(log h). h no cambia al duplicar la red."),
    ("viaje", "R5", "O(1)", "L = largo de rutas del origen y destino (fijo)",
     "R5 está excluido de la prueba de rendimiento. Depende del largo de las rutas, no de n."),
    ("ranking", "R6", "O(log n)", "n = estaciones abiertas (k = 10)",
     "AVL con clave (-buses, nombre): O(log n + k)."),
    ("agregar_parada", "R7", "O(log n)", "n = estaciones",
     "Lista enlazada + hash O(1); actualizar el ranking (AVL) es O(log n)."),
    ("quitar_parada", "R7", "O(log n)", "n = estaciones",
     "Igual que agregar: O(1) en la ruta + O(log n) en el ranking."),
    ("recorrido", "R7", "O(1)", "L = paradas de la ruta (fijo)",
     "Es O(L): recorre la lista enlazada. L no crece al duplicar la red."),
    ("cerrar", "R8", "O(log n)", "n = estaciones",
     "Borra de dos AVL: O(log n)."),
    ("reabrir", "R8", "O(log n)", "n = estaciones",
     "Inserta en dos AVL: O(log n)."),
    ("deshacer", "R9", "O(log n)", "n = estaciones",
     "Pila O(1) + revertir el cambio (aquí, un cierre: O(log n))."),
    ("rehacer", "R9", "O(log n)", "n = estaciones",
     "Pila O(1) + volver a aplicar el cambio."),
    ("simular_fila", "R10", "O(n)", "n = pasajeros",
     "Cada pasajero entra y sale de la cola una sola vez: O(n)."),
]


def _cronometrar(funcion, entradas):
    """Tiempo PROMEDIO (en microsegundos) de llamar funcion(*e) para cada e."""
    inicio = time.perf_counter()
    for e in entradas:
        funcion(*e)
    total = time.perf_counter() - inicio
    return total / len(entradas) * 1e6


def _medir_una_red(carpeta, factor, muestras, aleatorio):
    """Mide todas las operaciones en una red. Devuelve {operacion: µs}."""
    t = {}
    inicio = time.perf_counter()
    red = Red(carpeta)
    t["carga"] = (time.perf_counter() - inicio) * 1e6

    # Elegimos entradas al azar de esta red.
    estaciones = red.rango("", "￿")  # todas las abiertas, en orden
    rutas = red.nombres_rutas()
    est = [aleatorio.choice(estaciones) for _ in range(muestras)]

    t["estado"] = _cronometrar(red.estado, [(e,) for e in est])
    t["autocompletar"] = _cronometrar(red.autocompletar, [(e[:3], 10) for e in est])
    t["rango"] = _cronometrar(red.rango, [(e, e) for e in est])

    # R4: pares (estación, ruta) válidos y una hora al azar.
    pares = []
    for e in est:
        rs = red.rutas_de(e)
        if rs:
            hora = f"{aleatorio.randint(5, 21):02d}:{aleatorio.randint(0, 59):02d}"
            pares.append((e, aleatorio.choice(rs), hora))
    t["proximo_bus"] = _cronometrar(red.proximo_bus, pares)

    # R5: dentro de la misma copia de la red (las copias no se conectan).
    viajes = []
    for e in est[: muestras // 4]:
        copia = e.split(" #")[1] if " #" in e else None
        mismas = [x for x in estaciones if (x.split(" #")[1] if " #" in x else None) == copia]
        viajes.append((e, aleatorio.choice(mismas)))
    t["viaje"] = _cronometrar(red.viaje, viajes)

    t["ranking"] = _cronometrar(red.ranking, [(10,)] * muestras)

    # R7: quitar paradas (y luego deshacer, sin medir), y agregar.
    quitar = []
    usados = set()
    for r in aleatorio.sample(rutas, min(len(rutas), muestras)):
        recorrido = red.recorrido(r)
        if len(recorrido) > 2 and r not in usados:
            usados.add(r)
            quitar.append((r, recorrido[1]))
    t["quitar_parada"] = _cronometrar(red.quitar_parada, quitar)
    for _ in quitar:
        red.deshacer()

    agregar = []
    for r, _ in quitar:
        recorrido = red.recorrido(r)
        nueva = aleatorio.choice(estaciones)
        if nueva not in recorrido:
            agregar.append((r, nueva, recorrido[0]))
    t["agregar_parada"] = _cronometrar(red.agregar_parada, agregar)
    for _ in agregar:
        red.deshacer()

    t["recorrido"] = _cronometrar(red.recorrido, [(r,) for r, _ in quitar])

    # R8 y R9: cerrar estaciones distintas, deshacer, rehacer, reabrir.
    distintas = aleatorio.sample(estaciones, min(len(estaciones), muestras))
    t["cerrar"] = _cronometrar(red.cerrar, [(e,) for e in distintas])
    t["deshacer"] = _cronometrar(red.deshacer, [()] * len(distintas))
    t["rehacer"] = _cronometrar(red.rehacer, [()] * len(distintas))
    t["reabrir"] = _cronometrar(red.reabrir, [(e,) for e in distintas])

    # R10: 30.000 pasajeros por cada factor (n crece igual que la red).
    pasajeros = 30000 * factor
    llegadas = sorted(aleatorio.uniform(0, 120) for _ in range(pasajeros))
    inicio = time.perf_counter()
    simular_fila(llegadas, 5, 160)
    t["simular_fila"] = (time.perf_counter() - inicio) * 1e6

    return t, len(estaciones)


def medir(factores=(1, 2, 4, 8), muestras=2000, semilla=42, progreso=None):
    """
    Ejecuta el experimento completo. Devuelve un diccionario listo para JSON:
      { "factores": [...], "estaciones": [...], "operaciones": [ {...}, ... ] }
    'progreso' es una función opcional que recibe textos de avance.
    """
    aleatorio = random.Random(semilla)
    temporal = tempfile.mkdtemp(prefix="red_tm_")
    tiempos = []
    tamanos = []
    try:
        for factor in factores:
            if progreso:
                progreso(f"Generando y midiendo red x{factor}...")
            carpeta = DATOS if factor == 1 else generar_red(DATOS, factor, os.path.join(temporal, f"x{factor}"))
            t, n = _medir_una_red(carpeta, factor, muestras, aleatorio)
            tiempos.append(t)
            tamanos.append(n)
    finally:
        shutil.rmtree(temporal, ignore_errors=True)

    operaciones = []
    for clave, req, esperado, que_es_n, explicacion in OPERACIONES:
        serie = [t[clave] for t in tiempos]
        f = CRECIMIENTOS[esperado]
        # Razón medida y esperada entre tamaños consecutivos (n -> 2n).
        razones = [serie[i + 1] / serie[i] for i in range(len(serie) - 1)]
        base = tamanos if clave != "simular_fila" else [30000 * x for x in factores]
        esperadas = [f(base[i + 1]) / f(base[i]) for i in range(len(base) - 1)]
        promedio_medido = sum(razones) / len(razones) if razones else 1
        promedio_esperado = sum(esperadas) / len(esperadas) if esperadas else 1
        # Tolerancia: las mediciones en µs tienen ruido (caché, recolector de
        # basura...). Aceptamos hasta un 50% por encima de lo esperado.
        coincide = promedio_medido <= promedio_esperado * 1.5
        operaciones.append({
            "clave": clave, "requisito": req, "esperado": esperado,
            "que_es_n": que_es_n, "explicacion": explicacion,
            "tiempos_us": serie, "razones": razones, "razones_esperadas": esperadas,
            "razon_medida": promedio_medido, "razon_esperada": promedio_esperado,
            "coincide": coincide,
        })
    return {
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "factores": list(factores),
        "estaciones": tamanos,
        "operaciones": operaciones,
    }


def guardar(resultado, ruta=RESULTADOS):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Ejecutado por consola: mide, imprime una tabla y guarda el JSON.
    res = medir(progreso=print)
    guardar(res)
    print(f"\n{'Operación':16} {'Req':5} {'Esperado':10} {'Razón medida':>13} {'Esperada':>9}  ¿Coincide?")
    for op in res["operaciones"]:
        print(f"{op['clave']:16} {op['requisito']:5} {op['esperado']:10} "
              f"{op['razon_medida']:13.2f} {op['razon_esperada']:9.2f}  {'sí' if op['coincide'] else 'NO'}")
    print(f"\nGuardado en {RESULTADOS}")
