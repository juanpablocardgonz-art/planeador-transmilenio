# Datos de entrada

Los tres CSV que lee el motor, generados desde el GTFS de TransMilenio (julio 2021):

| Archivo | Columnas | Filas |
|---|---|---|
| `estaciones.csv` | `nombre` | 147 |
| `rutas.csv` | `ruta, orden, estacion` | 1.927 (181 rutas) |
| `horarios.csv` | `ruta, estacion, hora` | 140.492 (1.580 repetidas, que el motor descarta) |

Nombres en mayúsculas, sin tildes, sin repetidos; cada ruta va en un solo sentido; horas `HH:MM`.
Para regenerarlos: `python conversion/convertir_gtfs.py gtfs.zip datos/`.
