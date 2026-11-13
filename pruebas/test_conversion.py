# =============================================================================
# pruebas/test_conversion.py
# -----------------------------------------------------------------------------
# Prueba el script de conversión con un GTFS diminuto armado en memoria, y
# verifica que el motor pueda cargar lo que el script produce.
# =============================================================================

import csv
import os
import sys
import tempfile
import unittest
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from conversion.convertir_gtfs import convertir, hora_valida, normalizar  # noqa: E402
from motor import Red  # noqa: E402

GTFS = {
    "stops.txt": "stop_id,stop_name,parent_station\n"
                 "E1,Héroes,\nE1a,Héroes vagón 1,E1\nE2,Calle  26,\nE3,Ricaurte,\n",
    "routes.txt": "route_id,route_short_name\nr1,B11\n",
    "trips.txt": "trip_id,route_id,direction_id\nt1,r1,0\nt2,r1,0\nt3,r1,1\n",
    "stop_times.txt": "trip_id,stop_id,stop_sequence,arrival_time,departure_time\n"
                      "t1,E1a,1,06:00:00,06:00:00\nt1,E2,2,06:05:00,06:05:00\nt1,E3,3,06:10:00,06:10:00\n"
                      "t2,E1,1,25:10:00,25:10:00\nt2,E2,2,25:15:00,25:15:00\nt2,E3,3,25:20:00,25:20:00\n"
                      "t3,E3,1,07:00:00,07:00:00\nt3,E1,2,07:10:00,07:10:00\n",
}


class PruebaConversion(unittest.TestCase):
    def test_utilidades(self):
        self.assertEqual(normalizar("  Héroes  del  Sur "), "HEROES DEL SUR")
        self.assertEqual(hora_valida("25:10:00"), "01:10")
        self.assertIsNone(hora_valida("xx"))

    def test_convertir_y_cargar(self):
        with tempfile.TemporaryDirectory() as d:
            ruta_zip = os.path.join(d, "gtfs.zip")
            with zipfile.ZipFile(ruta_zip, "w") as z:
                for nombre, contenido in GTFS.items():
                    z.writestr(nombre, contenido)
            e, r, h = convertir(ruta_zip, os.path.join(d, "salida"))
            self.assertEqual((e, r), (3, 2))   # 2 sentidos = 2 rutas
            with open(os.path.join(d, "salida", "estaciones.csv"), encoding="utf-8") as f:
                self.assertEqual([x[0] for x in csv.reader(f)][1:], ["CALLE 26", "HEROES", "RICAURTE"])
            red = Red(os.path.join(d, "salida"))
            self.assertEqual(red.recorrido("B11-1"), ["HEROES", "CALLE 26", "RICAURTE"])
            self.assertEqual(red.proximo_bus("HEROES", "B11-1", "00:00"), "01:10")


if __name__ == "__main__":
    unittest.main()
