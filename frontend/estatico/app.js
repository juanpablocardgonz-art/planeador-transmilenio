// ============================================================================
// frontend/estatico/app.js
// ----------------------------------------------------------------------------
// Lógica de la INTERFAZ (no del sistema). Cada función:
//   1. lee lo que escribió el usuario,
//   2. llama a la API del servidor (que llama al motor),
//   3. dibuja la respuesta.
// Las reglas (cerradas, transbordos, orden, etc.) las aplica el motor.
// ============================================================================

// ---------------------------------------------------------------- utilidades
const $ = (id) => document.getElementById(id);

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

// Escapa texto para meterlo en HTML sin riesgo.
const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (n, d = 0) => Number(n).toLocaleString("es-CO", { maximumFractionDigits: d, minimumFractionDigits: d });

// Mensaje flotante temporal.
function aviso(texto) {
  const t = $("toast");
  t.textContent = texto;
  t.classList.add("visible");
  clearTimeout(aviso.timer);
  aviso.timer = setTimeout(() => t.classList.remove("visible"), 2600);
}

// Lee un color de las variables CSS (para que las gráficas respeten el tema).
const color = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

// ------------------------------------------------------------------ pestañas
document.querySelectorAll(".pestana").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".pestana").forEach((x) => x.classList.toggle("activa", x === b));
    document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("activo", p.id === `panel-${b.dataset.panel}`));
    if (b.dataset.panel === "ranking") cargarRanking();
    if (b.dataset.panel === "rendimiento") cargarRendimiento();
  })
);

// ------------------------------------------------------------ estado de red
function pintarEstadoRed(r) {
  $("estado-red").textContent =
    `${fmt(r.abiertas)}/${fmt(r.estaciones)} estaciones abiertas · ${fmt(r.rutas)} rutas · ${fmt(r.horarios)} horarios`;
  $("n-deshacer").textContent = r.deshacer;
  $("n-rehacer").textContent = r.rehacer;
  $("btn-deshacer").disabled = r.deshacer === 0;
  $("btn-rehacer").disabled = r.rehacer === 0;
}

async function inicio() {
  pintarEstadoRed(await consultar("resumen"));
  // Llenamos los <datalist> para que el navegador sugiera nombres.
  const todas = await consultar("rango", { desde: "", hasta: "￿" });
  $("lista-estaciones").innerHTML = todas.map((n) => `<option value="${esc(n)}">`).join("");
  const rutas = await consultar("rutas");
  $("lista-rutas").innerHTML = rutas.map((n) => `<option value="${esc(n)}">`).join("");
}

// ======================================================================= R1
$("form-estado").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await consultar("estado", { nombre: $("in-estado").value });
  let html;
  if (!r.existe) html = `<span class="etiqueta mal">No existe</span> <span class="tenue">${esc(r.nombre)}</span>`;
  else
    html = `<span class="etiqueta ${r.abierta ? "ok" : "mal"}">${r.abierta ? "Abierta" : "Cerrada"}</span>
      <b>${esc(r.nombre)}</b><p class="tenue">${fmt(r.buses)} buses al día · rutas: ${r.rutas.map(esc).join(", ")}</p>`;
  $("out-estado").innerHTML = html;
});

// ======================================================================= R2
// Se consulta en cada tecla (con una pequeña espera para no saturar).
let temporizadorAuto;
function autocompletar() {
  clearTimeout(temporizadorAuto);
  temporizadorAuto = setTimeout(async () => {
    const prefijo = $("in-auto").value;
    if (!prefijo) return ($("out-auto").innerHTML = "");
    const lista = await consultar("autocompletar", { prefijo, k: $("in-auto-k").value });
    $("out-auto").innerHTML = lista.length
      ? lista.map((n) => `<li>${esc(n)}</li>`).join("")
      : `<li class="vacio">Sin estaciones abiertas con ese prefijo</li>`;
  }, 120);
}
$("in-auto").addEventListener("input", autocompletar);
$("in-auto-k").addEventListener("input", autocompletar);

// ======================================================================= R3
$("form-rango").addEventListener("submit", async (e) => {
  e.preventDefault();
  const lista = await consultar("rango", { desde: $("in-desde").value, hasta: $("in-hasta").value });
  $("out-rango").innerHTML = lista.length
    ? lista.map((n) => `<li>${esc(n)}</li>`).join("") + `<li class="vacio">${lista.length} estaciones</li>`
    : `<li class="vacio">Ninguna estación abierta en ese rango</li>`;
});

