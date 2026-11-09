# Acuerdos de trabajo

## Flujo de Git

1. Actualizar `main` antes de empezar una tarea.
2. Crear una rama descriptiva, por ejemplo `feature/r1-consulta-estacion` o `test/pruebas-csv`.
3. Mantener cada cambio enfocado en un requisito o tarea.
4. Ejecutar las pruebas relevantes y abrir un Pull Request hacia `main`.
5. Solicitar revisión de al menos un compañero; integrar solo después de resolver comentarios y comprobar que las pruebas pasan.

No hacer `push` directo a `main`. Si GitHub permite configurar protección de rama, activar Pull Requests obligatorios y al menos una aprobación.

## Organización de tareas

- Registrar en el tablero del equipo quién se encarga de cada requisito y quién lo revisa.
- Antes de implementar, acordar las estructuras de datos y anotar ventajas, alternativas descartadas y complejidad.
- Coordinar cambios en el contrato público de `Red` para evitar que frontend, pruebas y motor dependan de firmas distintas.
- Resolver conflictos en conjunto; no sobrescribir cambios de otra persona sin hablarlo.

## Restricciones del motor

El código de `motor/` debe cumplir las restricciones del enunciado del curso. No se deben agregar dependencias externas ni usar atajos prohibidos. Si hay dudas sobre una función de Python o una librería permitida, confirmar con el enunciado y dejar la decisión documentada.

## Antes de integrar

- Verificar que la implementación corresponde al requisito y sus casos límite.
- Ejecutar las pruebas disponibles.
- Describir en el Pull Request qué cambió y cómo se verificó.
