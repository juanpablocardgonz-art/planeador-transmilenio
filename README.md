# Planeador TransMilenio

Proyecto académico de un planeador de viajes para la red de TransMilenio. El objetivo es construir y sustentar el motor usando estructuras de datos y algoritmos propios, no solo entregar una interfaz que funcione.

## Estructura inicial

```text
.
├── conversion/       # Herramientas para preparar los CSV de entrada
├── datos/            # estaciones.csv, rutas.csv y horarios.csv
├── frontend/         # Interfaz de usuario
├── motor/            # Estructuras de datos, algoritmos y clase Red
├── pruebas/          # Pruebas funcionales y de rendimiento
├── CONTRIBUTING.md   # Acuerdos para trabajar en equipo
└── integrantes.md    # Integrantes y distribución del trabajo
```

El motor debe leer los tres CSV indicados, sin depender de una red específica ni de datos codificados a mano.

## Requisitos del motor

El contrato del proyecto incluye consultas de estaciones, autocompletado, rangos, próximo bus, planeación de viajes, ranking, edición de recorridos, cierre y reapertura de estaciones, deshacer/rehacer y simulación de filas. Las firmas exactas se deben contrastar con el enunciado del profesor antes de implementarlas.

Dentro de `motor/`, respetar las restricciones del enunciado. Entre otras: no usar `dict`, `set`, `sorted()`, `.sort()`, `min()`/`max()` sobre colecciones, `in lista`, `.index()`, `.count()` ni módulos/paquetes prohibidos. Consultar el enunciado completo para la lista definitiva. Las listas (`list`) sí están permitidas para implementar las estructuras.

## Forma de trabajo sugerida

- Antes de programar un requisito, acordar responsable, estructura elegida y complejidad esperada.
- Trabajar en ramas cortas y abrir un Pull Request hacia `main`; no subir cambios directamente a `main`.
- Pedir revisión de al menos otra persona y ejecutar las pruebas antes de integrar.
- Coordinar cambios a las firmas públicas de `Red` antes de hacerlos.
- No subir datos personales, credenciales ni archivos locales del entorno.

Los pasos para colaborar están en [CONTRIBUTING.md](./CONTRIBUTING.md) y el estado de la distribución en [integrantes.md](./integrantes.md).