// ======================================================================= R4
// Al elegir la estación, cargamos las rutas que paran ahí en el <select>.
$("in-bus-est").addEventListener("change", async () => {
  const rutas = await consultar("rutas_de", { estacion: $("in-bus-est").value });
  $("in-bus-ruta").innerHTML = rutas.length
    ? rutas.map((r) => `<option>${esc(r)}</option>`).join("")
    : `<option value="">Ninguna ruta para aquí</option>`;
});
$("form-bus").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await consultar("proximo_bus", {
    estacion: $("in-bus-est").value, ruta: $("in-bus-ruta").value, hora: $("in-bus-hora").value,
  });
  $("out-bus").innerHTML = r.proximo
    ? `Próximo bus de <b>${esc($("in-bus-ruta").value)}</b>: <div class="horas">${r.siguientes.map((h) => `<span>${h}</span>`).join("")}</div>`
    : `<span class="etiqueta mal">Sin bus</span> <span class="tenue">No hay más buses ese día, la estación está cerrada o la ruta no para ahí.</span>`;
});

// ======================================================================= R5
$("form-viaje").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await consultar("viaje", { origen: $("in-origen").value, destino: $("in-destino").value });
  if (!r) {
    $("out-viaje").innerHTML = `<span class="etiqueta mal">Sin viaje</span>
      <span class="tenue">No hay viaje directo ni con un transbordo (o alguna estación está cerrada / no existe).</span>`;
    return;
  }
  if (r.tramos.length === 0) return ($("out-viaje").innerHTML = `Ya estás en el destino.`);
  const tipo = r.tramos.length === 1 ? "Directo" : "1 transbordo";
  $("out-viaje").innerHTML =
    `<p><span class="etiqueta ok">${tipo}</span> <b>${r.paradas}</b> paradas</p>` +
    r.tramos.map((t, i) => `<div class="tramo"><span class="ruta-badge">${esc(t.ruta)}</span>
        <div>Sube en <b>${esc(t.sube)}</b><br>${i < r.tramos.length - 1 ? "Cambia en" : "Baja en"} <b>${esc(t.baja)}</b></div></div>`).join("");
});

// ======================================================================= R6
async function cargarRanking() {
  const lista = await consultar("ranking", { k: $("in-rank-k").value });
  const tope = lista.length ? lista[0].buses : 1;
  $("out-rank").innerHTML = lista.map((x, i) => `
    <div class="barra-fila"><span class="pos">${i + 1}</span><span>${esc(x.nombre)}</span>
      <span class="pista"><span class="relleno" style="display:block;width:${(100 * x.buses) / tope}%"></span></span>
      <span class="valor">${fmt(x.buses)}</span></div>`).join("");
}
$("btn-rank").addEventListener("click", cargarRanking);

// ======================================================================= R7
async function verRuta() {
  const ruta = $("in-ruta").value.trim();
  if (!ruta) return;
  const lista = await consultar("recorrido", { ruta, al_reves: $("in-reves").checked ? 1 : 0 });
  if (!lista) return ($("out-recorrido").innerHTML = `<li class="tenue">La ruta no existe.</li>`);
  // Marcamos visualmente las cerradas (consultando R1 de cada una).
  const estados = await Promise.all(lista.map((n) => consultar("estado", { nombre: n })));
  $("out-recorrido").innerHTML = lista.map((n, i) =>
    `<li class="${estados[i].abierta ? "" : "cerrada"}"><button title="Quitar ${esc(n)} de la ruta" data-est="${esc(n)}">${esc(n)}</button></li>`).join("");
}
$("btn-ver-ruta").addEventListener("click", verRuta);
$("in-reves").addEventListener("change", verRuta);
$("out-recorrido").addEventListener("click", async (e) => {
  const est = e.target.dataset?.est;
  if (!est) return;
  const r = await operar("quitar_parada", { ruta: $("in-ruta").value.trim(), estacion: est });
  aviso(r.ok ? `Se quitó ${est}` : "No se pudo quitar");
  verRuta();
});
$("form-agregar").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await operar("agregar_parada", {
    ruta: $("in-ruta").value.trim(), nueva: $("in-nueva").value, despues_de: $("in-despues").value,
  });
  aviso(r.ok ? "Parada agregada" : "No se pudo: revisa que la ruta exista, la estación no esté ya y 'después de' sí esté");
  verRuta();
});

