# =============================================================================
# motor/  —  paquete con TODA la lógica evaluada del proyecto.
#
# El script del profesor hace exactamente:
#       from motor import Red, simular_fila
# así que aquí "exportamos" esos dos nombres.
#
# Mapa de archivos (cada uno explica su estructura y su complejidad):
#   red.py           Clase Red: el contrato R1-R9 (fachada que une todo)
#   tabla_hash.py    Tabla hash propia con encadenamiento      (R1, índices)
#   avl.py           Árbol AVL (BST balanceado)                (R2, R3, R6, R8)
#   lista_doble.py   Lista doblemente enlazada de paradas      (R7)
#   pila_cola.py     Pila (LIFO) y Cola (FIFO) sobre arreglos  (R9, R10)
#   historial.py     Deshacer/rehacer: dos pilas + Command     (R9)
#   planificador.py  Viaje con máximo un transbordo            (R5)
#   simulacion.py    Fila de abordaje                          (R10)
#   ordenamiento.py  Merge Sort y búsqueda binaria             (R4 y carga)
#   modelo.py        Clases Estacion y Ruta
#   carga.py         Lectura de los CSV con el módulo csv
#   horas.py         "HH:MM" <-> minutos
#
# Reglas del enunciado dentro de motor/: sin dict, set, sorted, .sort, min,
# max, "x in lista", .index, .count, bisect, heapq, collections, functools ni
# librerías externas. Solo csv, time y random. La prueba
# pruebas/test_restricciones.py revisa esto automáticamente.
# =============================================================================
"""Motor del planeador TransMilenio."""

from .red import Red
from .simulacion import simular_fila

__all__ = ["Red", "simular_fila"]
