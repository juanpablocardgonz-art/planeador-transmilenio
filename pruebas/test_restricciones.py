# =============================================================================
# pruebas/test_restricciones.py
# -----------------------------------------------------------------------------
# Revisa AUTOMÁTICAMENTE que el código de motor/ no use nada prohibido.
# "Un requisito que pasa las pruebas usando algo prohibido dentro de motor/
#  no recibe puntos de resultados ni de rendimiento."
#
# ¿Cómo? Con el módulo ast de Python (permitido fuera de motor/): convierte
# cada archivo en un ÁRBOL DE SINTAXIS y lo recorremos buscando:
#   - dict y set: literales {}, {a, b}, comprensiones y llamadas dict()/set()
#   - llamadas a sorted(), min(), max(), frozenset()
#   - métodos .sort(), .index(), .count()
#   - el operador "in" / "not in" en comparaciones (x in lista).
#     OJO: "for x in lista" NO es una comparación y sí está permitido.
#   - imports distintos de csv, time, random o del propio paquete (from .x)
#
# Correr antes de cada Pull Request:
#     python -m unittest pruebas.test_restricciones -v
# =============================================================================

import ast
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTOR = os.path.join(RAIZ, "motor")

NOMBRES_PROHIBIDOS = ("dict", "set", "frozenset", "sorted", "min", "max")
METODOS_PROHIBIDOS = ("sort", "index", "count")
MODULOS_PERMITIDOS = ("csv", "time", "random")


def buscar_infracciones(codigo, archivo):
    """Devuelve una lista de textos 'archivo:línea: problema'."""
    problemas = []
    arbol = ast.parse(codigo, filename=archivo)
    for nodo in ast.walk(arbol):
        linea = getattr(nodo, "lineno", "?")

        def reportar(texto):
            problemas.append(f"{archivo}:{linea}: {texto}")

        # 1. Literales y comprensiones de dict / set.
        if isinstance(nodo, (ast.Dict, ast.DictComp)):
            reportar("uso de dict ({})")
        elif isinstance(nodo, (ast.Set, ast.SetComp)):
            reportar("uso de set")
        # 2. Llamadas prohibidas: sorted(...), x.sort(), ...
        elif isinstance(nodo, ast.Call):
            f = nodo.func
            if isinstance(f, ast.Name) and f.id in NOMBRES_PROHIBIDOS:
                reportar(f"llamada prohibida {f.id}()")
            if isinstance(f, ast.Attribute) and f.attr in METODOS_PROHIBIDOS:
                reportar(f"método prohibido .{f.attr}()")
        # 3. Operador in / not in en comparaciones.
        elif isinstance(nodo, ast.Compare):
            for op in nodo.ops:
                if isinstance(op, (ast.In, ast.NotIn)):
                    reportar("operador 'in' para buscar")
        # 4. Imports.
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name.split(".")[0] not in MODULOS_PERMITIDOS:
                    reportar(f"import prohibido {alias.name}")
        elif isinstance(nodo, ast.ImportFrom):
            # level > 0 significa import relativo (from .algo import ...).
            if nodo.level == 0 and (nodo.module or "").split(".")[0] not in MODULOS_PERMITIDOS:
                reportar(f"import prohibido {nodo.module}")
    return problemas


class PruebaRestricciones(unittest.TestCase):
    def test_motor_no_usa_nada_prohibido(self):
        problemas = []
        for nombre in sorted(os.listdir(MOTOR)):
            if nombre.endswith(".py"):
                ruta = os.path.join(MOTOR, nombre)
                with open(ruta, encoding="utf-8") as f:
                    problemas += buscar_infracciones(f.read(), "motor/" + nombre)
        self.assertEqual(problemas, [], "\n" + "\n".join(problemas))

    def test_el_detector_funciona(self):
        # Verificamos el verificador: un código con trampas debe fallar.
        malo = "import heapq\nx = {}\ny = sorted([2, 1])\nif 3 in y: pass\ny.sort()\n"
        self.assertEqual(len(buscar_infracciones(malo, "malo.py")), 5)


if __name__ == "__main__":
    unittest.main()
