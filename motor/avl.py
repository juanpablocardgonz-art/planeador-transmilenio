# =============================================================================
# motor/avl.py
# -----------------------------------------------------------------------------
# ÁRBOL AVL: árbol binario de búsqueda (BST) AUTO-BALANCEADO.
#
# Lo usamos dos veces en el motor:
#   1. Con los NOMBRES de las estaciones abiertas  -> R2 (autocompletar),
#      R3 (rango) y R8 (al cerrar se borra, al reabrir se inserta).
#   2. Con claves (-buses, nombre) de las estaciones abiertas -> R6 (ranking).
#
# REPASO: árbol binario de búsqueda (BST)
#   Para cada nodo: todo lo de su subárbol izquierdo es MENOR y todo lo de su
#   subárbol derecho es MAYOR. Recorrerlo "en orden" (izquierda, nodo,
#   derecha) entrega las claves ORDENADAS.
#
#                  "CALLE 26"
#                 /          \
#         "AV. JIMENEZ"     "PORTAL SUR"
#           /                  \
#      "AGUAS"               "VIRREY"
#
# PROBLEMA del BST simple: si insertamos claves ya ordenadas (¡y estaciones.csv
# viene ordenado!) el árbol se degenera en una lista y todo pasa a O(n).
#
# SOLUCIÓN AVL: cada nodo guarda su ALTURA y exigimos que, en todo nodo, las
# alturas de sus dos hijos difieran como máximo en 1. Si una inserción o
# borrado rompe la regla, hacemos ROTACIONES (O(1) cada una). Así la altura
# siempre es O(log n).
#
# COMPLEJIDAD (n = número de claves en el árbol):
#   insertar, eliminar, contiene:            O(log n)
#   desde(inicio, k) (autocompletar/ranking): O(log n + k)
#   rango(desde, hasta):                      O(log n + r), r = claves devueltas
#
# ALTERNATIVAS CONSIDERADAS:
#   - Arreglo ordenado + búsqueda binaria: consultas igual de rápidas
#     (O(log n + k)), pero cerrar/reabrir obliga a desplazar elementos: O(n).
#   - Trie (árbol de prefijos): muy bueno para autocompletar (O(|prefijo| + k)),
#     pero no resuelve bien el rango (R3) ni el ranking (R6), y mantener "solo
#     abiertas" exige contadores en cada nodo. El AVL sirve para R2, R3 y R6.
#   - Recorrer todas las estaciones y filtrar: O(n) por consulta. Descartada.
# =============================================================================


class _NodoAVL:
    # __slots__ evita que cada nodo cargue un diccionario interno de atributos:
    # ahorra memoria cuando hay muchos nodos.
    __slots__ = ("clave", "izquierdo", "derecho", "altura")

    def __init__(self, clave):
        self.clave = clave
        self.izquierdo = None
        self.derecho = None
        self.altura = 1  # una hoja tiene altura 1


# ---------------------------------------------------------------- utilidades
def _altura(nodo):
    # Un subárbol vacío (None) tiene altura 0.
    return 0 if nodo is None else nodo.altura


def _actualizar_altura(nodo):
    # Altura = 1 + la mayor de las alturas de los hijos (sin usar max()).
    ai = _altura(nodo.izquierdo)
    ad = _altura(nodo.derecho)
    nodo.altura = 1 + (ai if ai > ad else ad)


def _balance(nodo):
    # Factor de balance: > 1 cargado a la izquierda, < -1 cargado a la derecha.
    return _altura(nodo.izquierdo) - _altura(nodo.derecho)


def _rotar_derecha(y):
    #        y                x
    #       / \              / \
    #      x   C    -->     A   y
    #     / \                  / \
    #    A   B                B   C
    x = y.izquierdo
    y.izquierdo = x.derecho
    x.derecho = y
    _actualizar_altura(y)  # primero y (quedó abajo), luego x
    _actualizar_altura(x)
    return x  # x es la nueva raíz de este subárbol


def _rotar_izquierda(x):
    #      x                    y
    #     / \                  / \
    #    A   y      -->       x   C
    #       / \              / \
    #      B   C            A   B
    y = x.derecho
    x.derecho = y.izquierdo
    y.izquierdo = x
    _actualizar_altura(x)
    _actualizar_altura(y)
    return y


def _rebalancear(nodo):
    """Revisa el balance de 'nodo' y aplica la rotación que haga falta."""
    _actualizar_altura(nodo)
    b = _balance(nodo)
    if b > 1:
        # Cargado a la izquierda.
        if _balance(nodo.izquierdo) < 0:
            # Caso Izquierda-Derecha: primero rotamos el hijo a la izquierda.
            nodo.izquierdo = _rotar_izquierda(nodo.izquierdo)
        # Caso Izquierda-Izquierda: una rotación a la derecha.
        return _rotar_derecha(nodo)
    if b < -1:
        # Cargado a la derecha.
        if _balance(nodo.derecho) > 0:
            # Caso Derecha-Izquierda.
            nodo.derecho = _rotar_derecha(nodo.derecho)
        # Caso Derecha-Derecha.
        return _rotar_izquierda(nodo)
    return nodo  # ya estaba balanceado


