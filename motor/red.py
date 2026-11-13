# =============================================================================
# motor/red.py
# -----------------------------------------------------------------------------
# Clase Red: el CONTRATO del motor que prueba el script del profesor.
#
#   Red(carpeta)                                  carga los 3 CSV
#   red.estado(nombre)                            R1
#   red.autocompletar(prefijo, k)                 R2
#   red.rango(desde, hasta)                       R3
#   red.proximo_bus(estacion, ruta, hora)         R4
#   red.viaje(origen, destino)                    R5
#   red.ranking(k)                                R6
#   red.agregar_parada(ruta, nueva, despues_de)   R7
#   red.quitar_parada(ruta, estacion)             R7
#   red.recorrido(ruta, al_reves=False)           R7
#   red.cerrar(nombre), red.reabrir(nombre)       R8
#   red.deshacer(), red.rehacer()                 R9
#   (simular_fila está en simulacion.py)          R10
#
# ⚠️  Los VALORES DE RETORNO exactos los define el enunciado completo del
#     profesor (la presentación no los trae). Los que usamos aquí están
#     documentados en cada método y en el README: si el enunciado dice otra
#     cosa, solo hay que cambiar la última línea del método correspondiente.
#
# ESTRUCTURAS QUE VIVEN DENTRO DE UNA Red (n = estaciones, R = rutas):
#
#   _estaciones  TablaHash nombre -> Estacion       R1, y para todo lo demás
#   _por_id      list   id -> Estacion              arreglos del planificador
#   _rutas       TablaHash nombre -> Ruta           R4, R7
#   _abiertas    ArbolAVL de nombres abiertos       R2, R3
#   _ranking     ArbolAVL de (-buses, nombre)       R6
#   _historial   dos Pilas de comandos              R9
#   _planificador arreglos por id + marcas          R5
#
# REGLA DE ORO (consistencia, R8): cada cambio pasa por los métodos internos
# _cerrar_estacion, _abrir_estacion, _conectar_parada y _desconectar_parada,
# que actualizan TODAS las estructuras a la vez. Así nunca quedan desfasadas.
# =============================================================================

from .tabla_hash import TablaHash
from .avl import ArbolAVL
from .lista_doble import NodoParada
from .modelo import Estacion, Ruta
from .carga import leer_tabla
from .horas import a_minutos, a_texto
from .ordenamiento import merge_sort, primer_mayor_o_igual, sin_repetidos
from .historial import (Historial, CerrarEstacion, ReabrirEstacion,
                        AgregarParada, QuitarParada)
from .planificador import Planificador


def _unir_ruta(carpeta, archivo):
    """Une carpeta + nombre de archivo sin usar os.path (solo csv/time/random)."""
    if carpeta.endswith("/") or carpeta.endswith("\\"):
        return carpeta + archivo
    return carpeta + "/" + archivo


