# Frontend

App web local: `servidor.py` (librería estándar de Python, `http.server`) expone una API JSON que solo llama al motor, y `estatico/` tiene la interfaz en HTML, CSS y JavaScript sin dependencias (sin CDN, sin npm, sin build). Se arranca con `python app.py` desde la raíz.

## `estatico/`

La interfaz está organizada por **quién la usa**, no por número de requisito, con un archivo de CSS y uno de JS por pantalla:

| Pantalla | Archivos | Requisitos |
|---|---|---|
| Viajar | `viajar.css`, `viajar.js` | R4, R5 |
| Estaciones | `estaciones.css`, `estaciones.js` | R1, R2, R3, R6 |
| Operar la red | `operar.css`, `operar.js` | R7, R8, R9 |
| Hora pico | `hora-pico.css`, `hora-pico.js` | R10 |
| Cómo funciona | `como-funciona.css`, `como-funciona.js` | R11 (+ mapa de requisitos) |

`index.html` solo trae el esqueleto (cabecera, navegación y los cinco `<section>`), `estilos.css` tiene las variables de tema (claro/oscuro automático por `prefers-color-scheme`) y los estilos compartidos, y `comun.js` trae las utilidades que usan todas las pantallas:

- `consultar()` / `operar()`: acceso a la API (`GET`/`POST /api/...`).
- `crearAutocompletar()`: combobox reutilizable sobre `/api/autocompletar` (R2), con teclado y ratón.
- `colorRuta()`: color estable por ruta (hash del nombre completo, no de la primera letra, para no confundir rutas como `B11-1`/`B12-1`/`B74-1`).
- `aviso()`: toast con un botón de acción opcional (por ejemplo "Deshacer").
- `mostrarPanel()` / navegación, `aplicarModoExplicacion()`, `prepararCanvas()`/`ejes()`/`color()` para las gráficas a mano.

Ninguna regla del sistema vive aquí: cerradas, transbordos, ranking, deshacer, etc. siempre los decide `motor/` a través de `servidor.py`. El front solo formatea lo que la API devuelve (sí se vale: mayúsculas/sin tildes de lo que escribe el usuario, formatear horas, calcular "en N min" a partir de la hora que ya devolvió el motor, o la descripción en texto de cada deshacer/rehacer, que el servidor no guarda — solo da el contador).

## API (`servidor.py`)

Sin cambios de superficie en este rediseño: todas las pantallas nuevas reutilizan los endpoints existentes (`CONSULTAS`/`OPERACIONES` en `servidor.py`), llamando a cada estación de una ruta por separado cuando hace falta su estado (como ya hacía la interfaz anterior) en vez de agregar un endpoint por lotes — las rutas tienen decenas de paradas, no miles.
