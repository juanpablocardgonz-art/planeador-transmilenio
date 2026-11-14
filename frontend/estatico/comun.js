// ============================================================================
// frontend/estatico/comun.js
// ----------------------------------------------------------------------------
// Utilidades COMPARTIDAS por todas las pantallas: acceso a la API, formato,
// un widget de autocompletar reutilizable, colores de ruta, el interruptor
// "Modo explicación" y la navegación entre pantallas.
//
// Aquí NO vive ninguna regla del sistema: solo presentación y llamadas a la
// API (que a su vez solo llama al motor). Cada pantalla tiene su propio
// archivo (viajar.js, estaciones.js, operar.js, hora-pico.js,
// como-funciona.js) que usa estas funciones.
// ============================================================================

const $ = (id) => document.getElementById(id);
const $$ = (selector, raiz = document) => Array.from(raiz.querySelectorAll(selector));

// --------------------------------------------------------------------- API
// GET /api/<ruta>?parametros  ->  JSON
async function consultar(ruta, parametros = {}) {
  const qs = new URLSearchParams(parametros).toString();
  const r = await fetch(`/api/${ruta}?${qs}`);
  return r.json();
}

// POST /api/<ruta> con cuerpo JSON  ->  JSON (incluye el estado de la red)
async function operar(ruta, datos = {}) {
  const r = await fetch(`/api/${ruta}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos),
  });
  const json = await r.json();
  if (json.red) pintarEstadoRed(json.red);
  return json;
}

// ----------------------------------------------------------------- formato
const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (n, d = 0) => Number(n).toLocaleString("es-CO", { maximumFractionDigits: d, minimumFractionDigits: d });

// Hora actual del computador, como "HH:MM" (lo que pide R4).
function horaActualTexto() {
  const ahora = new Date();
  return String(ahora.getHours()).padStart(2, "0") + ":" + String(ahora.getMinutes()).padStart(2, "0");
}

// Minutos desde ahora hasta una hora "HH:MM" que ya devolvió el motor. Es
// solo presentación ("en 7 min"): el motor decide la hora, aquí solo se
// calcula la diferencia con el reloj del navegador.
function minutosDesdeAhora(horaTexto) {
  const [h, m] = horaTexto.split(":").map(Number);
  const ahora = new Date();
  const minutosHora = h * 60 + m;
  const minutosAhora = ahora.getHours() * 60 + ahora.getMinutes();
  let dif = minutosHora - minutosAhora;
  if (dif < 0) dif += 24 * 60; // es la madrugada del día siguiente
  return dif;
}

// ------------------------------------------------------------- color de ruta
// Un color estable por ruta (presentación, no una regla del sistema): un
// hash del NOMBRE COMPLETO elige un color de una paleta fija. Usamos el
// nombre completo y no solo la primera letra porque muchas rutas la
// comparten (B11-1, B12-1, B74-1, ...) y colorear por letra las confundiría.
const PALETA_RUTAS = [
  "#c8102e", "#2b59c3", "#1f7a4d", "#b5691b", "#7b3fb0", "#0f8b8d",
  "#c23a7a", "#5c6bc0", "#8d6e34", "#2e8b8b", "#a4165a", "#476b2e",
];
function colorRuta(nombre) {
  let h = 0;
  for (let i = 0; i < nombre.length; i++) h = (h * 31 + nombre.charCodeAt(i)) >>> 0;
  return PALETA_RUTAS[h % PALETA_RUTAS.length];
}

// --------------------------------------------------------------- toast
// Mensaje flotante temporal, con un botón de acción opcional (por ejemplo
// "Deshacer" después de cerrar una estación).
function aviso(texto, accion) {
  const t = $("toast");
  t.innerHTML = esc(texto) + (accion ? ` <button type="button" id="toast-accion">${esc(accion.texto)}</button>` : "");
  if (accion) $("toast-accion").addEventListener("click", () => { accion.fn(); t.classList.remove("visible"); });
  t.classList.add("visible");
  clearTimeout(aviso.temporizador);
  aviso.temporizador = setTimeout(() => t.classList.remove("visible"), 4200);
}

// ------------------------------------------------- autocompletar (R2)
// Widget reutilizable: convierte un <input> cualquiera en un combobox con
// autocompletado. Usa /api/autocompletar (R2), con teclado y ratón.
function crearAutocompletar(input, opciones = {}) {
  const { minimo = 1, k = 8, onSeleccion = () => {} } = opciones;
  const lista = document.createElement("ul");
  lista.className = "autocompletar-lista";
  lista.hidden = true;
  lista.id = `${input.id}-lista`;
  input.insertAdjacentElement("afterend", lista);
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-controls", lista.id);
  input.autocomplete = "off";

  let activo = -1;
  let temporizador;

  function cerrar() {
    lista.hidden = true;
    lista.innerHTML = "";
    activo = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }

  async function buscar() {
    const texto = input.value.trim().toUpperCase();
    if (texto.length < minimo) return cerrar();
    const nombres = await consultar("autocompletar", { prefijo: texto, k });
    if (!nombres.length) return cerrar();
    lista.innerHTML = nombres.map((n, i) => `<li role="option" id="${lista.id}-${i}" data-valor="${esc(n)}">${esc(n)}</li>`).join("");
    lista.hidden = false;
    input.setAttribute("aria-expanded", "true");
    activo = -1;
  }

  function marcar(items) {
    items.forEach((li, i) => li.classList.toggle("activa", i === activo));
    if (activo >= 0) {
      input.setAttribute("aria-activedescendant", items[activo].id);
      items[activo].scrollIntoView({ block: "nearest" });
    }
  }

  function elegir(valor) {
    input.value = valor;
    cerrar();
    onSeleccion(valor);
  }

  input.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(buscar, 150);
  });
  input.addEventListener("keydown", (e) => {
    const items = $$("li", lista);
    if (lista.hidden || !items.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); activo = Math.min(activo + 1, items.length - 1); marcar(items); }
    else if (e.key === "ArrowUp") { e.preventDefault(); activo = Math.max(activo - 1, 0); marcar(items); }
    else if (e.key === "Enter" && activo >= 0) { e.preventDefault(); elegir(items[activo].dataset.valor); }
    else if (e.key === "Escape") cerrar();
  });
  lista.addEventListener("mousedown", (e) => {
    const li = e.target.closest("li");
    if (li) elegir(li.dataset.valor);
  });
  document.addEventListener("click", (e) => {
    if (e.target !== input && !lista.contains(e.target)) cerrar();
  });
  return { cerrar };
}

// --------------------------------------------------------- "Modo explicación"
// Preferencia de presentación por dispositivo (como el modo claro/oscuro):
// vive en localStorage, no en el servidor.
function modoExplicacionActivo() {
  try { return localStorage.getItem("modo-explicacion") === "1"; } catch { return false; }
}
function aplicarModoExplicacion(activo) {
  document.body.classList.toggle("modo-explicacion", activo);
  const boton = $("btn-modo-explicacion");
  if (boton) boton.setAttribute("aria-pressed", activo ? "true" : "false");
  try { localStorage.setItem("modo-explicacion", activo ? "1" : "0"); } catch { /* localStorage no disponible */ }
}

// -------------------------------------------------------------- navegación
const PANELES = ["viajar", "estaciones", "operar", "horapico", "comofunciona"];
function mostrarPanel(nombre) {
  PANELES.forEach((p) => $(`panel-${p}`)?.classList.toggle("activo", p === nombre));
  $$(".nav-boton").forEach((b) => b.classList.toggle("activa", b.dataset.panel === nombre));
  window.scrollTo(0, 0);
  if (nombre === "estaciones" && typeof alActivarEstaciones === "function") alActivarEstaciones();
  if (nombre === "operar" && typeof alActivarOperar === "function") alActivarOperar();
  if (nombre === "comofunciona" && typeof alActivarComoFunciona === "function") alActivarComoFunciona();
  try { localStorage.setItem("panel-actual", nombre); } catch { /* localStorage no disponible */ }
}

// ------------------------------------------------------------ estado de red
function pintarEstadoRed(r) {
  $("estado-red").textContent = `${fmt(r.abiertas)}/${fmt(r.estaciones)} estaciones abiertas · ${fmt(r.rutas)} rutas`;
  document.dispatchEvent(new CustomEvent("red-actualizada", { detail: r }));
}

// --------------------------------------------------------- ayudas de canvas
// Ajusta el canvas a la densidad de píxeles de la pantalla (se ve nítido) y
// lee un color de las variables CSS (para que las gráficas respeten el tema).
const color = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
function prepararCanvas(c) {
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth, h = c.height / (c.dataset.escalado ? dpr : 1);
  c.dataset.escalado = 1;
  c.width = w * dpr; c.height = h * dpr; c.style.height = h + "px";
  const ctx = c.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  return { ctx, w, h };
}
function ejes(ctx, w, h, m) {
  ctx.strokeStyle = color("--borde"); ctx.lineWidth = 1; ctx.beginPath();
  ctx.moveTo(m.i, m.a); ctx.lineTo(m.i, h - m.b); ctx.lineTo(w - m.d, h - m.b); ctx.stroke();
}

// ---------------------------------------------------------------- arranque
let LISTA_ESTACIONES = [];
let LISTA_RUTAS = [];

async function inicioComun() {
  aplicarModoExplicacion(modoExplicacionActivo());

  pintarEstadoRed(await consultar("resumen"));
  // Catálogo completo de estaciones y rutas: lo usan varias pantallas
  // (datalist de respaldo, listas de operar, etc.).
  LISTA_ESTACIONES = await consultar("rango", { desde: "", hasta: "￿" });
  $("lista-estaciones").innerHTML = LISTA_ESTACIONES.map((n) => `<option value="${esc(n)}">`).join("");
  LISTA_RUTAS = await consultar("rutas");
  $("lista-rutas").innerHTML = LISTA_RUTAS.map((n) => `<option value="${esc(n)}">`).join("");

  $$(".nav-boton").forEach((b) => b.addEventListener("click", () => mostrarPanel(b.dataset.panel)));
  const botonExplicacion = $("btn-modo-explicacion");
  if (botonExplicacion) botonExplicacion.addEventListener("click", () => aplicarModoExplicacion(!modoExplicacionActivo()));

  let inicial = "viajar";
  try { inicial = localStorage.getItem("panel-actual") || "viajar"; } catch { /* localStorage no disponible */ }
  mostrarPanel(PANELES.includes(inicial) ? inicial : "viajar");
}