class Red:
    # =========================================================== CARGA
    def __init__(self, carpeta):
        """
        Carga la red desde 'carpeta' (debe tener estaciones.csv, rutas.csv y
        horarios.csv).

        Complejidad: O(E + P + H log h)
          E = estaciones, P = filas de rutas.csv, H = filas de horarios.csv,
          h = horarios de un mismo par (ruta, estación).
        """
        self._estaciones = TablaHash()
        self._por_id = []
        self._rutas = TablaHash()
        self._nombres_rutas = []          # nombres de rutas, ordenados
        self._abiertas = ArbolAVL()
        self._ranking = ArbolAVL()
        self._historial = Historial()
        self._total_horarios = 0

        self._cargar_estaciones(_unir_ruta(carpeta, "estaciones.csv"))
        self._cargar_rutas(_unir_ruta(carpeta, "rutas.csv"))
        self._cargar_horarios(_unir_ruta(carpeta, "horarios.csv"))

        # Al final, todas las estaciones están abiertas: entran al ranking
        # con su número de buses ya calculado.
        for est in self._por_id:
            self._ranking.insertar((-est.buses, est.nombre))

        self._planificador = Planificador(len(self._por_id))

    # ---------------------------------------------------------- estaciones
    def _cargar_estaciones(self, archivo):
        for fila in leer_tabla(archivo, ["nombre"]):
            nombre = fila[0]
            # Los nombres no deberían repetirse, pero si pasa, no duplicamos.
            if not self._estaciones.contiene(nombre):
                est = Estacion(nombre, len(self._por_id))
                self._estaciones.insertar(nombre, est)
                self._por_id.append(est)
                self._abiertas.insertar(nombre)

    # ---------------------------------------------------------- rutas
    def _cargar_rutas(self, archivo):
        # 1. AGRUPAR las filas por ruta: TablaHash nombre_ruta -> lista de
        #    (orden, estacion). Guardamos también el orden de aparición.
        grupos = TablaHash()
        nombres = []
        for ruta, orden, estacion in leer_tabla(archivo, ["ruta", "orden", "estacion"]):
            grupo = grupos.buscar(ruta)
            if grupo is None:
                grupo = []
                grupos.insertar(ruta, grupo)
                nombres.append(ruta)
            grupo.append((int(orden), estacion))

        # 2. Para cada ruta: ORDENAR sus paradas por 'orden' (Merge Sort, por
        #    si el CSV no viene ordenado) y construir la lista enlazada.
        for nombre_ruta in nombres:
            paradas = merge_sort(grupos.buscar(nombre_ruta), lambda p: p[0])
            ruta = Ruta(nombre_ruta)
            for _, nombre_est in paradas:
                est = self._estaciones.buscar(nombre_est)
                # Ignoramos estaciones desconocidas o repetidas en la misma ruta.
                if est is None or ruta.indice.contiene(nombre_est):
                    continue
                nodo = NodoParada(est, [])
                ruta.paradas.agregar_al_final(nodo)
                ruta.indice.insertar(nombre_est, nodo)
                est.rutas.insertar(nombre_ruta, ruta)
            self._rutas.insertar(nombre_ruta, ruta)

        # 3. Lista de nombres de rutas ORDENADA (para mostrar en la app).
        self._nombres_rutas = merge_sort(nombres)

    # ---------------------------------------------------------- horarios
    def _cargar_horarios(self, archivo):
        # 1. Repartimos cada hora en el nodo (ruta, estación) que le toca.
        ruta_anterior = None   # pequeña caché: las filas de una misma ruta
        ruta = None            # suelen venir seguidas
        for nombre_ruta, nombre_est, hora in leer_tabla(archivo, ["ruta", "estacion", "hora"]):
            if nombre_ruta != ruta_anterior:
                ruta = self._rutas.buscar(nombre_ruta)
                ruta_anterior = nombre_ruta
            if ruta is None:
                continue  # ruta desconocida
            nodo = ruta.indice.buscar(nombre_est)
            if nodo is None:
                continue  # la ruta no para en esa estación
            try:
                nodo.horas.append(a_minutos(hora))
            except ValueError:
                continue  # hora mal escrita: la ignoramos

        # 2. ORDENAMOS cada arreglo de horas (para la búsqueda binaria de R4)
        #    y quitamos repetidos (el CSV real trae ~1.580 duplicados).
        #    Además sumamos los buses de cada estación (para R6).
        for ruta in self._rutas.valores():
            for nodo in ruta.paradas.recorrer():
                nodo.horas = sin_repetidos(merge_sort(nodo.horas))
                nodo.estacion.buses += len(nodo.horas)
                self._total_horarios += len(nodo.horas)

    # ======================================================== R1 ESTADO
    def estado(self, nombre):
        """
        R1. ¿Existe la estación y está abierta?
        Devuelve una tupla (existe, abierta):
            (False, False) -> no existe
            (True, True)   -> existe y está abierta
            (True, False)  -> existe pero está cerrada
        Estructura: tabla hash. Complejidad: O(1) promedio.
        """
        est = self._estaciones.buscar(nombre)
        if est is None:
            return (False, False)
        return (True, est.abierta)

    # ================================================== R2 AUTOCOMPLETAR
    def autocompletar(self, prefijo, k):
        """
        R2. Hasta k estaciones ABIERTAS que empiezan por 'prefijo', en orden
        alfabético. Devuelve una lista de nombres.
        Estructura: AVL de abiertas. Complejidad: O(log n + k).
        """
        if k <= 0:
            return []
        # Las palabras que empiezan por "CAL" son justamente las >= "CAL" que
        # todavía empiezan por "CAL": empezamos en "CAL" y paramos al primer
        # nombre que ya no tenga ese prefijo.
        return self._abiertas.desde(prefijo, k, lambda nombre: nombre.startswith(prefijo))

    # ========================================================= R3 RANGO
    def rango(self, desde, hasta):
        """
        R3. Estaciones ABIERTAS con desde <= nombre <= hasta (ambos incluidos),
        en orden alfabético. Si desde > hasta, lista vacía.
        Estructura: AVL de abiertas. Complejidad: O(log n + r), r = resultado.
        """
        return self._abiertas.rango(desde, hasta)

    # ================================================== R4 PRÓXIMO BUS
    def proximo_bus(self, estacion, ruta, hora):
        """
        R4. Hora ("HH:MM") del primer bus de 'ruta' que pasa por 'estacion' a
        la hora dada o después. None si: la estación o la ruta no existen, la
        ruta no para ahí, la estación está cerrada o no hay más buses ese día.
        Estructura: tabla hash (ruta -> nodo) + búsqueda binaria sobre el
        arreglo ordenado de horas. Complejidad: O(1) + O(log h).
        """
        siguientes = self.proximos_buses(estacion, ruta, hora, 1)
        if siguientes is None or len(siguientes) == 0:
            return None
        return siguientes[0]

    def proximos_buses(self, estacion, ruta, hora, cantidad):
        """Extra para la app: las próximas 'cantidad' horas (lista de "HH:MM")."""
        est = self._estaciones.buscar(estacion)
        obj_ruta = self._rutas.buscar(ruta)
        if est is None or obj_ruta is None or not est.abierta:
            return None
        nodo = obj_ruta.indice.buscar(estacion)
        if nodo is None:
            return None
        try:
            minuto = a_minutos(hora)
        except ValueError:
            return None
        # Búsqueda binaria: primera hora >= minuto.
        i = primer_mayor_o_igual(nodo.horas, minuto)
        resultado = []
        while i < len(nodo.horas) and len(resultado) < cantidad:
            resultado.append(a_texto(nodo.horas[i]))
            i += 1
        return resultado

    # ======================================================== R5 VIAJE
    def viaje(self, origen, destino):
        """
        R5. Viaje directo o con un transbordo con menos paradas.
        Devuelve (total_paradas, tramos) o None si no hay viaje.
          tramos = [(ruta, sube_en, baja_en)]                       directo
                 = [(ruta1, origen, transbordo), (ruta2, transbordo, destino)]
        Ver planificador.py. Complejidad: O(L_origen + L_destino).
        """
        o = self._estaciones.buscar(origen)
        d = self._estaciones.buscar(destino)
        if o is None or d is None:
            return None
        return self._planificador.viaje(o, d)

    # ======================================================== R6 RANKING
    def ranking(self, k):
        """
        R6. Las k estaciones ABIERTAS por donde pasan más buses al día.
        Devuelve lista de (nombre, buses), de más a menos buses; si empatan,
        en orden alfabético.
        Estructura: AVL con clave (-buses, nombre). Al negar los buses, el
        recorrido en orden (de menor a mayor) da primero las de MÁS buses.
        El árbol se actualiza solo cuando algo cambia (cerrar, reabrir,
        editar ruta): O(log n) por cambio. Consulta: O(log n + k).
        """
        resultado = []
        for clave in self._ranking.desde(None, k):
            resultado.append((clave[1], -clave[0]))
        return resultado

    # ================================================== R7 EDITAR RUTAS
    def agregar_parada(self, ruta, nueva, despues_de):
        """
        R7. Inserta la estación 'nueva' justo después de 'despues_de' en 'ruta'.
        Si despues_de es None o "", la inserta al inicio de la ruta.
        Devuelve True si se hizo, False si no era válido (ruta o estación
        inexistentes, 'nueva' ya está en la ruta, 'despues_de' no está).

        Horarios de la parada nueva (decisión del grupo): el bus pasa por ella
        a las mismas horas que por la parada anterior ('despues_de'). Así
        próximo_bus funciona y el ranking cuenta esos buses.

        Complejidad: O(1) promedio (hash + lista enlazada) + O(log n) para
        actualizar el ranking.
        """
        obj_ruta = self._rutas.buscar(ruta)
        est = self._estaciones.buscar(nueva)
        if obj_ruta is None or est is None or obj_ruta.indice.contiene(nueva):
            return False
        if despues_de is None or despues_de == "":
            # Al inicio: sin anterior; el siguiente es la cabeza actual.
            anterior = None
            siguiente = obj_ruta.paradas.cabeza
            horas = siguiente.horas if siguiente is not None else []
        else:
            anterior = obj_ruta.indice.buscar(despues_de)
            if anterior is None:
                return False
            siguiente = anterior.siguiente
            horas = anterior.horas  # se comparte el arreglo (no se modifica)
        nodo = NodoParada(est, horas, anterior, siguiente)
        self._historial.ejecutar(AgregarParada(obj_ruta, nodo), self)
        return True

    def quitar_parada(self, ruta, estacion):
        """
        R7. Quita 'estacion' del recorrido de 'ruta'. True si se hizo.
        Complejidad: O(1) promedio + O(log n) del ranking.
        """
        obj_ruta = self._rutas.buscar(ruta)
        if obj_ruta is None:
            return False
        nodo = obj_ruta.indice.buscar(estacion)
        if nodo is None:
            return False
        self._historial.ejecutar(QuitarParada(obj_ruta, nodo), self)
        return True

    def recorrido(self, ruta, al_reves=False):
        """
        R7. Lista de nombres de estaciones de la ruta, en su sentido o al
        revés. None si la ruta no existe. Complejidad: O(L).
        """
        obj_ruta = self._rutas.buscar(ruta)
        if obj_ruta is None:
            return None
        nombres = []
        for nodo in obj_ruta.paradas.recorrer(al_reves):
            nombres.append(nodo.estacion.nombre)
        return nombres

    # ================================================ R8 CERRAR / REABRIR
    def cerrar(self, nombre):
        """R8. Cierra la estación. False si no existe o ya estaba cerrada. O(log n)."""
        est = self._estaciones.buscar(nombre)
        if est is None or not est.abierta:
            return False
        self._historial.ejecutar(CerrarEstacion(est), self)
        return True

    def reabrir(self, nombre):
        """R8. Reabre la estación. False si no existe o ya estaba abierta. O(log n)."""
        est = self._estaciones.buscar(nombre)
        if est is None or est.abierta:
            return False
        self._historial.ejecutar(ReabrirEstacion(est), self)
        return True

    # =============================================== R9 DESHACER / REHACER
    def deshacer(self):
        """R9. Deshace el último cambio. False si no había nada."""
        return self._historial.deshacer(self)

    def rehacer(self):
        """R9. Rehace el último cambio deshecho. False si no había nada."""
        return self._historial.rehacer(self)

    # ============================================ CAMBIOS INTERNOS (R7-R9)
    # Estos son los ÚNICOS métodos que modifican la red. Los comandos del
    # historial los llaman tanto al aplicar como al revertir.

    def _cerrar_estacion(self, est):
        est.abierta = False
        self._abiertas.eliminar(est.nombre)               # sale de R2/R3
        self._ranking.eliminar((-est.buses, est.nombre))  # sale de R6

    def _abrir_estacion(self, est):
        est.abierta = True
        self._abiertas.insertar(est.nombre)
        self._ranking.insertar((-est.buses, est.nombre))

    def _conectar_parada(self, ruta, nodo):
        est = nodo.estacion
        ruta.paradas.enlazar(nodo)                   # lista enlazada
        ruta.indice.insertar(est.nombre, nodo)       # índice hash de la ruta
        est.rutas.insertar(ruta.nombre, ruta)        # rutas de la estación
        self._sumar_buses(est, len(nodo.horas))      # ranking

    def _desconectar_parada(self, ruta, nodo):
        est = nodo.estacion
        ruta.paradas.desenlazar(nodo)
        ruta.indice.eliminar(est.nombre)
        est.rutas.eliminar(ruta.nombre)
        self._sumar_buses(est, -len(nodo.horas))

    def _sumar_buses(self, est, delta):
        """Cambia los buses de una estación manteniendo el ranking ordenado."""
        if delta == 0:
            return
        # La clave del AVL depende de 'buses': hay que sacarla, cambiarla y
        # volverla a meter (no se puede modificar en su sitio).
        if est.abierta:
            self._ranking.eliminar((-est.buses, est.nombre))
        est.buses += delta
        if est.abierta:
            self._ranking.insertar((-est.buses, est.nombre))

    # ======================================================= EXTRAS (app)
    def nombres_rutas(self):
        """Todos los nombres de ruta en orden alfabético (para la app)."""
        return list(self._nombres_rutas)

    def rutas_de(self, nombre):
        """Rutas que paran en una estación, ordenadas. None si no existe."""
        est = self._estaciones.buscar(nombre)
        if est is None:
            return None
        return merge_sort(est.rutas.claves())

    def buses_de(self, nombre):
        """Buses al día que pasan por la estación. None si no existe."""
        est = self._estaciones.buscar(nombre)
        return None if est is None else est.buses

    def resumen(self):
        """(estaciones, abiertas, rutas, horarios, deshacibles, rehacibles)."""
        deshacer, rehacer = self._historial.cantidades()
        return (len(self._por_id), len(self._abiertas), len(self._rutas),
                self._total_horarios, deshacer, rehacer)
