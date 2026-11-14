// ============================================================================
// frontend/estatico/como-funciona.js
// ----------------------------------------------------------------------------
// Pantalla "Cómo funciona": el panel de rendimiento (R11) y un mapa de
// "requisito → dónde está en la app", pensados para el profesor y la
// sustentación. El interruptor "Modo explicación" (comun.js) es global y
// revela las tarjetas "Bajo el capó" en TODAS las pantallas, no solo en esta.
// ============================================================================

// --------------------------------------------------------------------- R11
async function cargarRendimiento() {
  const r = await consultar("rendimiento");
  if (!r) {
    $("out-rendimiento").innerHTML = `<p class="vacio">Aún no hay mediciones. Pulsa «Volver a medir».</p>`;
    return;
  }
  pintarRendimiento(r);
}

function cablearBotonMedir() {
  $("btn-medir").addEventListener("click", async () => {
    $("btn-medir").disabled = true;
    $("out-medir").textContent = "Midiendo con redes de n, 2n, 4n y 8n… (unos 15 s)";
    const r = await operar("medir");
    $("btn-medir").disabled = false;
    $("out-medir").textContent = r.error ? r.error : `Medición del ${r.fecha}`;
    if (!r.error) pintarRendimiento(r);
  });
}

function pintarRendimiento(r) {
  const filas = r.operaciones.map((op) => `
    <tr><td><b>${op.clave}</b></td><td>${op.requisito}</td><td>${op.esperado}<div class="tenue">${esc(op.que_es_n)}</div></td>
      ${op.tiempos_us.map((t) => `<td class="num">${t >= 1e5 ? fmt(t / 1000) + " ms" : fmt(t, t < 10 ? 2 : 1) + " µs"}</td>`).join("")}
      <td class="num">×${fmt(op.razon_medida, 2)}</td><td class="num">×${fmt(op.razon_esperada, 2)}</td>
      <td><span class="etiqueta ${op.coincide ? "ok" : "mal"}">${op.coincide ? "Coincide" : "No coincide"}</span></td></tr>`).join("");
  $("out-rendimiento").innerHTML = `
    <p class="tenue">Medición del ${r.fecha}. Estaciones por red: ${r.estaciones.map((x) => fmt(x)).join(" → ")}.
      «Razón» = tiempo(2n) / tiempo(n), promedio de cada duplicación.</p>
    <div class="tabla-scroll"><table class="tabla-rend"><thead><tr><th>Operación</th><th>Req</th><th>Esperado</th>
      ${r.factores.map((f) => `<th>${f === 1 ? "n" : f + "n"}</th>`).join("")}<th>Razón medida</th><th>Esperada</th><th></th></tr></thead>
      <tbody>${filas}</tbody></table></div>
    <div class="leyenda"><span><i style="background:${color("--acento")}"></i>medido</span>
      <span><i style="background:${color("--tenue")}"></i>esperado (escalado al primer punto)</span></div>
    <div class="minis">${r.operaciones.map((op, i) => `
      <div class="mini"><h3><span>${op.clave} <span class="tenue">${op.requisito}</span></span>
        <span class="etiqueta ${op.coincide ? "ok" : "mal"}">${op.esperado}</span></h3>
        <canvas id="mini-${i}" height="110"></canvas><p>${esc(op.explicacion)}</p></div>`).join("")}</div>`;
  r.operaciones.forEach((op, i) => dibujarMini($(`mini-${i}`), r.factores, op));
}

// Mini gráfica: tiempo medido vs. curva esperada escalada al primer punto.
const FUNCIONES_CRECIMIENTO = {
  "O(1)": () => 1, "O(log n)": (n) => Math.log2(n), "O(n)": (n) => n, "O(n log n)": (n) => n * Math.log2(n),
};
function dibujarMini(c, factores, op) {
  const { ctx, w, h } = prepararCanvas(c);
  const m = { i: 8, d: 8, a: 10, b: 10 };
  const base = 1000; // tamaño de referencia (solo importa la forma de la curva)
  const f = FUNCIONES_CRECIMIENTO[op.esperado];
  const esperado = factores.map((x) => (op.tiempos_us[0] * f(base * x)) / f(base));
  const tope = Math.max(...op.tiempos_us, ...esperado) * 1.1;
  const X = (i) => m.i + ((w - m.i - m.d) * i) / (factores.length - 1);
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

// --------------------------------------------------------- mapa de requisitos
function irA(panel, sub) {
  mostrarPanel(panel);
  if (sub && typeof mostrarSubpanelEstaciones === "function" && panel === "estaciones") mostrarSubpanelEstaciones(sub);
}
function cablearMapaRequisitos() {
  $$(".enlace-panel").forEach((b) => b.addEventListener("click", () => irA(b.dataset.ir, b.dataset.sub)));
}

// Se llama la primera vez que el usuario entra a esta pantalla (ver comun.js).
let comoFuncionaInicializado = false;
function alActivarComoFunciona() {
  if (comoFuncionaInicializado) return;
  comoFuncionaInicializado = true;
  cargarRendimiento();
}

function cablearComoFunciona() {
  cablearBotonMedir();
  cablearMapaRequisitos();
}

cablearComoFunciona();
