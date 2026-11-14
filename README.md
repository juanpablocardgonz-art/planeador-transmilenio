# Planeador TransMilenio

Proyecto final de **Estructuras de Datos y Algoritmos**. Es una app web local donde cualquiera busca una estación, planea un viaje y sabe a qué hora pasa su bus, usando la red real de TransMilenio. Toda la lógica vive en el paquete `motor/`, escrito sin `dict`, `set`, `sorted` ni librerías externas.

## Arrancar la app (un solo comando)

```bash
python app.py
```

Se abre `http://localhost:8000`. Solo se necesita Python 3.9 o superior; no hay que instalar nada.

Otros comandos útiles:

```bash
python -m unittest discover -s pruebas -v      # todas las pruebas (incluye las reglas prohibidas)
python -m rendimiento.medir                     # mide el rendimiento y guarda rendimiento/resultados.json
python conversion/convertir_gtfs.py gtfs.zip datos/   # regenerar los CSV desde el GTFS
```

## Estructura del repositorio

```text
.
├── app.py                  # comando único: arranca el servidor web local
├── motor/                  # TODA la lógica evaluada (reglas estrictas del enunciado)
│   ├── red.py              #   clase Red: el contrato R1–R9 (fachada)
│   ├── tabla_hash.py       #   tabla hash con encadenamiento        R1 e índices
│   ├── avl.py              #   árbol AVL (BST balanceado)            R2, R3, R6, R8
│   ├── lista_doble.py      #   lista doblemente enlazada de paradas  R7
│   ├── pila_cola.py        #   pila y cola sobre arreglos            R9, R10
│   ├── historial.py        #   deshacer/rehacer: 2 pilas + Command    R9
│   ├── planificador.py     #   viaje con máximo 1 transbordo         R5
│   ├── simulacion.py       #   fila de abordaje                      R10
│   ├── ordenamiento.py     #   merge sort + búsqueda binaria         R4 y carga
│   ├── modelo.py           #   clases Estacion y Ruta
│   ├── carga.py            #   lectura de CSV con el módulo csv
│   └── horas.py            #   "HH:MM" <-> minutos
├── frontend/               # servidor HTTP (librería estándar) + HTML/CSS/JS
├── rendimiento/            # R11: genera redes de n, 2n, 4n, 8n y mide
├── conversion/             # GTFS -> estaciones.csv, rutas.csv, horarios.csv
├── datos/                  # los tres CSV generados
├── pruebas/                # unittest: funcionales, restricciones, conversión
└── docs/GUIA_DE_ESTUDIO.md # cómo estudiar el código para la sustentación
```

Cada archivo de `motor/` empieza con un bloque de comentarios que explica la estructura de datos, un dibujo, su complejidad y las alternativas descartadas.

---

## R12 · Decisiones de diseño

**Notación.** n = número de estaciones · L = paradas de una ruta · h = horas de una ruta en una estación · k = cantidad pedida · r = cantidad devuelta · P = pasajeros.

### Resumen

| Req | Operación | Estructura y algoritmo | Complejidad | Alternativa descartada |
|---|---|---|---|---|
| R1 | `estado` | Tabla hash propia (encadenamiento, rehash a 0.75) | O(1) promedio | Búsqueda binaria en arreglo ordenado, O(log n) |
| R2 | `autocompletar` | AVL de estaciones abiertas + recorrido en orden con pila | O(log n + k) | Trie; recorrer todo y filtrar, O(n) |
| R3 | `rango` | El mismo AVL, recorrido en orden acotado | O(log n + r) | Arreglo ordenado (cerrar costaría O(n)) |
| R4 | `proximo_bus` | Hash ruta→parada + búsqueda binaria en horas ordenadas | O(1) + O(log h) | Búsqueda lineal en las horas, O(h) |
| R5 | `viaje` | Grafo estación↔ruta, dos barridos con marcas de versión | O(L_origen + L_destino) | Probar todos los pares de rutas; BFS sobre toda la red |
| R6 | `ranking` | AVL con clave (−buses, nombre), actualizado en cada cambio | O(log n + k) consulta, O(log n) por cambio | Ordenar en cada consulta, O(n log n) |
| R7 | `agregar_parada`, `quitar_parada`, `recorrido` | Lista doblemente enlazada + hash estación→nodo | O(1) + O(log n) del ranking; recorrido O(L) | Arreglo por ruta (insertar en medio, O(L)) |
| R8 | `cerrar`, `reabrir` | Bandera + sacar/meter en los 2 AVL | O(log n) | Filtrar las cerradas en cada consulta |
| R9 | `deshacer`, `rehacer` | Dos pilas de comandos (patrón Command) | O(1) + costo del cambio | Guardar una copia de toda la red en cada cambio |
| R10 | `simular_fila` | Cola FIFO sobre arreglo con índice de frente | O(P + B) | `list.pop(0)`, O(P²) |
| Carga | `Red(carpeta)` | csv.reader + Merge Sort por par (ruta, estación) | O(filas · log h) | Insertion sort, O(h²) por par |

