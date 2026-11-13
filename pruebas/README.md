# Pruebas

```bash
python -m unittest discover -s pruebas -v
```

- `test_motor.py`: R1–R10 sobre `red_mini/` (respuestas calculables a mano) y carga de la red real.
- `test_restricciones.py`: revisa con `ast` que `motor/` no use nada prohibido.
- `test_conversion.py`: el script GTFS → CSV con un GTFS de ejemplo.

El rendimiento (R11) está en `rendimiento/`.
