# =============================================================================
# motor/historial.py
# -----------------------------------------------------------------------------
# R9: DESHACER y REHACER con dos PILAS y el PATRÓN COMMAND.
#
# PATRÓN COMMAND: cada cambio a la red se guarda como un OBJETO que sabe
# aplicarse y revertirse:
#     CerrarEstacion   aplicar = cerrar,          revertir = reabrir
#     ReabrirEstacion  aplicar = reabrir,         revertir = cerrar
#     AgregarParada    aplicar = enlazar nodo,    revertir = desenlazar nodo
#     QuitarParada     aplicar = desenlazar nodo, revertir = enlazar nodo
#
# DOS PILAS:
#     deshacer: [c1, c2, c3]   <- tope = el último cambio hecho
#     rehacer:  []
#
#   - Hacer un cambio nuevo:  se apila en 'deshacer' y se VACÍA 'rehacer'
#     (el enunciado: "un cambio nuevo borra lo que había para rehacer").
#   - deshacer(): sacamos de 'deshacer', lo revertimos, y lo pasamos a 'rehacer'.
#   - rehacer():  sacamos de 'rehacer', lo aplicamos, y vuelve a 'deshacer'.
#
# ¿Por qué pila? Porque los cambios se deben revertir en orden inverso (LIFO):
# lo último que se hizo es lo primero que se deshace.
#
# COMPLEJIDAD: apilar/desapilar O(1); el costo total es el de la operación
# que se revierte (cerrar O(log n), agregar parada O(log n), ...).
#
# ALTERNATIVA DESCARTADA: guardar una copia completa de la red en cada cambio
# (snapshot). Deshacer sería trivial, pero cada cambio costaría O(tamaño de la
# red) en tiempo y memoria.
# =============================================================================

from .pila_cola import Pila


# ------------------------------------------------------------------ comandos
class CerrarEstacion:
    def __init__(self, estacion):
        self.estacion = estacion

    def aplicar(self, red):
        red._cerrar_estacion(self.estacion)

    def revertir(self, red):
        red._abrir_estacion(self.estacion)


class ReabrirEstacion:
    def __init__(self, estacion):
        self.estacion = estacion

    def aplicar(self, red):
        red._abrir_estacion(self.estacion)

    def revertir(self, red):
        red._cerrar_estacion(self.estacion)


class AgregarParada:
    # 'nodo' ya trae puestos sus vecinos anterior/siguiente (ver red.py).
    def __init__(self, ruta, nodo):
        self.ruta = ruta
        self.nodo = nodo

    def aplicar(self, red):
        red._conectar_parada(self.ruta, self.nodo)

    def revertir(self, red):
        red._desconectar_parada(self.ruta, self.nodo)


class QuitarParada:
    def __init__(self, ruta, nodo):
        self.ruta = ruta
        self.nodo = nodo

    def aplicar(self, red):
        red._desconectar_parada(self.ruta, self.nodo)

    def revertir(self, red):
        red._conectar_parada(self.ruta, self.nodo)


# ------------------------------------------------------------------ historial
class Historial:
    def __init__(self):
        self._deshacer = Pila()
        self._rehacer = Pila()

    def ejecutar(self, comando, red):
        """Aplica un cambio NUEVO y lo registra."""
        comando.aplicar(red)
        self._deshacer.apilar(comando)
        self._rehacer.vaciar()  # un cambio nuevo invalida lo que había para rehacer

    def deshacer(self, red):
        """Revierte el último cambio. False si no hay nada que deshacer."""
        if self._deshacer.vacia():
            return False
        comando = self._deshacer.desapilar()
        comando.revertir(red)
        self._rehacer.apilar(comando)
        return True

    def rehacer(self, red):
        """Vuelve a aplicar el último cambio deshecho. False si no hay."""
        if self._rehacer.vacia():
            return False
        comando = self._rehacer.desapilar()
        comando.aplicar(red)
        self._deshacer.apilar(comando)
        return True

    def cantidades(self):
        """(cuántos se pueden deshacer, cuántos se pueden rehacer)."""
        return len(self._deshacer), len(self._rehacer)
