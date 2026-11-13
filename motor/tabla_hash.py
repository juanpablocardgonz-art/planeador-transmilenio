# =============================================================================
# motor/tabla_hash.py
# -----------------------------------------------------------------------------
# TABLA HASH propia con ENCADENAMIENTO (chaining).
#
# El enunciado prohíbe dict y set dentro de motor/. Pero necesitamos responder
# "¿existe la estación X?" muchísimas veces (R1 es la consulta más usada), y
# buscar en una lista sería O(n). La solución es construir nuestra propia
# tabla hash.
#
# IDEA:
#   1. Una función hash convierte la clave (un texto) en un número entero.
#   2. Ese número módulo la capacidad nos da una "cubeta" (posición del arreglo).
#   3. Varias claves pueden caer en la misma cubeta (COLISIÓN). Cada cubeta
#      guarda una pequeña lista de pares [clave, valor]: eso es el
#      encadenamiento.
#   4. Si la tabla se llena demasiado (factor de carga > 0.75) duplicamos la
#      capacidad y re-ubicamos todo (REHASH). Igual que un arreglo dinámico,
#      el costo O(n) del rehash se reparte: inserción O(1) AMORTIZADA.
#
#   cubetas:  [0] -> None
#             [1] -> [["AV. JIMENEZ", est1], ["CALLE 26", est2]]   <- colisión
#             [2] -> [["PORTAL SUR", est3]]
#             ...
#
# COMPLEJIDAD (n = número de claves, L = largo de la clave):
#   buscar / insertar / eliminar: O(L) promedio  -> O(1) respecto a n
#                                 O(n) peor caso (todo en la misma cubeta)
#
# ALTERNATIVAS CONSIDERADAS:
#   - Lista + búsqueda lineal: O(n) por consulta. Descartada.
#   - Arreglo ordenado + búsqueda binaria: O(log n), pero insertar es O(n).
#   - Encadenamiento con LISTAS ENLAZADAS en vez de listas de Python: misma
#     complejidad; usamos list porque el enunciado la permite como arreglo y
#     es más simple de leer.
# =============================================================================


class TablaHash:
    # Cuando (elementos / cubetas) supera este valor, duplicamos la capacidad.
    _CARGA_MAXIMA = 0.75

    def __init__(self, capacidad_inicial=16):
        # Arreglo de cubetas. None significa "cubeta vacía" (ahorra memoria:
        # solo creamos la lista interna cuando llega la primera clave).
        self._cubetas = [None] * capacidad_inicial
        # Cuántas claves hay guardadas en total.
        self._tamano = 0

    # ------------------------------------------------------------------ hash
    @staticmethod
    def _hash(clave):
        """
        Función hash POLINOMIAL para textos (la misma idea que usa Java):
            h = c0 * 31^(L-1) + c1 * 31^(L-2) + ... + c(L-1)
        Se calcula con el método de Horner: h = h * 31 + código del carácter.
        Usamos 31 porque es primo e impar: reparte bien las claves.
        Hacemos "% 2^61-1" en cada paso para que el número no crezca sin
        límite (2^61-1 es un primo de Mersenne grande).
        """
        h = 0
        for caracter in clave:
            h = (h * 31 + ord(caracter)) % 2305843009213693951
        return h

    def _posicion(self, clave):
        # De número hash a índice válido del arreglo: residuo de la división.
        return self._hash(clave) % len(self._cubetas)

    # ------------------------------------------------------------ operaciones
    def insertar(self, clave, valor):
        """Guarda (clave, valor). Si la clave ya existía, reemplaza el valor."""
        pos = self._posicion(clave)
        cubeta = self._cubetas[pos]
        if cubeta is None:
            # Primera clave en esta cubeta: creamos su lista.
            self._cubetas[pos] = [[clave, valor]]
        else:
            # Recorremos la cadena (normalmente 0, 1 o 2 elementos).
            for par in cubeta:
                if par[0] == clave:
                    par[1] = valor  # ya existía: actualizamos
                    return
            cubeta.append([clave, valor])
        self._tamano += 1
        # ¿Se llenó demasiado? Entonces duplicamos (rehash).
        if self._tamano > len(self._cubetas) * self._CARGA_MAXIMA:
            self._redimensionar(len(self._cubetas) * 2)

    def buscar(self, clave, defecto=None):
        """Devuelve el valor asociado a la clave, o 'defecto' si no existe."""
        cubeta = self._cubetas[self._posicion(clave)]
        if cubeta is not None:
            for par in cubeta:
                if par[0] == clave:
                    return par[1]
        return defecto

    def contiene(self, clave):
        """True si la clave está en la tabla."""
        cubeta = self._cubetas[self._posicion(clave)]
        if cubeta is not None:
            for par in cubeta:
                if par[0] == clave:
                    return True
        return False

    def eliminar(self, clave):
        """Borra la clave. Devuelve True si existía, False si no."""
        pos = self._posicion(clave)
        cubeta = self._cubetas[pos]
        if cubeta is None:
            return False
        for i in range(len(cubeta)):
            if cubeta[i][0] == clave:
                # Truco O(1): pasamos el último par a la posición i y quitamos
                # el último. El orden dentro de la cubeta no importa.
                ultimo = len(cubeta) - 1
                cubeta[i] = cubeta[ultimo]
                cubeta.pop()
                if len(cubeta) == 0:
                    self._cubetas[pos] = None
                self._tamano -= 1
                return True
        return False

    def _redimensionar(self, nueva_capacidad):
        """REHASH: crea un arreglo más grande y vuelve a ubicar cada par. O(n)."""
        viejas = self._cubetas
        self._cubetas = [None] * nueva_capacidad
        self._tamano = 0
        for cubeta in viejas:
            if cubeta is not None:
                for par in cubeta:
                    # La posición cambia porque cambió len(self._cubetas).
                    self.insertar(par[0], par[1])

    # -------------------------------------------------------------- recorrido
    def pares(self):
        """Lista de (clave, valor) en orden arbitrario. O(n + capacidad)."""
        resultado = []
        for cubeta in self._cubetas:
            if cubeta is not None:
                for par in cubeta:
                    resultado.append((par[0], par[1]))
        return resultado

    def claves(self):
        resultado = []
        for par in self.pares():
            resultado.append(par[0])
        return resultado

    def valores(self):
        resultado = []
        for par in self.pares():
            resultado.append(par[1])
        return resultado

    def __len__(self):
        return self._tamano
