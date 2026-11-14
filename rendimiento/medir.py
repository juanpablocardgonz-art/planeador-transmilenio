# =============================================================================
# rendimiento/medir.py
# -----------------------------------------------------------------------------
# R11: mide cada operación del motor en redes de 10.000, 20.000, 40.000 y
# 80.000 estaciones (los mismos tamaños que usa el profesor) y compara cómo
# crece el tiempo con la complejidad que esperábamos.
#
# MÉTODO (el mismo del script del profesor, que es el del Taller 1):
#   1. Para cada red, cada operación se corre con un lote fijo de consultas
#      aleatorias; el lote se repite varias veces y nos quedamos con la
#      MEDIANA (la mediana ignora repeticiones "raras" en las que el sistema
#      operativo o el recolector de basura interrumpieron).
#   2. Con los cuatro puntos (n, tiempo) calculamos la PENDIENTE de la recta
#      log(tiempo) contra log(n) (regresión lineal por mínimos cuadrados):
#          pendiente 0  -> constante:  O(1) y, en la práctica, O(log n)
#          pendiente 1  -> lineal:     O(n)
#      ¿Por qué log-log? Si t = c * n^p, entonces log t = log c + p * log n:
#      una recta cuya pendiente es justamente el exponente p.
#   3. Comparamos con la pendiente esperada. Para O(log n), entre 10.000 y
#      80.000 la pendiente teórica es ln(log 80000 / log 10000) / ln 8 ≈ 0.10.
#
# Las operaciones que modifican la red se deshacen después (sin medir eso)
# para que cada repetición arranque de la misma red.
#
# Uso por consola (guarda rendimiento/resultados.json, que lee la app):
#     python -m rendimiento.medir            # 10k, 20k, 40k, 80k (~2-3 min)
#     python -m rendimiento.medir --rapido   # 1.250 a 10.000 (~20 s)
# =============================================================================

import json
import math
import os
import random
import shutil
import statistics
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from motor import Red, simular_fila  # noqa: E402
from rendimiento.generar_sintetica import generar  # noqa: E402

RESULTADOS = os.path.join(RAIZ, "rendimiento", "resultados.json")
TAMANOS_PROFESOR = (10000, 20000, 40000, 80000)
TAMANOS_RAPIDOS = (1250, 2500, 5000, 10000)

# Funciones de crecimiento: con ellas calculamos la pendiente ESPERADA.
CRECIMIENTOS = {
    "O(1)": lambda n: 1.0,
    "O(log n)": lambda n: math.log2(n),
    "O(n)": lambda n: float(n),
    "O(n log n)": lambda n: n * math.log2(n),
}

# (clave, requisito, complejidad esperada, qué es n, explicación)
OPERACIONES = [
    ("carga", "Carga", "O(n)", "n = filas de los CSV",
     "Lee cada fila una vez. Merge Sort solo ordena las horas de un mismo par (ruta, estación), que no crece con la red. El profesor solo mide cuánto tarda."),
    ("estado", "R1", "O(1)", "n = estaciones",
     "Tabla hash propia. Puede subir un poco al crecer la tabla por fallos de caché de memoria, no por más comparaciones."),
    ("autocompletar", "R2", "O(log n)", "n = estaciones abiertas (k = 10)",
     "AVL: bajar O(log n) + recorrer k nodos con una pila. k es fijo."),
    ("rango", "R3", "O(log n)", "n = estaciones abiertas (r = 1)",
     "AVL: O(log n + r). Medimos un rango de 1 resultado para aislar el log n; r depende de lo que se pida, no de la red."),
    ("proximo_bus", "R4", "O(log n)", "n = horas de esa ruta en esa estación",
     "Hash O(1) para llegar a la parada + búsqueda binaria O(log h). h no crece con el número de estaciones."),
    ("viaje", "R5", "O(1)", "L = largo de las rutas del origen y destino",
     "R5 está excluido de la medición del profesor. Cuesta O(L_origen + L_destino): no depende del total de estaciones."),
    ("ranking", "R6", "O(log n)", "n = estaciones abiertas (k = 10)",
     "AVL con clave (-buses, nombre): O(log n + k). Se mantiene al día en cada cambio, no se reordena al consultar."),
    ("agregar_parada", "R7", "O(log n)", "n = estaciones",
     "Lista doble + hash O(1) en la ruta; actualizar el ranking (AVL) es O(log n)."),
    ("quitar_parada", "R7", "O(log n)", "n = estaciones",
     "Igual que agregar: O(1) en la ruta + O(log n) en el ranking."),
    ("recorrido", "R7", "O(1)", "L = paradas de la ruta",
     "Es O(L): recorre la lista enlazada. L no crece al crecer la red."),
    ("cerrar", "R8", "O(log n)", "n = estaciones",
     "Hash O(1) + borrar de dos AVL O(log n)."),
    ("reabrir", "R8", "O(log n)", "n = estaciones",
     "Hash O(1) + insertar en dos AVL O(log n)."),
    ("deshacer", "R9", "O(log n)", "n = estaciones",
     "Pila O(1) + revertir el cambio (aquí, un cierre: O(log n))."),
    ("rehacer", "R9", "O(log n)", "n = estaciones",
     "Pila O(1) + volver a aplicar el cambio."),
    ("simular_fila", "R10", "O(n)", "n = pasajeros (= estaciones de la red)",
     "Cada pasajero entra y sale de la cola una sola vez: O(n). Si las llegadas vienen desordenadas se suma Merge Sort, O(n log n)."),
]


