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

## 2. Preguntas típicas y dónde está la respuesta

- **¿Por qué una tabla hash para R1 y no búsqueda binaria?** Una cuesta O(1) y la otra O(log n), y R1 es la consulta más frecuente. La desventaja es que la tabla no mantiene orden; por eso R2 y R3 usan el AVL. (`tabla_hash.py`, encabezado)
- **¿Qué pasa si todas las claves caen en la misma cubeta?** El peor caso es O(n). El rehash a 0.75 y una buena función hash lo hacen improbable.
- **¿Por qué AVL y no un BST simple?** `estaciones.csv` viene ordenado: un BST simple quedaría como una lista enlazada y todo costaría O(n).
- **¿Por qué el ranking no se recalcula en cada consulta?** El enunciado dice que se consulta mucho y cambia poco. Pagamos O(log n) por cambio y la consulta cuesta O(log n + k).
- **¿Cómo funciona deshacer de "quitar parada" en O(1)?** El nodo conserva `anterior` y `siguiente`, y la pila garantiza que esos vecinos no han cambiado. (`lista_doble.py`)
- **¿Por qué R5 no es un BFS normal?** BFS minimiza paradas, pero no limita los buses a dos. (`planificador.py`, encabezado)
- **¿Qué es n en cada operación?** Está en la tabla R12 del README y en el panel R11.
- **¿Por qué estas mediciones no son exactamente 1.00 en O(1)?** Por la caché de memoria, el recolector de basura y el ruido del sistema. El panel lo explica junto a cada gráfica.

## 3. Ejercicios para practicar el "cambio sorpresa"

Hagan cada uno sin mirar la solución y corran `python -m unittest discover -s pruebas` al terminar. Recuerden que `test_restricciones` también tiene que pasar.

1. **Estaciones con prefijo, contando cerradas:** `red.contar_prefijo(prefijo)` (pista: el AVL con un contador de tamaño por subárbol daría O(log n)).
2. **Último bus del día:** `red.ultimo_bus(estacion, ruta)` → el último elemento del arreglo de horas, en O(1).
3. **Buses en una franja:** cuántos buses pasan entre dos horas (dos búsquedas binarias, O(log h)).
4. **Ranking inverso:** las k estaciones con menos buses (pista: recorrer el AVL de derecha a izquierda).
5. **Viaje con hora:** que `viaje` diga también a qué hora sale el primer bus después de una hora dada (combina R4 y R5).
6. **Deshacer varias veces:** `red.deshacer_n(k)`.

## 4. Antes de la entrega

- [ ] `integrantes.md` con los usuarios de GitHub y qué requisito hizo cada uno (sigue pendiente de llenar con los datos reales del equipo).
- [ ] Commits de **todos** a lo largo del proyecto (el historial vale 5 puntos). ⚠️ Ahora mismo todos los commits del motor, datos, pruebas, conversión, rendimiento y frontend tienen el mismo autor y el mismo segundo exacto: no cumplen "a lo largo del proyecto". Cada integrante debe hacer sus propios commits reales, desde su cuenta de GitHub, repasando y entendiendo el código que no escribió (lo necesitarán para la sustentación individual).
- [x] Contrato confirmado contra la presentación oficial del profesor: las firmas de R1–R10 y `simular_fila` coinciden exactamente (ver la nota en el README).
- [ ] Correr `convertir_gtfs.py` con el zip real y comparar con `datos/`.
- [ ] Volver a medir el rendimiento en el computador de la presentación.
