# =============================================================================
# pruebas/test_motor.py
# -----------------------------------------------------------------------------
# Pruebas FUNCIONALES de R1 a R10 sobre una red pequeña hecha a mano
# (pruebas/red_mini), donde podemos calcular las respuestas en papel:
#
#   R1: A -> B -> C -> D
#   R2: C -> E -> X                (en el CSV viene desordenada a propósito)
#   R3: A -> CAL 1 -> CAL 2 -> CAL 3 -> D -> E
#
#   Buses al día: A=4 (R1 tiene 06:20 repetido, cuenta una vez), C=2, D=2,
#   E=2, y el resto 1.
#
# Además hay una prueba con la red REAL (datos/) para comprobar que carga.
#
# Cómo correr todas las pruebas (desde la raíz del repositorio):
#     python -m unittest discover -s pruebas -v
# =============================================================================

import os
import sys
import unittest

# Agregamos la raíz del repositorio al path para poder hacer "import motor".
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from motor import Red, simular_fila  # noqa: E402

MINI = os.path.join(RAIZ, "pruebas", "red_mini")
DATOS = os.path.join(RAIZ, "datos")


class PruebasConsultas(unittest.TestCase):
    def setUp(self):
        # Cada prueba arranca con una red recién cargada.
        self.red = Red(MINI)

    # ---------------------------------------------------------------- R1
    def test_r1_estado(self):
        self.assertEqual(self.red.estado("A"), "ABIERTA")
        self.assertEqual(self.red.estado("NO EXISTE"), "NO EXISTE")
        self.red.cerrar("A")
        self.assertEqual(self.red.estado("A"), "CERRADA")
        # Los nombres van exactamente como vienen en el CSV.
        self.assertEqual(self.red.estado("a"), "NO EXISTE")

    # ---------------------------------------------------------------- R2
    def test_r2_autocompletar(self):
        self.assertEqual(self.red.autocompletar("CAL", 10), ["CAL 1", "CAL 2", "CAL 3"])
        self.assertEqual(self.red.autocompletar("CAL", 2), ["CAL 1", "CAL 2"])
        self.assertEqual(self.red.autocompletar("ZZZ", 5), [])
        self.assertEqual(self.red.autocompletar("CAL", 0), [])
        # Una estación cerrada no aparece.
        self.red.cerrar("CAL 1")
        self.assertEqual(self.red.autocompletar("CAL", 2), ["CAL 2", "CAL 3"])
        # Prefijo vacío: las primeras k abiertas en orden alfabético.
        self.assertEqual(self.red.autocompletar("", 3), ["A", "B", "C"])

    # ---------------------------------------------------------------- R3
    def test_r3_rango(self):
        self.assertEqual(self.red.rango("B", "CAL 2"), ["B", "C", "CAL 1", "CAL 2"])
        self.assertEqual(self.red.rango("D", "B"), [])           # al revés
        self.assertEqual(self.red.rango("BB", "BZ"), [])         # nada adentro
        self.red.cerrar("C")
        self.assertEqual(self.red.rango("B", "CAL 1"), ["B", "CAL 1"])

    # ---------------------------------------------------------------- R4
    def test_r4_proximo_bus(self):
        self.assertEqual(self.red.proximo_bus("A", "R1", "06:05"), "06:10")
        self.assertEqual(self.red.proximo_bus("A", "R1", "06:10"), "06:10")  # misma hora
        self.assertEqual(self.red.proximo_bus("A", "R1", "05:00"), "06:00")
        self.assertIsNone(self.red.proximo_bus("A", "R1", "06:21"))        # ya no hay
        self.assertIsNone(self.red.proximo_bus("X", "R1", "06:00"))        # no para ahí
        self.assertIsNone(self.red.proximo_bus("A", "NOPE", "06:00"))
        self.red.cerrar("A")
        self.assertIsNone(self.red.proximo_bus("A", "R1", "06:00"))        # cerrada

    # ---------------------------------------------------------------- R5
    def test_r5_viaje(self):
        # Directo por R1 (3 paradas) es mejor que por R3 (5 paradas).
        self.assertEqual(self.red.viaje("A", "D"), [("R1", "A", "D")])
        # Con transbordo en C: A->C por R1 (2) + C->X por R2 (2).
        self.assertEqual(self.red.viaje("A", "X"), [("R1", "A", "C"), ("R2", "C", "X")])
        self.assertEqual(self.red.viaje_con_paradas("A", "X")[0], 4)
        self.assertEqual(self.red.viaje("B", "E"), [("R1", "B", "C"), ("R2", "C", "E")])
        # Si cerramos C, ya no se puede transbordar ahí: toca por D.
        self.red.cerrar("C")
        self.assertEqual(self.red.viaje("B", "E"), [("R1", "B", "D"), ("R3", "D", "E")])
        # Casos borde.
        self.assertIsNone(self.red.viaje("D", "A"))      # no hay forma
        self.assertIsNone(self.red.viaje("A", "C"))      # destino cerrado
        self.assertIsNone(self.red.viaje("C", "A"))      # origen cerrado
        self.assertEqual(self.red.viaje("A", "A"), [])
        self.assertIsNone(self.red.viaje("A", "NOPE"))

    # ---------------------------------------------------------------- R6
    def test_r6_ranking(self):
        top = self.red.ranking(4)
        self.assertEqual(top[0], ("A", 4))
        # Empate de 2 buses entre C, D y E: orden alfabético.
        self.assertEqual(top[1:], [("C", 2), ("D", 2), ("E", 2)])
        self.red.cerrar("A")
        self.assertEqual(self.red.ranking(1), [("C", 2)])
        self.assertEqual(self.red.ranking(0), [])

    # ---------------------------------------------------------------- R7
    def test_r7_editar_rutas(self):
        self.assertEqual(self.red.recorrido("R2"), ["C", "E", "X"])  # se ordenó
        self.assertEqual(self.red.recorrido("R1", al_reves=True), ["D", "C", "B", "A"])
        self.assertTrue(self.red.agregar_parada("R1", "X", "B"))
        self.assertEqual(self.red.recorrido("R1"), ["A", "B", "X", "C", "D"])
        # X hereda las horas de B: un bus más al día.
        self.assertEqual(self.red.buses_de("X"), 2)
        self.assertEqual(self.red.proximo_bus("X", "R1", "06:00"), "06:05")
        self.assertTrue(self.red.quitar_parada("R1", "A"))
        self.assertEqual(self.red.recorrido("R1"), ["B", "X", "C", "D"])
        self.assertTrue(self.red.agregar_parada("R1", "A", None))  # al inicio
        self.assertEqual(self.red.recorrido("R1"), ["A", "B", "X", "C", "D"])
        self.assertTrue(self.red.quitar_parada("R1", "D"))          # la última
        self.assertEqual(self.red.recorrido("R1", True), ["C", "X", "B", "A"])
        # Inválidos.
        self.assertFalse(self.red.agregar_parada("R1", "B", "A"))     # ya está
        self.assertFalse(self.red.agregar_parada("R1", "E", "NOPE"))  # ref no está
        self.assertFalse(self.red.agregar_parada("NOPE", "E", "A"))
        self.assertFalse(self.red.quitar_parada("R1", "E"))
        self.assertEqual(self.red.recorrido("NOPE"), [])

    # ---------------------------------------------------------------- R8
    def test_r8_cerrar_reabrir(self):
        self.assertTrue(self.red.cerrar("B"))
        self.assertFalse(self.red.cerrar("B"))       # ya cerrada
        self.assertFalse(self.red.cerrar("NOPE"))
        self.assertTrue(self.red.reabrir("B"))
        self.assertFalse(self.red.reabrir("B"))      # ya abierta
        self.assertEqual(self.red.estado("B"), "ABIERTA")

    # ---------------------------------------------------------------- R9
    def test_r9_deshacer_rehacer(self):
        self.assertFalse(self.red.deshacer())        # nada que deshacer
        self.red.cerrar("A")
        self.red.quitar_parada("R1", "B")
        self.red.agregar_parada("R1", "E", "C")
        self.assertEqual(self.red.recorrido("R1"), ["A", "C", "E", "D"])
        # Deshacemos en orden inverso.
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.recorrido("R1"), ["A", "C", "D"])
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.recorrido("R1"), ["A", "B", "C", "D"])
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.estado("A"), "ABIERTA")
        self.assertEqual(self.red.ranking(1), [("A", 4)])
        # Rehacemos.
        self.assertTrue(self.red.rehacer())
        self.assertEqual(self.red.estado("A"), "CERRADA")
        self.assertTrue(self.red.rehacer())
        self.assertEqual(self.red.recorrido("R1"), ["A", "C", "D"])
        # Un cambio nuevo borra lo que había para rehacer.
        self.red.reabrir("A")
        self.assertFalse(self.red.rehacer())
        self.assertEqual(self.red.estado("A"), "ABIERTA")


