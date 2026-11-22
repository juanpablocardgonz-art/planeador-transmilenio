// ============================================================================
// frontend/estatico/hora-pico.js
// ----------------------------------------------------------------------------
// Pantalla "Hora pico": simula la fila de abordaje (R10) con sliders en
// lenguaje simple, una frase con el resultado, una animación ESQUEMÁTICA
// (ilustrativa: con hasta un millón de pasajeros no se puede ni tiene
// sentido animar a cada persona) y la gráfica real de llegadas vs. espera,
// que sí viene directo de la respuesta del motor.
// ============================================================================

function frase(r) {
  return `
    <p>En promedio, la gente esperó <b>${fmt(r.espera_promedio, 1)} minutos</b>; el 5% que más esperó, más de <b>${fmt(r.espera_p95, 1)} minutos</b>.</p>
    <p class="tenue">Se usaron <b>${fmt(r.buses)}</b> buses para <b>${fmt(r.pasajeros)}</b> pasajeros. El último bus salió a los <b>${fmt(r.ultimo_bus, 1)}</b> minutos de empezar.</p>`;
}

async function simularHoraPico() {
  const params = {
    pasajeros: $("in-pasajeros").value, minutos: $("in-minutos").value,
    frecuencia: $("in-frecuencia").value, capacidad: $("in-capacidad").value,
  };
  $("out-frase").innerHTML = `<p class="cargando">Simulando…</p>`;
  const r = await operar("simular", params);
  if (r.error) {
    $("out-frase").innerHTML = `<p class="resultado-error"><span class="etiqueta mal">Error</span> ${esc(r.error)}</p>`;
    return;
  }
  $("out-frase").innerHTML = frase(r);
  dibujarFila(r.franjas);
  animarEscena(params);
}

// Gráfica real: barras = llegadas por franja; línea = espera promedio.
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
  ctx.textAlign = "left";
}

// ------------------------------------------------- animación ilustrativa
let animacionId = null;
function detenerAnimacion() {
  if (animacionId) cancelAnimationFrame(animacionId);
  animacionId = null;
}
function animarEscena(params) {
  detenerAnimacion();
  const c = $("escena-fila");
  const { ctx, w, h } = prepararCanvas(c);
  const xAnden = w * 0.66;
  const yBase = h - 16;
  const capacidadVisual = Math.max(3, Math.min(16, Math.round(Number(params.capacidad) / 18)));
  const intervaloBusMs = Math.max(500, Math.min(2600, Number(params.frecuencia) * 420));
  let personas = [];
  let ultimoBus = performance.now();
  let ultimaLlegada = performance.now();

  function paso(ahora) {
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = color("--borde"); ctx.lineWidth = 2; ctx.beginPath();
    ctx.moveTo(10, yBase); ctx.lineTo(xAnden, yBase); ctx.stroke();

    ctx.fillStyle = color("--acento");
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(xAnden + 12, yBase - 32, 50, 32, 6);
    else ctx.rect(xAnden + 12, yBase - 32, 50, 32);
    ctx.fill();
    ctx.font = "16px system-ui"; ctx.textAlign = "center";
    ctx.fillText("🚌", xAnden + 37, yBase - 10);
    ctx.textAlign = "left";

    if (ahora - ultimaLlegada > 220 && personas.length < 40) {
      ultimaLlegada = ahora;
      personas.push({ x: 10, y: yBase - 5 - Math.random() * 5, destino: 24 + Math.random() * (xAnden - 60) });
    }
    personas.forEach((p) => { if (p.x < p.destino) p.x += 1.1; });

    if (ahora - ultimoBus > intervaloBusMs) {
      ultimoBus = ahora;
      personas.sort((a, b) => a.x - b.x);
      personas.splice(0, capacidadVisual);
    }

    ctx.fillStyle = color("--linea");
    personas.forEach((p) => { ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, Math.PI * 2); ctx.fill(); });

    animacionId = requestAnimationFrame(paso);
  }
  animacionId = requestAnimationFrame(paso);
}

// -------------------------------------------------------------- cablear
function cablearSliders() {
  [["in-pasajeros", "valor-pasajeros", (v) => fmt(v)],
   ["in-frecuencia", "valor-frecuencia", (v) => v],
   ["in-capacidad", "valor-capacidad", (v) => v],
   ["in-minutos", "valor-minutos", (v) => v]].forEach(([idEntrada, idSalida, formatear]) => {
    const entrada = $(idEntrada), salida = $(idSalida);
    const actualizar = () => { salida.textContent = formatear(entrada.value); };
    entrada.addEventListener("input", actualizar);
    actualizar();
  });
}

function cablearHoraPico() {
  cablearSliders();
  $("form-simular").addEventListener("submit", (e) => { e.preventDefault(); simularHoraPico(); });
}

cablearHoraPico();
