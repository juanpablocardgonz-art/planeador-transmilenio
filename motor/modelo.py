# =============================================================================
# motor/modelo.py
# -----------------------------------------------------------------------------
# Las dos "entidades" de la red: Estacion y Ruta.
#
# Cómo se conectan (esto ES el grafo de la red):
#
#   Estacion "RICAURTE"                      Ruta "B11-1"
#     .rutas: TablaHash  --------------->      .paradas: ListaDoble
#         "B11-1" -> Ruta                          [..] <-> [RICAURTE] <-> [..]
#         "F23-2" -> Ruta                      .indice: TablaHash
#                                                  "RICAURTE" -> NodoParada
#
#   - Una Estacion sabe por qué rutas pasa (para planear viajes, R5).
#   - Una Ruta sabe su recorrido (lista enlazada) y encuentra cualquier
#     parada en O(1) con su índice hash.
#
# Visto como GRAFO: las estaciones son vértices y cada par de paradas
# consecutivas de una ruta es una arista dirigida (cada ruta va en un solo
# sentido). Es una representación con LISTAS DE ADYACENCIA: el vecino
# siguiente de cada parada es nodo.siguiente. Descartamos la matriz de
# adyacencia porque ocupa O(n^2) y la red es muy dispersa (cada estación
# tiene pocos vecinos).
# =============================================================================

from .tabla_hash import TablaHash
from .lista_doble import ListaDoble


class Estacion:
    __slots__ = ("nombre", "id", "abierta", "buses", "rutas")

    def __init__(self, nombre, identificador):
        self.nombre = nombre
        # id: número 0..n-1. Nos deja usar arreglos indexados por estación
        # (ver planificador.py) en vez de tablas hash, que es más rápido.
        self.id = identificador
        self.abierta = True
        # buses: cuántas veces al día pasa un bus por aquí (sumando todas las
        # rutas). Es la medida del ranking (R6).
        self.buses = 0
        # rutas: nombre_ruta -> Ruta, todas las rutas que paran aquí.
        self.rutas = TablaHash(4)


class Ruta:
    __slots__ = ("nombre", "paradas", "indice")

    def __init__(self, nombre):
        self.nombre = nombre
        self.paradas = ListaDoble()     # recorrido en orden
        self.indice = TablaHash(8)      # nombre_estacion -> NodoParada