### Detalle por requisito

**R1 · Buscar una estación.** Es la consulta más usada, así que buscamos O(1). Como `dict` está prohibido, implementamos una **tabla hash** (`motor/tabla_hash.py`):
- La función hash es polinomial (h·31 + carácter, método de Horner).
- Las colisiones se resuelven por **encadenamiento**.
- Cuando el factor de carga supera 0.75, la capacidad se **duplica**: el costo es O(n) pero amortizado O(1), como un arreglo dinámico.
- El peor caso es O(n), si todas las claves caen en la misma cubeta.

Devuelve `(existe, abierta)`.

**R2 y R3 · Autocompletar y rango.** Un **árbol AVL** (`motor/avl.py`) guarda los nombres de las estaciones *abiertas*.
- Usamos AVL y no un BST simple porque `estaciones.csv` viene ordenado: un BST simple se degeneraría en una lista, con O(n).
- El recorrido **en orden, iterativo y con pila** empieza en el primer nombre ≥ `prefijo` (o ≥ `desde`) y se detiene al juntar k nombres, al salir del prefijo o al pasar `hasta`.
- Comparamos con dos alternativas:
  - Un **Trie** es O(|prefijo| + k) para R2, pero no resuelve R3 ni R6 y complica "solo abiertas".
  - Un **arreglo ordenado** con búsqueda binaria da las mismas consultas, pero cerrar y reabrir costaría O(n).

`rango` incluye los dos extremos y devuelve `[]` si desde > hasta.

**R4 · Próximo bus.** Al cargar, cada parada (nodo de la lista de su ruta) guarda un **arreglo de minutos ordenado** con Merge Sort y sin repetidos. Merge Sort tiene un mejor caso O(n) si ya viene ordenado.
- La consulta es hash (ruta → nodo) más **búsqueda binaria lower bound**: la primera hora ≥ la pedida.
- Devuelve `"HH:MM"`, o `None` si no existe la estación o la ruta, si la ruta no para ahí, si la estación está cerrada o si no hay más buses ese día.

**R5 · Planear un viaje.** Un BFS clásico minimiza paradas, pero no limita los transbordos a uno. Usamos *encuentro en el medio* (`motor/planificador.py`):
1. Desde el destino caminamos **hacia atrás** cada ruta que para ahí y anotamos, para cada estación T, la menor cantidad de paradas de T al destino.
2. Desde el origen caminamos **hacia adelante** cada ruta. Si aparece el destino, es un viaje directo. Si aparece una T anotada, es un viaje con un transbordo.

Las anotaciones van en arreglos indexados por `estacion.id` con **marcas de versión**: así no hay que reiniciarlos, y cada consulta cuesta O(L_origen + L_destino) sin depender de n.

Reglas que aplicamos:
- En una estación cerrada no se sube, no se baja ni se transborda, pero el bus sí pasa por ella.
- Si dos viajes empatan en paradas, gana el directo, y luego el orden alfabético de las rutas.

Devuelve `(paradas, [(ruta, sube, baja), ...])`, `(0, [])` si origen = destino, o `None`.

**R6 · Ranking.** "Se consulta muy seguido y cambia poco": por eso pagamos el costo al **cambiar** y no al consultar.
- Un AVL guarda `(-buses, nombre)` de las estaciones abiertas. El recorrido en orden da primero las de más buses y desempata alfabéticamente.
- Cerrar, reabrir o editar una ruta saca y vuelve a meter la clave: O(log n).
- *Buses al día* = número de pasadas (horas distintas) sumando todas las rutas de la estación.

Devuelve `[(nombre, buses), ...]`.

**R7 · Editar rutas.** Cada ruta es una **lista doblemente enlazada** más una **tabla hash** estación → nodo. Así insertar o quitar es O(1) y `recorrido(al_reves=True)` usa el enlace `anterior`, también O(L).
- Si `despues_de` es `None`, la parada nueva va al inicio.
- La parada nueva hereda las horas de la parada anterior. Es una decisión nuestra: el bus pasa por ella aproximadamente a la misma hora.
- Devuelve `True` o `False` según si la operación fue válida.