class PruebasFila(unittest.TestCase):
    # ---------------------------------------------------------------- R10
    def test_r10_ejemplo_del_enunciado(self):
        self.assertEqual(simular_fila([30, 5, 5, 70], 60, 2), [120, 60, 60, 120])

    def test_r10_basico(self):
        # Buses salen en 5, 10, 15, ... con 2 cupos (el primero en 'frecuencia').
        salidas = simular_fila([0, 1, 1, 2, 7, 7, 7, 30], 5, 2)
        self.assertEqual(salidas, [5, 5, 10, 10, 15, 15, 20, 30])
        # Quien llega justo en el segundo de salida alcanza ese bus.
        self.assertEqual(simular_fila([60, 60, 61], 60, 5), [60, 60, 120])

    def test_r10_desordenado_y_bordes(self):
        # Llegadas desordenadas: se atiende por hora de llegada; si empatan,
        # por el orden en la lista (estable).
        self.assertEqual(simular_fila([6, 1, 1], 5, 1), [15, 5, 10])
        self.assertEqual(simular_fila([], 5, 3), [])
        with self.assertRaises(ValueError):
            simular_fila([1], 0, 3)

    def test_r10_muchos_pasajeros(self):
        llegadas = list(range(200000))       # uno por minuto
        salidas = simular_fila(llegadas, 10, 100)
        self.assertEqual(len(salidas), 200000)
        self.assertEqual(salidas[0], 10)
        self.assertEqual(salidas[10], 10)
        self.assertEqual(salidas[11], 20)


class PruebasRedReal(unittest.TestCase):
    def test_carga_red_real(self):
        if not os.path.exists(os.path.join(DATOS, "estaciones.csv")):
            self.skipTest("no están los CSV en datos/")
        red = Red(DATOS)
        estaciones, abiertas, rutas, horarios, _, _ = red.resumen()
        self.assertEqual(estaciones, 147)
        self.assertEqual(rutas, 181)
        self.assertTrue(horarios > 100000)
        self.assertEqual(red.ranking(1)[0][0], "RICAURTE")


if __name__ == "__main__":
    unittest.main()
