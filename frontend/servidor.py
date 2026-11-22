# =============================================================================
# frontend/servidor.py
# -----------------------------------------------------------------------------
# Servidor web LOCAL de la app. Solo usa la librería estándar de Python
# (http.server y json), así que no hay que instalar nada.
#
# ARQUITECTURA (la regla del proyecto: "la app solo llama al motor"):
#
#   Navegador (HTML + JS)  --fetch /api/...-->  servidor.py  -->  motor.Red
#            ^                                       |
#            +---------------- JSON <----------------+
#
#   - Este archivo NO tiene lógica del sistema: solo traduce peticiones HTTP
#     en llamadas al motor y convierte las respuestas a JSON.
#   - Todas las reglas (estaciones cerradas, transbordos, etc.) viven en
#     motor/. "Una regla del sistema escrita en el front no cuenta."
#
# Cómo arrancar (desde la raíz del repositorio):
#     python app.py
# y abrir http://localhost:8000
# =============================================================================

import json
import os
import random
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from motor import Red, simular_fila  # noqa: E402
from rendimiento import medir as medidor  # noqa: E402

ESTATICOS = os.path.join(RAIZ, "frontend", "estatico")
TIPOS = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml"}

# Una sola Red compartida por toda la app. El candado (lock) evita que dos
# peticiones simultáneas modifiquen la red al mismo tiempo.
RED = None
CANDADO = threading.Lock()


# ----------------------------------------------------------------- utilidades
def _texto(params, nombre, defecto=""):
    """Saca un parámetro de la URL (?nombre=valor) como texto."""
    valores = params.get(nombre)
    return valores[0] if valores else defecto


def _entero(params, nombre, defecto):
    try:
        return int(_texto(params, nombre, str(defecto)))
    except ValueError:
        return defecto


def _estado_red():
    """Resumen para la barra superior de la app."""
    e, a, r, h, d, rh = RED.resumen()
    return {"estaciones": e, "abiertas": a, "rutas": r, "horarios": h,
            "deshacer": d, "rehacer": rh}


# --------------------------------------------------------- API de consultas
# Cada función recibe los parámetros y devuelve algo convertible a JSON.

def api_estado(p):                                   # R1
    nombre = _texto(p, "nombre").strip().upper()
    estado = RED.estado(nombre)              # "ABIERTA", "CERRADA" o "NO EXISTE"
    existe = estado != "NO EXISTE"
    return {"nombre": nombre, "estado": estado, "existe": existe, "abierta": estado == "ABIERTA",
            "rutas": RED.rutas_de(nombre) if existe else [],
            "buses": RED.buses_de(nombre)}


def api_autocompletar(p):                            # R2
    return RED.autocompletar(_texto(p, "prefijo").upper(), _entero(p, "k", 8))


def api_rango(p):                                    # R3
    return RED.rango(_texto(p, "desde").strip().upper(), _texto(p, "hasta").strip().upper())


def api_proximo_bus(p):                              # R4
    est, ruta, hora = _texto(p, "estacion").upper(), _texto(p, "ruta"), _texto(p, "hora")
    return {"proximo": RED.proximo_bus(est, ruta, hora),
            "siguientes": RED.proximos_buses(est, ruta, hora, 6)}


def api_viaje(p):                                    # R5
    resultado = RED.viaje_con_paradas(_texto(p, "origen").upper(), _texto(p, "destino").upper())
    if resultado is None:
        return None
    paradas, tramos = resultado
    return {"paradas": paradas,
            "tramos": [{"ruta": r, "sube": s, "baja": b} for r, s, b in tramos]}


def api_ranking(p):                                  # R6
    return [{"nombre": n, "buses": b} for n, b in RED.ranking(_entero(p, "k", 10))]


def api_recorrido(p):                                # R7
    lista = RED.recorrido(_texto(p, "ruta"), _texto(p, "al_reves") == "1")
    return lista if lista else None   # [] = la ruta no existe (o quedó vacía)


def api_rutas(p):
    return RED.nombres_rutas()


def api_rutas_de(p):
    return RED.rutas_de(_texto(p, "estacion").upper()) or []


def api_resumen(p):
    return _estado_red()


def api_rendimiento(p):                              # R11 (resultado guardado)
    if os.path.exists(medidor.RESULTADOS):
        with open(medidor.RESULTADOS, encoding="utf-8") as f:
            return json.load(f)
    return None


CONSULTAS = {
    "/api/estado": api_estado, "/api/autocompletar": api_autocompletar,
    "/api/rango": api_rango, "/api/proximo_bus": api_proximo_bus,
    "/api/viaje": api_viaje, "/api/ranking": api_ranking,
    "/api/recorrido": api_recorrido, "/api/rutas": api_rutas,
    "/api/rutas_de": api_rutas_de, "/api/resumen": api_resumen,
    "/api/rendimiento": api_rendimiento,
}


# ------------------------------------------------------- API de operaciones
# Estas cambian la red (R7, R8, R9) o hacen cálculos pesados (R10, R11).
# Reciben un JSON en el cuerpo de la petición POST.

def op_agregar_parada(d):
    despues = (d.get("despues_de") or "").upper() or None
    return {"ok": RED.agregar_parada(d.get("ruta", ""), d.get("nueva", "").upper(), despues)}


def op_quitar_parada(d):
    return {"ok": RED.quitar_parada(d.get("ruta", ""), d.get("estacion", "").upper())}