**R8 · Cerrar y reabrir.** Toda modificación pasa por cuatro métodos internos de `Red` (`_cerrar_estacion`, `_abrir_estacion`, `_conectar_parada` y `_desconectar_parada`). Cada uno actualiza **todas** las estructuras: los dos AVL, los índices hash y la lista enlazada. Así nunca quedan inconsistentes. Cerrar una estación que ya estaba cerrada devuelve `False` y no entra al historial.

**R9 · Deshacer y rehacer.** Usamos el **patrón Command** con **dos pilas**.
- Un cambio nuevo se apila en *deshacer* y vacía *rehacer*.
- Un truco de la lista enlazada hace que deshacer sea O(1): al desenlazar un nodo **no se borran sus punteros**. Como las pilas obligan a revertir en orden exacto, al volver a enlazarlo sus vecinos son los mismos de antes.

**R10 · Fila de abordaje.** `simular_fila(llegadas, frecuencia, capacidad)` funciona así:
- Los buses salen en los minutos 0, f, 2f, …
- Quien llega justo en el minuto de salida alcanza ese bus.
- Se sube en orden de llegada; si dos llegan al mismo minuto, sube primero el que va antes en la lista (Merge Sort es estable).
- Devuelve `salidas[i]` = minuto de salida del bus que tomó el pasajero i.

La **cola** usa un arreglo con índice de frente y compactación amortizada. Cuando la cola está vacía, la simulación salta directo al siguiente bus útil, así que el costo es O(P + B).

### Datos y conversión

`conversion/convertir_gtfs.py` lee `stops.txt`, `routes.txt`, `trips.txt` y `stop_times.txt` del GTFS (julio 2021). Decisiones:

- **Nombres:** se pasan a mayúsculas, sin tildes y con los espacios normalizados. Los vagones (`parent_station`) se unen a su estación.
- **Rutas:** cada secuencia distinta de estaciones de una misma ruta comercial es una ruta de un solo sentido (`B11-1`, `B11-2`, …).
- **Horas ≥ 24:** `25:10` pasa a `01:10` (módulo 24) porque el formato exige HH:MM. Esos buses quedan al inicio del día.
- **Repetidos:** las horas repetidas se eliminan. En el motor también se eliminan al cargar, porque el CSV actual traía 1.580 duplicados.

### R11 · Panel de rendimiento

La pestaña **Rendimiento** de la app (y `python -m rendimiento.medir`) copia la red real 2, 4 y 8 veces. Mide cada operación con 2.000 entradas aleatorias y compara la razón *tiempo(2n)/tiempo(n)* con la esperada. En la última medición las 15 operaciones coincidieron. Las O(1) suben un poco al pasar de 4n a 8n por efectos de caché de memoria; la explicación aparece junto a cada gráfica.

### Restricciones del motor

`pruebas/test_restricciones.py` analiza el árbol de sintaxis (`ast`) de cada archivo de `motor/` y falla si encuentra:
- `dict` o `set` (incluidos `{}` y las comprensiones);
- `sorted`, `min`, `max`;
- `.sort()`, `.index()`, `.count()`;
- `x in lista`;
- imports distintos de `csv`, `time` y `random`.

> ✅ **Contrato confirmado contra el enunciado del profesor.** Las firmas de `Red(carpeta)`, `estado`, `autocompletar`, `rango`, `proximo_bus`, `viaje`, `ranking`, `agregar_parada`, `quitar_parada`, `recorrido`, `cerrar`/`reabrir`, `deshacer`/`rehacer` y `simular_fila` (función suelta, no método de `Red`) coinciden exactamente con las que el script del profesor va a llamar. Los **valores de retorno exactos** no los fija el enunciado letra por letra; los formatos elegidos (documentados arriba y en el docstring de cada método) son una decisión nuestra de R12, como pide la rúbrica.

## Forma de trabajo

- Ramas cortas, un Pull Request hacia `main` y revisión de otra persona (ver [CONTRIBUTING.md](./CONTRIBUTING.md)).
- Correr las pruebas antes de integrar.
- Cada integrante debe poder explicar cualquier requisito: ver [docs/GUIA_DE_ESTUDIO.md](./docs/GUIA_DE_ESTUDIO.md) y la distribución en [integrantes.md](./integrantes.md).
