# =============================================================================
# motor/lista_doble.py
# -----------------------------------------------------------------------------
# LISTA DOBLEMENTE ENLAZADA para el recorrido de cada ruta (R7).
#
#   None <- [UNIVERSIDADES] <-> [RECINTO FERIAL] <-> [EL TIEMPO] -> None
#              cabeza                                    cola
#
# Cada nodo es una PARADA de una ruta y guarda:
#   - estacion:  el objeto Estacion donde para.
#   - horas:     arreglo ORDENADO de minutos en que el bus pasa por ahí (R4).
#   - anterior / siguiente: enlaces a las paradas vecinas.
#
# ¿Por qué DOBLE enlace?
#   - R7 pide ver el recorrido "en los dos sentidos": con el enlace 'anterior'
#     recorremos al revés en O(L) sin copiar ni invertir nada.
#   - Para quitar un nodo necesitamos tocar a su anterior; con enlace doble
#     lo tenemos en O(1).
#
# ¿Cómo encontramos el nodo de una estación en O(1)?
#   Cada Ruta tiene además una TablaHash nombre_estacion -> nodo (ver red.py).
#   Lista enlazada + tabla hash = insertar/quitar parada en O(1).
#
# TRUCO para deshacer/rehacer (R9):
#   Al desenlazar un nodo NO borramos sus punteros anterior/siguiente. Como
#   deshacer y rehacer van en orden estricto de pila, cuando lo volvemos a
#   enlazar sus vecinos son exactamente los mismos de antes: reenlazarlo es O(1).
#
# ALTERNATIVA DESCARTADA: guardar la ruta en un arreglo (list). Recorrer es
# igual, pero insertar o quitar en medio cuesta O(L) por el desplazamiento.
# =============================================================================


class NodoParada:
    __slots__ = ("estacion", "horas", "anterior", "siguiente")

    def __init__(self, estacion, horas, anterior=None, siguiente=None):
        self.estacion = estacion
        self.horas = horas
        self.anterior = anterior
        self.siguiente = siguiente


class ListaDoble:
    def __init__(self):
        self.cabeza = None  # primera parada
        self.cola = None    # última parada
        self.tamano = 0

    def agregar_al_final(self, nodo):
        """Agrega un nodo al final. O(1). Se usa al cargar los CSV."""
        nodo.anterior = self.cola
        nodo.siguiente = None
        self.enlazar(nodo)

    def enlazar(self, nodo):
        """
        Inserta 'nodo' entre nodo.anterior y nodo.siguiente, que deben venir
        ya puestos. O(1). Sirve para:
          - insertar una parada nueva (ponemos sus vecinos y llamamos aquí),
          - deshacer un 'quitar' o rehacer un 'agregar' (los vecinos quedaron
            guardados en el nodo).
        """
        # Enlace hacia atrás: si no hay anterior, el nodo es la nueva cabeza.
        if nodo.anterior is None:
            self.cabeza = nodo
        else:
            nodo.anterior.siguiente = nodo
        # Enlace hacia adelante: si no hay siguiente, el nodo es la nueva cola.
        if nodo.siguiente is None:
            self.cola = nodo
        else:
            nodo.siguiente.anterior = nodo
        self.tamano += 1

    def desenlazar(self, nodo):
        """
        Saca 'nodo' de la lista en O(1): sus vecinos se apuntan entre sí.
        OJO: no limpiamos nodo.anterior / nodo.siguiente (ver TRUCO arriba).
        """
        if nodo.anterior is None:
            self.cabeza = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente
        if nodo.siguiente is None:
            self.cola = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior
        self.tamano -= 1

    def recorrer(self, al_reves=False):
        """Lista de nodos de inicio a fin (o de fin a inicio). O(L)."""
        resultado = []
        if al_reves:
            nodo = self.cola
            while nodo is not None:
                resultado.append(nodo)
                nodo = nodo.anterior
        else:
            nodo = self.cabeza
            while nodo is not None:
                resultado.append(nodo)
                nodo = nodo.siguiente
        return resultado