def _mediana_us(funcion, entradas, repeticiones):
    """Mediana (entre repeticiones) del tiempo promedio por llamada, en µs."""
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        for e in entradas:
            funcion(*e)
        tiempos.append((time.perf_counter() - inicio) / len(entradas) * 1e6)
    return statistics.median(tiempos)


def _pendiente(ns, ts):
    """Pendiente de la recta de mínimos cuadrados de log(t) contra log(n)."""
    xs = [math.log(n) for n in ns]
    ys = [math.log(t) for t in ts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


def _medir_una_red(carpeta, n, consultas, repeticiones, aleatorio):
    """Mide todas las operaciones en una red de n estaciones. Devuelve {op: µs}."""
    t = {}
    inicio = time.perf_counter()
    red = Red(carpeta)
    t["carga"] = (time.perf_counter() - inicio) * 1e6

    estaciones = red.rango("", "￿")
    rutas = red.nombres_rutas()
    est = [aleatorio.choice(estaciones) for _ in range(consultas)]
    rep = repeticiones

    t["estado"] = _mediana_us(red.estado, [(e,) for e in est], rep)
    t["autocompletar"] = _mediana_us(red.autocompletar, [(e[:-2], 10) for e in est], rep)
    t["rango"] = _mediana_us(red.rango, [(e, e) for e in est], rep)

    pares = []
    for e in est:
        rs = red.rutas_de(e)
        if rs:
            pares.append((e, aleatorio.choice(rs), f"{aleatorio.randint(5, 21):02d}:{aleatorio.randint(0, 59):02d}"))
    t["proximo_bus"] = _mediana_us(red.proximo_bus, pares, rep)
    t["viaje"] = _mediana_us(red.viaje, [(aleatorio.choice(est), aleatorio.choice(est)) for _ in range(consultas // 4)], rep)
    t["ranking"] = _mediana_us(red.ranking, [(10,)] * consultas, rep)

    # R7: rutas distintas; quitar la segunda parada / agregar después de la primera.
    muestra = aleatorio.sample(rutas, min(len(rutas), consultas))
    quitar = [(r, red.recorrido(r)[1]) for r in muestra if len(red.recorrido(r)) > 2]
    agregar = []
    for r, _ in quitar:
        recorrido = red.recorrido(r)
        nueva = aleatorio.choice(estaciones)
        if nueva not in recorrido:
            agregar.append((r, nueva, recorrido[0]))
    t["recorrido"] = _mediana_us(red.recorrido, [(r,) for r, _ in quitar], rep)

    def quitar_y_volver(*_):
        pass

    tiempos_q, tiempos_a = [], []
    for _ in range(rep):
        inicio = time.perf_counter()
        for q in quitar:
            red.quitar_parada(*q)
        tiempos_q.append((time.perf_counter() - inicio) / len(quitar) * 1e6)
        for _ in quitar:
            red.deshacer()
        inicio = time.perf_counter()
        for a in agregar:
            red.agregar_parada(*a)
        tiempos_a.append((time.perf_counter() - inicio) / len(agregar) * 1e6)
        for _ in agregar:
            red.deshacer()
    t["quitar_parada"] = statistics.median(tiempos_q)
    t["agregar_parada"] = statistics.median(tiempos_a)

    # R8 y R9: cerrar estaciones distintas, deshacer, rehacer, reabrir.
    distintas = aleatorio.sample(estaciones, min(len(estaciones), consultas))
    tc, td, tr, ta = [], [], [], []
    for _ in range(rep):
        for lista, accion in ((tc, lambda: [red.cerrar(e) for e in distintas]),
                              (td, lambda: [red.deshacer() for _ in distintas]),
                              (tr, lambda: [red.rehacer() for _ in distintas]),
                              (ta, lambda: [red.reabrir(e) for e in distintas])):
            inicio = time.perf_counter()
            accion()
            lista.append((time.perf_counter() - inicio) / len(distintas) * 1e6)
    t["cerrar"], t["deshacer"] = statistics.median(tc), statistics.median(td)
    t["rehacer"], t["reabrir"] = statistics.median(tr), statistics.median(ta)

    # R10: n pasajeros (crece igual que la red), segundos, bus cada 60 s.
    llegadas = sorted(aleatorio.randint(0, 7200) for _ in range(n))
    tiempos = []
    for _ in range(rep):
        inicio = time.perf_counter()
        simular_fila(llegadas, 60, 200)
        tiempos.append((time.perf_counter() - inicio) * 1e6)
    t["simular_fila"] = statistics.median(tiempos)
    return t


def medir(tamanos=TAMANOS_PROFESOR, consultas=1000, repeticiones=5, semilla=42, progreso=None):
    """Experimento completo. Devuelve un diccionario listo para guardar en JSON."""
    aleatorio = random.Random(semilla)
    temporal = tempfile.mkdtemp(prefix="red_tm_")
    tiempos = []
    try:
        for n in tamanos:
            if progreso:
                progreso(f"Generando red de {n:,} estaciones y midiendo...")
            carpeta = os.path.join(temporal, f"n{n}")
            generar(n, carpeta)
            tiempos.append(_medir_una_red(carpeta, n, consultas, repeticiones, aleatorio))
            shutil.rmtree(carpeta, ignore_errors=True)
    finally:
        shutil.rmtree(temporal, ignore_errors=True)

    operaciones = []
    for clave, req, esperado, que_es_n, explicacion in OPERACIONES:
        serie = [t[clave] for t in tiempos]
        f = CRECIMIENTOS[esperado]
        # Para R4 el "n" real (horas por parada) no cambia con la red: se
        # espera una curva plana igual que O(1).
        ns_esperados = tamanos if clave != "proximo_bus" else [1, 1, 1, 1]
        esperada_serie = [f(x) if f(x) > 0 else 1 for x in ns_esperados]
        pendiente_medida = _pendiente(tamanos, serie)
        pendiente_esperada = _pendiente(tamanos, esperada_serie) if len(set(esperada_serie)) > 1 else 0.0
        # Tolerancia: medir microsegundos tiene ruido. Aceptamos 0.25 por
        # encima de lo esperado (una operación lineal daría ~1.0).
        coincide = pendiente_medida <= pendiente_esperada + 0.25
        operaciones.append({
            "clave": clave, "requisito": req, "esperado": esperado,
            "que_es_n": que_es_n, "explicacion": explicacion,
            "tiempos_us": serie,
            "razones": [serie[i + 1] / serie[i] for i in range(len(serie) - 1)],
            "pendiente_medida": pendiente_medida, "pendiente_esperada": pendiente_esperada,
            "coincide": coincide,
        })
    return {"fecha": time.strftime("%Y-%m-%d %H:%M"), "estaciones": list(tamanos),
            "consultas": consultas, "repeticiones": repeticiones, "operaciones": operaciones}


def guardar(resultado, ruta=RESULTADOS):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    tamanos = TAMANOS_RAPIDOS if "--rapido" in sys.argv else TAMANOS_PROFESOR
    res = medir(tamanos, progreso=print)
    guardar(res)
    print(f"\n{'Operación':16} {'Req':5} {'Esperado':9} " + " ".join(f"{n:>10,}" for n in tamanos)
          + "   pendiente  esperada  ¿coincide?")
    for op in res["operaciones"]:
        ts = " ".join(f"{t:>8.1f}µs" if t < 1e5 else f"{t / 1e6:>9.2f}s" for t in op["tiempos_us"])
        print(f"{op['clave']:16} {op['requisito']:5} {op['esperado']:9} {ts}   "
              f"{op['pendiente_medida']:9.2f} {op['pendiente_esperada']:9.2f}  {'sí' if op['coincide'] else 'NO'}")
    print(f"\nGuardado en {RESULTADOS}")