// ======================================================================= R8
async function cambiarEstacion(accion) {
  const nombre = $("in-cerrar").value;
  const r = await operar(accion, { nombre });
  $("out-cerrar").innerHTML = r.ok
    ? `<span class="etiqueta ${accion === "cerrar" ? "mal" : "ok"}">${accion === "cerrar" ? "Cerrada" : "Reabierta"}</span> ${esc(nombre.toUpperCase())}`
    : `<span class="tenue">Sin cambios: no existe o ya estaba ${accion === "cerrar" ? "cerrada" : "abierta"}.</span>`;
}
$("btn-cerrar").addEventListener("click", () => cambiarEstacion("cerrar"));
$("btn-reabrir").addEventListener("click", () => cambiarEstacion("reabrir"));

// ======================================================================= R9
async function historial(accion) {
  const r = await operar(accion);
  $("out-historial").textContent = r.ok ? (accion === "deshacer" ? "Se deshizo el último cambio." : "Se rehízo el cambio.") : "Nada que " + accion + ".";
  if ($("in-ruta").value) verRuta();
}
$("btn-deshacer").addEventListener("click", () => historial("deshacer"));
$("btn-rehacer").addEventListener("click", () => historial("rehacer"));

// ====================================================================== R10
$("form-fila").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("out-fila-stats").innerHTML = `<span class="aviso">Simulando…</span>`;
  const t0 = performance.now();
  const r = await operar("simular", {
    pasajeros: $("in-pasajeros").value, minutos: $("in-minutos").value,
    frecuencia: $("in-frecuencia").value, capacidad: $("in-capacidad").value,
  });
  if (r.error) return ($("out-fila-stats").innerHTML = `<span class="etiqueta mal">${esc(r.error)}</span>`);
  const kpi = (v, l) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`;
  $("out-fila-stats").innerHTML =
    kpi(fmt(r.pasajeros), "pasajeros") + kpi(fmt(r.buses), "buses usados") +
    kpi(fmt(r.espera_promedio, 1) + " min", "espera promedio") + kpi(fmt(r.espera_p95, 1) + " min", "espera p95") +
    kpi(fmt(r.espera_maxima, 1) + " min", "espera máxima") + kpi(fmt(performance.now() - t0) + " ms", "tiempo total");
  dibujarFila(r.franjas);
});

// Gráfica: barras = llegadas por franja; línea = espera promedio.
function dibujarFila(franjas) {
  const c = $("graf-fila");
  const { ctx, w, h } = prepararCanvas(c);
  const m = { i: 48, d: 48, a: 16, b: 28 };
  const maxL = Math.max(...franjas.map((f) => f.llegadas), 1);
  const maxE = Math.max(...franjas.map((f) => f.espera), 1);
  const ancho = (w - m.i - m.d) / franjas.length;
  ejes(ctx, w, h, m);
  ctx.fillStyle = color("--borde");
  franjas.forEach((f, i) => {
    const alto = ((h - m.a - m.b) * f.llegadas) / maxL;
    ctx.fillRect(m.i + i * ancho + 1, h - m.b - alto, Math.max(1, ancho - 2), alto);
  });
  ctx.strokeStyle = color("--acento"); ctx.lineWidth = 2; ctx.beginPath();
  franjas.forEach((f, i) => {
    const x = m.i + i * ancho + ancho / 2, y = h - m.b - ((h - m.a - m.b) * f.espera) / maxE;
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = color("--tenue"); ctx.font = "12px system-ui";
  ctx.fillText(`${fmt(maxL)} llegadas`, 4, m.a + 4);
  ctx.textAlign = "right"; ctx.fillText(`${fmt(maxE, 1)} min espera`, w - 4, m.a + 4);
  ctx.textAlign = "left"; ctx.fillText("minuto 0", m.i, h - 8);
  ctx.textAlign = "right"; ctx.fillText(`minuto ${franjas[franjas.length - 1].minuto}`, w - m.d, h - 8);
}

// ====================================================================== R11
async function cargarRendimiento() {
  const r = await consultar("rendimiento");
  if (!r) {
    $("out-rendimiento").innerHTML = `<p class="tenue">Aún no hay mediciones. Pulsa «Volver a medir».</p>`;
    return;
  }
  pintarRendimiento(r);
}
$("btn-medir").addEventListener("click", async () => {
  $("btn-medir").disabled = true;
  $("out-medir").textContent = "Generando redes de 10.000, 20.000, 40.000 y 80.000 estaciones y midiendo (≈1 min)…";
  const r = await operar("medir");
  $("btn-medir").disabled = false;
  $("out-medir").textContent = r.error ? r.error : `Medición del ${r.fecha}`;
  if (!r.error) pintarRendimiento(r);
});

function pintarRendimiento(r) {
  const filas = r.operaciones.map((op) => `
    <tr><td><b>${op.clave}</b></td><td>${op.requisito}</td><td>${op.esperado}<div class="tenue">${esc(op.que_es_n)}</div></td>
      ${op.tiempos_us.map((t) => `<td class="num">${t >= 1e5 ? fmt(t / 1000) + " ms" : fmt(t, t < 10 ? 2 : 1) + " µs"}</td>`).join("")}
      <td class="num">${fmt(op.pendiente_medida, 2)}</td><td class="num">${fmt(op.pendiente_esperada, 2)}</td>
      <td><span class="etiqueta ${op.coincide ? "ok" : "mal"}">${op.coincide ? "Coincide" : "No coincide"}</span></td></tr>`).join("");
  $("out-rendimiento").innerHTML = `
    <p class="tenue">Medición del ${r.fecha}. Estaciones por red: ${r.estaciones.map((x) => fmt(x)).join(" → ")}.
      Cada tiempo es la mediana de ${r.repeticiones} repeticiones de ${fmt(r.consultas)} consultas.
      «Pendiente» = inclinación de log(tiempo) contra log(n): 0 es plano (O(1), O(log n)), 1 es lineal (O(n)).</p>
    <div class="tabla-scroll"><table class="tabla-rend"><thead><tr><th>Operación</th><th>Req</th><th>Esperado</th>
      ${r.estaciones.map((n) => `<th class="num">${fmt(n)}</th>`).join("")}<th>Pendiente medida</th><th>Esperada</th><th></th></tr></thead>
      <tbody>${filas}</tbody></table></div>
    <div class="leyenda"><span><i style="background:${color("--acento")}"></i>medido</span>
      <span><i style="background:${color("--tenue")}"></i>esperado (escalado al primer punto)</span></div>
    <div class="minis">${r.operaciones.map((op, i) => `
      <div class="mini"><h3><span>${op.clave} <span class="tenue">${op.requisito}</span></span>
        <span class="etiqueta ${op.coincide ? "ok" : "mal"}">${op.esperado}</span></h3>
        <canvas id="mini-${i}" height="110"></canvas><p>${esc(op.explicacion)}</p></div>`).join("")}</div>`;
  r.operaciones.forEach((op, i) => dibujarMini($(`mini-${i}`), r.estaciones, op));
}

// Mini gráfica: tiempo medido vs. curva esperada escalada al primer punto.
const FUNCIONES = {
  "O(1)": () => 1, "O(log n)": (n) => Math.log2(n), "O(n)": (n) => n, "O(n log n)": (n) => n * Math.log2(n),
};
function dibujarMini(c, tamanos, op) {
  const { ctx, w, h } = prepararCanvas(c);
  const m = { i: 8, d: 8, a: 10, b: 10 };
  // Curva esperada: t(n) = t(primera red) * f(n) / f(primera n).
  // En R4 el n real (horas por parada) no crece con la red: se espera plana.
  const f = op.clave === "proximo_bus" ? FUNCIONES["O(1)"] : FUNCIONES[op.esperado];
  const esperado = tamanos.map((n) => (op.tiempos_us[0] * f(n)) / f(tamanos[0]));
  const tope = Math.max(...op.tiempos_us, ...esperado) * 1.1;
  const X = (i) => m.i + ((w - m.i - m.d) * i) / (tamanos.length - 1);
  const Y = (v) => h - m.b - ((h - m.a - m.b) * v) / tope;
  ejes(ctx, w, h, m);
  [[esperado, color("--tenue"), [4, 4]], [op.tiempos_us, color("--acento"), []]].forEach(([serie, col, guion]) => {
    ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.setLineDash(guion); ctx.beginPath();
    serie.forEach((v, i) => (i ? ctx.lineTo(X(i), Y(v)) : ctx.moveTo(X(i), Y(v))));
    ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = col;
    serie.forEach((v, i) => { ctx.beginPath(); ctx.arc(X(i), Y(v), 2.5, 0, 7); ctx.fill(); });
  });
}

// ------------------------------------------------------- ayudas de canvas
// Ajusta el canvas a la densidad de píxeles de la pantalla (se ve nítido).
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

inicio();
