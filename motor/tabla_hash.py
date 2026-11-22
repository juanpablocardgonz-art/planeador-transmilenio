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
#   1. Una función hash convierte la clave (un texto) en un número entero
#      (ver _hash: usamos hash() de Python; la polinomial queda documentada).
#   2. Ese número módulo la capacidad nos da una "cubeta" (posición del arreglo).
#   3. Varias claves pueden caer en la misma cubeta (COLISIÓN). Cada cubeta
#      guarda una pequeña lista con sus pares clave/valor: eso es el
#      encadenamiento.
#   4. Si la tabla se llena demasiado (factor de carga > 0.75) duplicamos la
#      capacidad y re-ubicamos todo (REHASH). Igual que un arreglo dinámico,
#      el costo O(n) del rehash se reparte: inserción O(1) AMORTIZADA.
#
#   cubetas:  [0] -> None
#             [1] -> ["AV. JIMENEZ", est1, "CALLE 26", est2]   <- colisión
#             [2] -> ["PORTAL SUR", est3]
#             ...
#
#   Cada cubeta es UNA lista "aplanada": clave en posición par (0, 2, 4...) y
#   su valor justo después (1, 3, 5...). Primero usábamos una lista por cada
#   par ([[k1, v1], [k2, v2]]), pero con la red de 80.000 estaciones eso son
#   más de 600.000 listitas extra: más memoria y más trabajo para el
#   recolector de basura de Python. Aplanando, la carga bajó ~15%.
#
# COMPLEJIDAD (n = número de claves, L = largo de la clave):
#   buscar / insertar / eliminar: O(1) promedio (O(L) la primera vez que se
#                                 calcula el hash de un texto)
#                                 O(n) peor caso (todo en la misma cubeta)
#
# ALTERNATIVAS CONSIDERADAS:
#   - Lista + búsqueda lineal: O(n) por consulta. Descartada.
#   - Arreglo ordenado + búsqueda binaria: O(log n), pero insertar es O(n).
#   - Direccionamiento abierto (sondeo lineal): misma complejidad promedio,
#     pero borrar exige "lápidas" y se degrada más con carga alta.
#   - Encadenamiento con LISTAS ENLAZADAS: misma complejidad, pero un nodo
#     por clave (más memoria). Usamos un arreglo por cubeta.
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
    def hash_polinomial(clave):
        """
        Función hash POLINOMIAL para textos (la misma idea que usa Java):
            h = c0 * 31^(L-1) + c1 * 31^(L-2) + ... + c(L-1)
        Se calcula con el método de Horner: h = h * 31 + código del carácter.
        Usamos 31 porque es primo e impar: reparte bien las claves.
        Hacemos "% 2^61-1" en cada paso para que el número no crezca sin
        límite (2^61-1 es un primo de Mersenne grande).

        Esta fue nuestra PRIMERA versión de _hash. La dejamos para explicar
        la idea y para las pruebas, pero la tabla usa hash() (ver abajo).
        """
        h = 0
        for caracter in clave:
            h = (h * 31 + ord(caracter)) % 2305843009213693951
        return h

    @staticmethod
    def _hash(clave):
        """
        Usamos la función hash() de Python (no está prohibida: lo prohibido
        son dict, set y las búsquedas/ordenamientos de la librería).

        ¿Por qué cambiamos la polinomial por hash()? Lo MEDIMOS con el
        perfilador: con la red de 10.000 estaciones, calcular la polinomial
        letra por letra en Python era el 40% del tiempo de carga.
          - hash() hace el mismo tipo de cálculo (recorre el texto una vez,
            O(L)), pero escrito en C: muchísimo más rápido.
          - Python GUARDA el hash dentro del objeto texto la primera vez que
            se calcula: las siguientes búsquedas con el mismo texto cuestan O(1).
        Lo demás de la tabla hash (cubetas, encadenamiento, factor de carga,
        rehash) sigue siendo nuestro.
        """
        return hash(clave)

    def _posicion(self, clave):
        # De número hash a índice válido del arreglo: residuo de la división.
        return hash(clave) % len(self._cubetas)

    # ------------------------------------------------------------ operaciones
    def insertar(self, clave, valor):
        """Guarda (clave, valor). Si la clave ya existía, reemplaza el valor."""
        pos = self._posicion(clave)
        cubeta = self._cubetas[pos]
        if cubeta is None:
            # Primera clave en esta cubeta: creamos su lista [clave, valor].
            self._cubetas[pos] = [clave, valor]
        else:
            # Recorremos solo las CLAVES (posiciones pares). La cadena casi
            # siempre tiene 1 o 2 claves.
            for i in range(0, len(cubeta), 2):
                if cubeta[i] == clave:
                    cubeta[i + 1] = valor  # ya existía: actualizamos
                    return
            cubeta.append(clave)
            cubeta.append(valor)
        self._tamano += 1
        # ¿Se llenó demasiado? Entonces duplicamos (rehash).
        if self._tamano > len(self._cubetas) * self._CARGA_MAXIMA:
            self._redimensionar(len(self._cubetas) * 2)

    def buscar(self, clave, defecto=None):
        """Devuelve el valor asociado a la clave, o 'defecto' si no existe."""
        cubeta = self._cubetas[hash(clave) % len(self._cubetas)]
        if cubeta is not None:
            for i in range(0, len(cubeta), 2):
                if cubeta[i] == clave:
                    return cubeta[i + 1]
        return defecto

    def contiene(self, clave):
        """True si la clave está en la tabla."""
        cubeta = self._cubetas[hash(clave) % len(self._cubetas)]
        if cubeta is not None:
            for i in range(0, len(cubeta), 2):
                if cubeta[i] == clave:
                    return True
        return False

    def eliminar(self, clave):
        """Borra la clave. Devuelve True si existía, False si no."""
        pos = self._posicion(clave)
        cubeta = self._cubetas[pos]
        if cubeta is None:
            return False
        for i in range(0, len(cubeta), 2):
            if cubeta[i] == clave:
                # Truco O(1): pasamos el ÚLTIMO par (clave, valor) a la
                # posición i y quitamos los dos últimos elementos. El orden
                # dentro de la cubeta no importa.
                ultimo = len(cubeta) - 2
                cubeta[i] = cubeta[ultimo]
                cubeta[i + 1] = cubeta[ultimo + 1]
                cubeta.pop()
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
                for i in range(0, len(cubeta), 2):
                    # La posición cambia porque cambió len(self._cubetas).
                    self.insertar(cubeta[i], cubeta[i + 1])

    # -------------------------------------------------------------- recorrido
    def pares(self):
        """Lista de (clave, valor) en orden arbitrario. O(n + capacidad)."""
        resultado = []
        for cubeta in self._cubetas:
            if cubeta is not None:
                for i in range(0, len(cubeta), 2):
                    resultado.append((cubeta[i], cubeta[i + 1]))
        return resultado

    def claves(self):
        resultado = []
        for cubeta in self._cubetas:
            if cubeta is not None:
                for i in range(0, len(cubeta), 2):
                    resultado.append(cubeta[i])
        return resultado

    def valores(self):
        resultado = []
        for cubeta in self._cubetas:
            if cubeta is not None:
                for i in range(1, len(cubeta), 2):
                    resultado.append(cubeta[i])
        return resultado

    def __len__(self):
        return self._tamano
