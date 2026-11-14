# Guía de estudio para la sustentación

En la sustentación cada persona responde sobre un requisito **que no hizo** y hace un cambio en vivo. Esta guía conecta los temas del semestre con el código, en el orden en que conviene leerlo.

## 1. Orden de lectura sugerido

| Paso | Archivo | Tema del curso | Qué entender |
|---|---|---|---|
| 1 | `motor/horas.py` | Representación de datos | Por qué guardamos minutos (enteros) y no texto |
| 2 | `motor/ordenamiento.py` | Merge Sort, búsqueda binaria | Divide y vencerás, estabilidad, *lower bound*, mejor caso O(n) |
| 3 | `motor/tabla_hash.py` | Tablas hash | Función hash, colisiones, encadenamiento, factor de carga, rehash amortizado |
| 4 | `motor/pila_cola.py` | Pilas y colas | LIFO y FIFO; por qué `pop(0)` es O(n) |
| 5 | `motor/lista_doble.py` | Listas enlazadas | Insertar y quitar en O(1); por qué no se borran los punteros |
| 6 | `motor/avl.py` | BST y árboles balanceados | Rotaciones, altura O(log n), recorrido en orden con pila |
| 7 | `motor/modelo.py` | Grafos | Listas de adyacencia: estación ↔ ruta |
| 8 | `motor/historial.py` | Pilas + patrón Command | Deshacer y rehacer en orden |
| 9 | `motor/planificador.py` | Grafos, BFS de profundidad 2 | Encuentro en el medio, marcas de versión |
| 10 | `motor/simulacion.py` | Colas, simulación de eventos | O(P + B) |
| 11 | `motor/red.py` | Diseño modular | Cómo se mantienen consistentes todas las estructuras |

## 2. Las seis preguntas de la sustentación (3.0 de la nota)

El profesor escoge **quién** responde, sin importar quién hizo el requisito. Todos deben poder contestar las seis. Para cada una preparen: qué usamos, por qué, por qué no la alternativa, qué pasaría si cambiáramos X por Y, la O grande y qué es n.

| Pregunta | Tema | Archivos | Alternativas que hay que saber defender |
|---|---|---|---|
| 1 | R1–R3: la estructura que guarda las estaciones | `tabla_hash.py`, `avl.py` | Trie, arreglo ordenado + búsqueda binaria, BST sin balancear |
| 2 | R4: el próximo bus entre cientos de horarios | `ordenamiento.py`, `red.py` (`proximos_buses`) | búsqueda lineal, árbol de horarios |
| 3 | R5: el viaje con menos paradas y el transbordo | `planificador.py` | BFS/Dijkstra sobre toda la red, probar todas las parejas de rutas |
| 4 | R6 y R8: el ranking al día al cerrar o reabrir | `avl.py`, `red.py` (`_sumar_buses`, `_cerrar_estacion`) | ordenar en cada consulta, heap, arreglo ordenado |
| 5 | R7 y R9: el recorrido de una ruta, deshacer y rehacer | `lista_doble.py`, `historial.py` | arreglo por ruta, guardar copias de la red |
| 6 | R10 y R11: ordenar llegadas, la fila y el panel | `simulacion.py`, `pila_cola.py`, `rendimiento/medir.py` | `pop(0)`, Quick Sort (no estable), medir con duplicación vs. pendiente log-log |

## 3. Preguntas típicas y dónde está la respuesta

- **¿Por qué una tabla hash para R1 y no búsqueda binaria?** Una cuesta O(1) y la otra O(log n), y R1 es la consulta más frecuente. La desventaja es que la tabla no mantiene orden; por eso R2 y R3 usan el AVL. (`tabla_hash.py`, encabezado)
- **¿Qué pasa si todas las claves caen en la misma cubeta?** El peor caso es O(n). El rehash a 0.75 y una buena función hash lo hacen improbable.
- **¿Por qué AVL y no un BST simple?** `estaciones.csv` viene ordenado: un BST simple quedaría como una lista enlazada y todo costaría O(n).
- **¿Por qué el ranking no se recalcula en cada consulta?** El enunciado dice que se consulta mucho y cambia poco. Pagamos O(log n) por cambio y la consulta cuesta O(log n + k).
- **¿Cómo funciona deshacer de "quitar parada" en O(1)?** El nodo conserva `anterior` y `siguiente`, y la pila garantiza que esos vecinos no han cambiado. (`lista_doble.py`)
- **¿Por qué R5 no es un BFS normal?** BFS minimiza paradas, pero no limita los buses a dos. (`planificador.py`, encabezado)
- **¿Qué es n en cada operación?** Está en la tabla R12 del README y en el panel R11.
- **¿Por qué la pendiente de una operación O(1) no es exactamente 0?** Por la caché de memoria, el recolector de basura y el ruido del sistema. Por eso se usa la mediana de varias repeticiones. El panel lo explica junto a cada gráfica.
- **¿Por qué `hash()` y no su propia función hash?** Lo medimos: la polinomial en Python era el 40 % de la carga. `hash()` hace el mismo cálculo O(L) en C y Python lo guarda dentro del texto. La tabla (cubetas, colisiones, rehash) sigue siendo nuestra.

## 4. Ejercicios para practicar el "cambio sorpresa"

Hagan cada uno sin mirar la solución y corran `python -m unittest discover -s pruebas` al terminar. Recuerden que `test_restricciones` también tiene que pasar.

1. **Estaciones con prefijo, contando cerradas:** `red.contar_prefijo(prefijo)` (pista: el AVL con un contador de tamaño por subárbol daría O(log n)).
2. **Último bus del día:** `red.ultimo_bus(estacion, ruta)` → el último elemento del arreglo de horas, en O(1).
3. **Buses en una franja:** cuántos buses pasan entre dos horas (dos búsquedas binarias, O(log h)).
4. **Ranking inverso:** las k estaciones con menos buses (pista: recorrer el AVL de derecha a izquierda).
5. **Viaje con hora:** que `viaje` diga también a qué hora sale el primer bus después de una hora dada (combina R4 y R5).
6. **Deshacer varias veces:** `red.deshacer_n(k)`.

## 5. Antes de la entrega

- [ ] `integrantes.md` con los usuarios de GitHub y qué requisito hizo cada uno.
- [ ] Commits de **todos** a lo largo del proyecto (el historial vale 5 puntos).
- [ ] El repositorio público (o con acceso de lectura para el profesor) y el trabajo integrado en `main`.
- [ ] Último commit antes del 21 de noviembre de 2026, 23:59.
- [ ] Correr `convertir_gtfs.py` con el zip real y comparar con `datos/`.
- [ ] Volver a medir el rendimiento en el computador de la presentación.
