# =============================================================================
# motor/planificador.py
# -----------------------------------------------------------------------------
# R5: PLANEAR UN VIAJE directo o con UN SOLO transbordo, por menos paradas.
#
# ¿Por qué no un BFS normal sobre estaciones?
#   BFS encuentra el camino con menos paradas, pero puede usar 5 buses
#   distintos. Aquí el límite es "como mucho 2 buses", y en un bus se viaja
#   de una estación a cualquier otra MÁS ADELANTE en su recorrido.
#   Por eso pensamos el problema como un grafo de dos niveles (rutas y
#   estaciones) y lo resolvemos con dos barridos. Equivale a un BFS de
#   profundidad 2 sobre el grafo "estación -> ruta -> estación".
#
# IDEA (encuentro en el medio):
#
#   origen ==(ruta A)==> T ==(ruta B)==> destino
#
#   Barrido 1 (hacia atrás desde el destino):
#     Para cada ruta B que para en el destino, caminamos su lista enlazada
#     HACIA ATRÁS desde el destino. Cada estación T que encontramos podría
#     ser el transbordo: anotamos  dist[T] = paradas de T al destino por B
#     (nos quedamos con la menor si varias rutas llegan).
#
#   Barrido 2 (hacia adelante desde el origen):
#     Para cada ruta A que para en el origen, caminamos HACIA ADELANTE.
#       - Si encontramos el destino: es un viaje DIRECTO con j paradas.
#       - Si encontramos una T anotada en el barrido 1: viaje con transbordo
#         de j + dist[T] paradas.
#     Nos quedamos con el mejor.
#
# TRUCO DE LAS MARCAS (para no reiniciar arreglos):
#   dist es un arreglo de tamaño n indexado por estacion.id. Reiniciarlo en
#   cada consulta costaría O(n). En vez de eso guardamos marca[id] = número
#   de la consulta que lo escribió. Si marca[id] != consulta actual, el valor
#   es "basura vieja" y lo tratamos como vacío. Reinicio en O(1).
#
# REGLAS de estaciones cerradas (R8): nadie sube, baja ni transborda en una
#   estación cerrada. El bus sí puede pasar por ella (cuenta como parada del
#   recorrido, porque el bus sigue pasando por ahí).
#
# DESEMPATES: menos paradas; si empatan, preferimos el directo (menos
#   transbordos); si sigue el empate, el primero en orden alfabético de rutas.
#
# COMPLEJIDAD: O(L_origen + L_destino), donde L_x = suma de las longitudes de
#   las rutas que pasan por x. No depende del número total de estaciones.
#
# ALTERNATIVAS DESCARTADAS:
#   - Probar todas las parejas de rutas (A, B): O(R^2 * L). Mucho más lento.
#   - Dijkstra / BFS sobre todo el grafo: no respeta el límite de 1 transbordo
#     sin modificar los estados, y recorrería toda la red.
# =============================================================================


class Planificador:
    def __init__(self, total_estaciones):
        # Arreglos paralelos indexados por estacion.id.
        self._marca = [0] * total_estaciones   # en qué consulta se escribió
        self._dist = [0] * total_estaciones    # paradas de T al destino
        self._ruta = [None] * total_estaciones # ruta B para ir de T al destino
        self._consulta = 0                     # contador de consultas

    def viaje(self, origen, destino):
        """
        origen, destino: objetos Estacion (ya validados como existentes).
        Devuelve (total_paradas, tramos) o None si no hay viaje posible.
        Cada tramo es una tupla (ruta, estacion_donde_sube, estacion_donde_baja).
        """
        # --- Casos borde -----------------------------------------------------
        if not origen.abierta or not destino.abierta:
            return None  # no se puede subir o bajar en una estación cerrada
        if origen is destino:
            return (0, [])  # ya está allí: cero paradas, ningún bus

        # Nueva consulta: invalida todas las marcas anteriores en O(1).
        self._consulta += 1
        actual = self._consulta

        # --- Barrido 1: desde el destino hacia atrás --------------------------
        for ruta_b in destino.rutas.valores():
            nodo_destino = ruta_b.indice.buscar(destino.nombre)
            paradas = 0
            nodo = nodo_destino.anterior
            while nodo is not None:
                paradas += 1
                t = nodo.estacion
                # Solo se puede transbordar en estaciones abiertas.
                if t.abierta:
                    if self._marca[t.id] != actual or _mejor(
                            paradas, ruta_b.nombre,
                            self._dist[t.id], self._ruta[t.id].nombre):
                        self._marca[t.id] = actual
                        self._dist[t.id] = paradas
                        self._ruta[t.id] = ruta_b
                nodo = nodo.anterior

        # --- Barrido 2: desde el origen hacia adelante -------------------------
        mejor = None  # (paradas, transbordos, texto_desempate, tramos)
        for ruta_a in origen.rutas.valores():
            nodo_origen = ruta_a.indice.buscar(origen.nombre)
            paradas = 0
            nodo = nodo_origen.siguiente
            while nodo is not None:
                paradas += 1
                t = nodo.estacion
                if t is destino:
                    # VIAJE DIRECTO
                    candidato = (paradas, 0, ruta_a.nombre,
                                 [(ruta_a.nombre, origen.nombre, destino.nombre)])
                    if _es_mejor(candidato, mejor):
                        mejor = candidato
                    break  # más adelante en esta ruta solo empeora
                if t.abierta and self._marca[t.id] == actual:
                    ruta_b = self._ruta[t.id]
                    # Si A y B son la misma ruta, en realidad es un directo
                    # (y lo encontraremos al seguir caminando).
                    if ruta_b is not ruta_a:
                        candidato = (paradas + self._dist[t.id], 1,
                                     ruta_a.nombre + "|" + ruta_b.nombre,
                                     [(ruta_a.nombre, origen.nombre, t.nombre),
                                      (ruta_b.nombre, t.nombre, destino.nombre)])
                        if _es_mejor(candidato, mejor):
                            mejor = candidato
                nodo = nodo.siguiente

        if mejor is None:
            return None
        return (mejor[0], mejor[3])


def _mejor(paradas, nombre_ruta, paradas_actual, nombre_actual):
    """¿(paradas, nombre_ruta) es mejor que lo anotado? Menos paradas gana."""
    if paradas != paradas_actual:
        return paradas < paradas_actual
    return nombre_ruta < nombre_actual


def _es_mejor(candidato, mejor):
    """Compara (paradas, transbordos, desempate) sin usar min()."""
    if mejor is None:
        return True
    for i in range(3):
        if candidato[i] != mejor[i]:
            return candidato[i] < mejor[i]
    return False