def op_cerrar(d):
    return {"ok": RED.cerrar(d.get("nombre", "").upper())}


def op_reabrir(d):
    return {"ok": RED.reabrir(d.get("nombre", "").upper())}


def op_deshacer(d):
    return {"ok": RED.deshacer()}


def op_rehacer(d):
    return {"ok": RED.rehacer()}


def op_simular(d):                                   # R10
    """
    Genera llegadas aleatorias de hora pico (fuera del motor: aquí sí se
    puede usar random libremente) y llama a simular_fila del motor.
    Las llegadas siguen una forma de "campana": más gente a la mitad del
    periodo, que es lo que pasa en una hora pico real.
    """
    pasajeros = max(1, min(int(d.get("pasajeros", 30000)), 1000000))
    minutos = max(1, int(d.get("minutos", 120)))
    frecuencia = max(1, int(d.get("frecuencia", 3)))
    capacidad = max(1, int(d.get("capacidad", 160)))
    gen = random.Random(int(d.get("semilla", 7)))
    # La interfaz trabaja en MINUTOS (más fácil para una persona) y el motor
    # en SEGUNDOS (contrato oficial): convertimos aquí, en la entrada y la salida.
    llegadas = []
    while len(llegadas) < pasajeros:
        t = gen.gauss(minutos / 2, minutos / 5)
        if 0 <= t <= minutos:          # descartamos las que caen fuera del periodo
            llegadas.append(t)
    llegadas.sort()                    # fuera del motor sí se puede usar sort

    llegadas_s = [round(l * 60) for l in llegadas]
    salidas = [s / 60 for s in simular_fila(llegadas_s, frecuencia * 60, capacidad)]  # <-- el motor

    # Estadísticas para la gráfica (esto es presentación, no lógica).
    esperas = [s - l for s, l in zip(salidas, llegadas)]
    esperas_ordenadas = sorted(esperas)
    buses = len(set(salidas))
    paso = max(1, minutos // 40)
    llegadas_por_franja = [0] * (minutos // paso + 2)
    espera_por_franja = [0.0] * (minutos // paso + 2)
    for l, e in zip(llegadas, esperas):
        i = int(l // paso)
        llegadas_por_franja[i] += 1
        espera_por_franja[i] += e
    franjas = [{"minuto": i * paso, "llegadas": c,
                "espera": (espera_por_franja[i] / c) if c else 0}
               for i, c in enumerate(llegadas_por_franja)]
    return {
        "pasajeros": pasajeros, "buses": buses,
        "espera_promedio": sum(esperas) / len(esperas),
        "espera_mediana": esperas_ordenadas[len(esperas) // 2],
        "espera_p95": esperas_ordenadas[int(len(esperas) * 0.95)],
        "espera_maxima": esperas_ordenadas[-1],
        "ultimo_bus": max(salidas),
        "franjas": franjas,
    }


def op_medir(d):                                     # R11 (nueva medición)
    resultado = medidor.medir(medidor.TAMANOS_PROFESOR)
    medidor.guardar(resultado)
    return resultado


OPERACIONES = {
    "/api/agregar_parada": op_agregar_parada, "/api/quitar_parada": op_quitar_parada,
    "/api/cerrar": op_cerrar, "/api/reabrir": op_reabrir,
    "/api/deshacer": op_deshacer, "/api/rehacer": op_rehacer,
    "/api/simular": op_simular, "/api/medir": op_medir,
}


# ------------------------------------------------------------- servidor HTTP
class Manejador(BaseHTTPRequestHandler):
    def _responder(self, codigo, cuerpo, tipo="application/json; charset=utf-8"):
        datos = cuerpo if isinstance(cuerpo, bytes) else json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in CONSULTAS:
            with CANDADO:
                try:
                    self._responder(200, CONSULTAS[url.path](parse_qs(url.query)))
                except Exception as error:  # error inesperado -> 500 con mensaje
                    self._responder(500, {"error": str(error)})
            return
        # Archivos estáticos (HTML, JS, CSS).
        nombre = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
        ruta = os.path.normpath(os.path.join(ESTATICOS, nombre))
        if not ruta.startswith(ESTATICOS) or not os.path.isfile(ruta):
            self._responder(404, {"error": "no encontrado"})
            return
        with open(ruta, "rb") as f:
            self._responder(200, f.read(), TIPOS.get(os.path.splitext(ruta)[1], "application/octet-stream"))

    def do_POST(self):
        url = urlparse(self.path)
        if url.path not in OPERACIONES:
            self._responder(404, {"error": "no encontrado"})
            return
        largo = int(self.headers.get("Content-Length", 0))
        try:
            datos = json.loads(self.rfile.read(largo) or b"{}")
            with CANDADO:
                respuesta = OPERACIONES[url.path](datos)
                if isinstance(respuesta, dict):
                    respuesta["red"] = _estado_red()
            self._responder(200, respuesta)
        except Exception as error:
            self._responder(400, {"error": str(error)})

    def log_message(self, formato, *args):
        pass  # silenciamos el registro de cada petición en la consola


def iniciar(puerto=8000, carpeta_datos=os.path.join(RAIZ, "datos")):
    global RED
    print(f"Cargando la red desde {carpeta_datos} ...")
    RED = Red(carpeta_datos)
    e, _, r, h, _, _ = RED.resumen()
    print(f"Red lista: {e} estaciones, {r} rutas, {h} horarios.")
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    print(f"Abre http://localhost:{puerto} en tu navegador (Ctrl+C para salir).")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
