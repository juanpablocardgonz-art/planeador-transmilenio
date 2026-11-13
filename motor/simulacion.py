# =============================================================================
# motor/simulacion.py
# -----------------------------------------------------------------------------
# R10: simulación de la FILA DE ABORDAJE en hora pico con una COLA (FIFO).
#
# Modelo (decisión del grupo, ver README):
#   - llegadas:   lista de números; llegadas[i] = minuto en que llega el
#                 pasajero i a la estación.
#   - frecuencia: cada cuántos minutos sale un bus. Salen en los minutos
#                 0, f, 2f, 3f, ... (múltiplos de la frecuencia).
#   - capacidad:  cuántos pasajeros caben en cada bus.
#   - Un pasajero que llega justo en el minuto de salida alcanza ese bus.
#   - Suben en ORDEN DE LLEGADA (FIFO). Si dos llegan al mismo minuto, sube
#     primero el que aparece antes en la lista.
#
# Devuelve: una lista 'salidas' del mismo tamaño que 'llegadas', donde
#   salidas[i] = minuto en que sale el bus en el que se subió el pasajero i.
#   (La espera del pasajero i es salidas[i] - llegadas[i].)
#
# ALGORITMO (simulación por eventos):
#   Para cada bus (en orden de salida):
#     1. Pasan a la cola todos los pasajeros que ya llegaron (llegada <= hora).
#     2. Suben hasta 'capacidad' pasajeros, sacándolos del frente de la cola.
#   Si la cola queda vacía, saltamos directamente al primer bus que sale
#   después de que llegue el siguiente pasajero (no simulamos buses vacíos).
#
# COMPLEJIDAD: O(P + B), con P = pasajeros y B = buses que salen con gente.
#   Cada pasajero se encola una vez y se desencola una vez, O(1) cada vez.
#   Si 'llegadas' no viene ordenada, primero la ordenamos: O(P log P).
#
# ALTERNATIVA DESCARTADA: lista de Python con pop(0) -> O(P) por cada salida,
# O(P^2) en total. Con 300.000 pasajeros son ~4.5 * 10^10 movimientos.
# =============================================================================

from .pila_cola import Cola
from .ordenamiento import esta_ordenada, merge_sort


def simular_fila(llegadas, frecuencia, capacidad):
    # --- 1. Validaciones ----------------------------------------------------
    if frecuencia <= 0:
        raise ValueError("La frecuencia debe ser mayor que 0")
    if capacidad <= 0:
        raise ValueError("La capacidad debe ser mayor que 0")

    total = len(llegadas)
    salidas = [None] * total  # respuesta, se llena por posición del pasajero

    # --- 2. Orden de llegada -------------------------------------------------
    # 'orden' es la lista de índices de pasajeros, ordenada por hora de
    # llegada. Si ya viene ordenada (lo normal), es simplemente 0, 1, 2, ...
    indices = list(range(total))
    if esta_ordenada(llegadas):
        orden = indices
    else:
        # Merge Sort es ESTABLE: si dos llegan al mismo minuto, se respeta
        # el orden original de la lista.
        orden = merge_sort(indices, lambda i: llegadas[i])

    # --- 3. Simulación ----------------------------------------------------------
    cola = Cola()
    siguiente = 0      # posición en 'orden' del próximo pasajero por llegar
    atendidos = 0      # cuántos ya se subieron a un bus
    hora_bus = None    # minuto de salida del bus actual

    while atendidos < total:
        # 3a. Si nadie espera, saltamos al primer bus que alcanza el
        #     próximo pasajero: el menor múltiplo de 'frecuencia' >= su llegada.
        if cola.vacia():
            llegada = llegadas[orden[siguiente]]
            multiplo = llegada // frecuencia
            candidato = multiplo * frecuencia
            if candidato < llegada:
                candidato = candidato + frecuencia
            if hora_bus is None or candidato > hora_bus:
                hora_bus = candidato

        # 3b. Todos los que ya llegaron entran a la fila (al final de la cola).
        while siguiente < total and llegadas[orden[siguiente]] <= hora_bus:
            cola.encolar(orden[siguiente])
            siguiente += 1

        # 3c. Sube gente desde el frente de la cola hasta llenar el bus.
        subieron = 0
        while subieron < capacidad and not cola.vacia():
            pasajero = cola.desencolar()
            salidas[pasajero] = hora_bus
            subieron += 1
            atendidos += 1

        # 3d. El siguiente bus sale 'frecuencia' minutos después.
        hora_bus = hora_bus + frecuencia

    return salidas
