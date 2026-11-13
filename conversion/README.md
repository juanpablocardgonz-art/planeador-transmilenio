# Conversión de datos

`convertir_gtfs.py` transforma el GTFS de TransMilenio en `estaciones.csv`, `rutas.csv` y `horarios.csv`:

```bash
python conversion/convertir_gtfs.py ruta/al/gtfs.zip datos/
```

Las decisiones (nombres normalizados, una ruta por sentido, horas ≥ 24 en módulo 24, sin repetidos) están explicadas al inicio del script y en el README principal. `pruebas/test_conversion.py` lo prueba con un GTFS de ejemplo.
