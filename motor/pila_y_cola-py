# =============================================================================
# motor/pila_cola.py
# -----------------------------------------------------------------------------
# PILA (LIFO) y COLA (FIFO) implementadas sobre arreglos (list).
#
#   PILA  (Last In, First Out)  -> R9 deshacer / rehacer.
#         push ->  [ a, b, c ]  <- pop     (entra y sale por el mismo extremo)
#
#   COLA  (First In, First Out) -> R10 fila de abordaje.
#         encolar -> [ a, b, c ] -> desencolar   (entra por atrás, sale por delante)
# =============================================================================


class Pila:
    """
    Pila sobre un arreglo dinámico. El TOPE es el final del arreglo.
      apilar (push):    append -> O(1) amortizado
      desapilar (pop):  pop()  -> O(1)  (quitar el ÚLTIMO no desplaza nada)
    """

    def __init__(self):
        self._datos = []

    def apilar(self, elemento):
        self._datos.append(elemento)

    def desapilar(self):
        if self.vacia():
            raise IndexError("desapilar de una pila vacía")
        return self._datos.pop()

    def tope(self):
        if self.vacia():
            raise IndexError("tope de una pila vacía")
        return self._datos[len(self._datos) - 1]

    def vacia(self):
        return len(self._datos) == 0

    def vaciar(self):
        # Reemplazamos el arreglo: O(1) para nosotros (el recolector de basura
        # libera el anterior).
        self._datos = []

    def __len__(self):
        return len(self._datos)


class Cola:
    """
    Cola sobre un arreglo + un índice 'frente'.

    ¿Por qué no usar lista.pop(0)? Porque quitar el PRIMERO de un arreglo
    obliga a desplazar todos los demás: O(n). Con cientos de miles de
    pasajeros (R10) eso sería O(n^2) en total.

    En vez de eso, NO borramos: movemos el índice 'frente' una posición.
      encolar:    append          -> O(1) amortizado
      desencolar: datos[frente]; frente += 1   -> O(1)
    Cuando la parte "ya atendida" (antes de frente) ocupa más de la mitad,
    compactamos copiando lo que queda: O(n) pero ocurre pocas veces, así que
    el costo amortizado sigue siendo O(1) y la memoria no crece sin límite.

    Alternativa equivalente: cola con lista enlazada (nodos con 'siguiente').
    Misma complejidad; el arreglo usa menos memoria por elemento.
    """

    def __init__(self):
        self._datos = []
        self._frente = 0

    def encolar(self, elemento):
        self._datos.append(elemento)

    def desencolar(self):
        if self.vacia():
            raise IndexError("desencolar de una cola vacía")
        elemento = self._datos[self._frente]
        self._datos[self._frente] = None  # soltamos la referencia
        self._frente += 1
        # Compactación ocasional (amortizada).
        if self._frente > 64 and self._frente * 2 > len(self._datos):
            self._datos = self._datos[self._frente:]
            self._frente = 0
        return elemento

    def frente(self):
        if self.vacia():
            raise IndexError("frente de una cola vacía")
        return self._datos[self._frente]

    def vacia(self):
        return self._frente == len(self._datos)

    def __len__(self):
        return len(self._datos) - self._frente