# ===================================================================== AVL
class ArbolAVL:
    def __init__(self):
        self._raiz = None
        self._tamano = 0
        # Bandera interna: las funciones recursivas la usan para avisar si
        # realmente insertaron/borraron algo.
        self._cambio = False

    def __len__(self):
        return self._tamano

    # ------------------------------------------------------------ insertar
    def insertar(self, clave):
        """Inserta la clave. Devuelve False si ya estaba. O(log n)."""
        self._cambio = False
        self._raiz = self._insertar(self._raiz, clave)
        if self._cambio:
            self._tamano += 1
        return self._cambio

    def _insertar(self, nodo, clave):
        # 1. Llegamos a un hueco vacío: aquí va el nuevo nodo.
        if nodo is None:
            self._cambio = True
            return _NodoAVL(clave)
        # 2. Bajamos como en un BST normal.
        if clave < nodo.clave:
            nodo.izquierdo = self._insertar(nodo.izquierdo, clave)
        elif nodo.clave < clave:
            nodo.derecho = self._insertar(nodo.derecho, clave)
        else:
            return nodo  # clave repetida: no se inserta
        # 3. De regreso (al "subir" la recursión) rebalanceamos cada ancestro.
        return _rebalancear(nodo)

    # ------------------------------------------------------------ eliminar
    def eliminar(self, clave):
        """Elimina la clave. Devuelve False si no estaba. O(log n)."""
        self._cambio = False
        self._raiz = self._eliminar(self._raiz, clave)
        if self._cambio:
            self._tamano -= 1
        return self._cambio

    def _eliminar(self, nodo, clave):
        if nodo is None:
            return None  # no estaba
        if clave < nodo.clave:
            nodo.izquierdo = self._eliminar(nodo.izquierdo, clave)
        elif nodo.clave < clave:
            nodo.derecho = self._eliminar(nodo.derecho, clave)
        else:
            # ¡Lo encontramos!
            self._cambio = True
            # Caso 1 y 2: tiene 0 o 1 hijo -> lo reemplaza ese hijo.
            if nodo.izquierdo is None:
                return nodo.derecho
            if nodo.derecho is None:
                return nodo.izquierdo
            # Caso 3: tiene 2 hijos -> lo reemplazamos por su SUCESOR
            # (el menor del subárbol derecho) y borramos el sucesor de allá.
            sucesor = nodo.derecho
            while sucesor.izquierdo is not None:
                sucesor = sucesor.izquierdo
            nodo.clave = sucesor.clave
            nodo.derecho = self._eliminar(nodo.derecho, sucesor.clave)
        return _rebalancear(nodo)

    # ------------------------------------------------------------ buscar
    def contiene(self, clave):
        """True si la clave está. O(log n), iterativo (sin recursión)."""
        nodo = self._raiz
        while nodo is not None:
            if clave < nodo.clave:
                nodo = nodo.izquierdo
            elif nodo.clave < clave:
                nodo = nodo.derecho
            else:
                return True
        return False

    # ------------------------------------------------------------ recorridos
    def desde(self, inicio, k, condicion=None):
        """
        Devuelve hasta k claves >= inicio, en orden ascendente.
        - inicio=None significa "desde la menor clave".
        - condicion: función opcional; en cuanto una clave NO la cumple,
          paramos (sirve para autocompletar: "mientras empiece por CAL").

        Recorrido EN ORDEN iterativo con una PILA (O(log n + k)):
          a) Bajamos desde la raíz guardando en la pila solo los nodos >= inicio
             (son los candidatos, del más pequeño hacia arriba).
          b) Sacamos de la pila (ese es el siguiente en orden), y metemos el
             "borde izquierdo" de su subárbol derecho.
        """
        resultado = []
        if k <= 0:
            return resultado
        pila = []  # pila implementada con list: append = push, pop = pop
        # a) Descenso inicial: O(log n) porque el árbol está balanceado.
        nodo = self._raiz
        while nodo is not None:
            if inicio is None or not (nodo.clave < inicio):
                pila.append(nodo)      # candidato: miramos si hay menores
                nodo = nodo.izquierdo
            else:
                nodo = nodo.derecho    # es muy pequeño: vamos a la derecha
        # b) Sacamos en orden hasta completar k o romper la condición.
        while len(pila) > 0 and len(resultado) < k:
            nodo = pila.pop()
            if condicion is not None and not condicion(nodo.clave):
                break  # todas las siguientes también fallan (están ordenadas)
            resultado.append(nodo.clave)
            # El siguiente en orden es el más a la izquierda del hijo derecho.
            hijo = nodo.derecho
            while hijo is not None:
                pila.append(hijo)
                hijo = hijo.izquierdo
        return resultado

    def rango(self, desde, hasta):
        """Todas las claves c con desde <= c <= hasta, en orden. O(log n + r)."""
        resultado = []
        if hasta < desde:
            return resultado
        # Reutilizamos 'desde' sin límite de cantidad y con la condición
        # "c <= hasta". El límite es el tamaño del árbol (nunca hay más).
        return self.desde(desde, self._tamano, lambda c: not (hasta < c))

    def en_orden(self):
        """Todas las claves en orden. O(n). Útil para depurar y pruebas."""
        return self.desde(None, self._tamano)
