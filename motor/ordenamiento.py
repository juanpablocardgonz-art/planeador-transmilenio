# =============================================================================
# motor/ordenamiento.py
# -----------------------------------------------------------------------------
# Algoritmos de ordenamiento y búsqueda escritos a mano.
#
# El enunciado prohíbe sorted(), .sort(), bisect, min() y max() dentro de
# motor/. Por eso implementamos aquí:
#
#   1. merge_sort            -> ordenar (Divide y vencerás, O(n log n)).
#   2. esta_ordenada         -> verificar si ya está ordenada (O(n)).
#   3. primer_mayor_o_igual  -> búsqueda binaria "lower bound" (O(log n)).
#   4. sin_repetidos         -> quitar duplicados de una lista ordenada (O(n)).
#
# ¿Por qué Merge Sort y no Insertion/Bubble/Selection Sort?
#   - Bubble, Selection e Insertion son O(n^2): con 140.000 horarios serían
#     ~2 * 10^10 comparaciones en el peor caso. Inviable.
#   - Merge Sort es O(n log n) SIEMPRE (también en el peor caso) y es ESTABLE:
#     si dos elementos son iguales conserva su orden original. La estabilidad
#     la usamos en simular_fila (R10): dos pasajeros que llegan a la misma
#     hora deben conservar su orden de llegada.
#   - Alternativa descartada: Quick Sort (O(n^2) en el peor caso y no estable).
# =============================================================================


def esta_ordenada(lista, clave=None):
    """Devuelve True si la lista ya está en orden no decreciente. O(n)."""
    # Recorremos pares vecinos (i-1, i). Si algún vecino de la izquierda es
    # mayor que el de la derecha, la lista no está ordenada.
    for i in range(1, len(lista)):
        if clave is None:
            anterior, actual = lista[i - 1], lista[i]
        else:
            anterior, actual = clave(lista[i - 1]), clave(lista[i])
        if actual < anterior:
            return False
    return True


def merge_sort(lista, clave=None):
    """
    Ordena con Merge Sort y devuelve una LISTA NUEVA (no modifica la original).

    - clave: función opcional que dice por qué valor comparar cada elemento
      (igual que el parámetro key de sorted). Ej: clave=lambda p: p[0].
    - Complejidad: O(n log n) en tiempo, O(n) de memoria extra.
    - Mejor caso O(n): si ya estaba ordenada, no hacemos nada más.
    """
    # Atajo (mejor caso): muchos horarios llegan ya ordenados en el CSV.
    # Revisarlo cuesta O(n), mucho menos que O(n log n).
    if esta_ordenada(lista, clave):
        return list(lista)
    return _merge_sort_recursivo(lista, clave)


def _merge_sort_recursivo(lista, clave):
    # CASO BASE: una lista de 0 o 1 elementos ya está ordenada.
    n = len(lista)
    if n <= 1:
        return list(lista)
    # DIVIDIR: partimos la lista por la mitad.
    mitad = n // 2
    izquierda = _merge_sort_recursivo(lista[:mitad], clave)
    derecha = _merge_sort_recursivo(lista[mitad:], clave)
    # COMBINAR: mezclamos las dos mitades ya ordenadas.
    return _mezclar(izquierda, derecha, clave)


def _mezclar(izquierda, derecha, clave):
    """Mezcla dos listas ordenadas en una sola lista ordenada. O(n)."""
    resultado = []
    i = 0  # índice dentro de 'izquierda'
    j = 0  # índice dentro de 'derecha'
    # Mientras queden elementos en ambas, tomamos el menor de los dos frentes.
    while i < len(izquierda) and j < len(derecha):
        if clave is None:
            a, b = izquierda[i], derecha[j]
        else:
            a, b = clave(izquierda[i]), clave(derecha[j])
        # Usamos "b < a" (y no "b <= a") para que, si son iguales, gane el de
        # la izquierda. Eso hace que el algoritmo sea ESTABLE.
        if b < a:
            resultado.append(derecha[j])
            j += 1
        else:
            resultado.append(izquierda[i])
            i += 1
    # Una de las dos se acabó: copiamos lo que sobre de la otra.
    while i < len(izquierda):
        resultado.append(izquierda[i])
        i += 1
    while j < len(derecha):
        resultado.append(derecha[j])
        j += 1
    return resultado


def primer_mayor_o_igual(arreglo, objetivo):
    """
    Búsqueda binaria "lower bound".

    Devuelve la PRIMERA posición i tal que arreglo[i] >= objetivo.
    Si todos son menores, devuelve len(arreglo).
    Requisito: el arreglo debe estar ordenado.
    Complejidad: O(log n), porque en cada paso descartamos la mitad.

    Ejemplo: arreglo = [300, 310, 320], objetivo = 305 -> 1 (el 310).
    """
    # Invariante: la respuesta siempre está en el intervalo [bajo, alto].
    bajo = 0
    alto = len(arreglo)
    while bajo < alto:
        medio = (bajo + alto) // 2
        if arreglo[medio] < objetivo:
            # arreglo[medio] es muy pequeño: la respuesta está a la derecha.
            bajo = medio + 1
        else:
            # arreglo[medio] sirve, pero puede haber uno que sirva más a la
            # izquierda: seguimos buscando en [bajo, medio].
            alto = medio
    return bajo


def sin_repetidos(arreglo_ordenado):
    """
    Quita los valores repetidos de una lista YA ORDENADA. O(n).
    Como está ordenada, los repetidos quedan juntos: basta comparar cada
    elemento con el último que guardamos.
    """
    resultado = []
    for valor in arreglo_ordenado:
        if len(resultado) == 0 or resultado[len(resultado) - 1] != valor:
            resultado.append(valor)
    return resultado
