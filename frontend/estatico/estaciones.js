// ============================================================================
// frontend/estatico/estaciones.js
// ----------------------------------------------------------------------------
// Pantalla "Estaciones": ficha de una estación (R1), buscador A-Z (R2 para
// el campo de búsqueda, R3 para el listado por rango) y las más concurridas
// (R6). El motor decide todo; aquí solo se formatea y se agrupa por letra.
// ============================================================================

// --------------------------------------------------------------------- R1
async function mostrarFicha(nombreCrudo) {
  const nombre = (nombreCrudo || "").trim().toUpperCase();
  const cont = $("ficha-estacion");
  if (!nombre) {
    cont.innerHTML = `<p class="vacio">Escribe el nombre de una estación, por ejemplo CALLE 26.</p>`;
    return;
  }
  cont.innerHTML = `<p class="cargando">Buscando…</p>`;
  const r = await consultar("estado", { nombre });
  if (!r.existe) {
    cont.innerHTML = `<p class="vacio">No encontramos ninguna estación llamada <b>${esc(nombre)}</b>.</p>`;
    return;
  }
  cont.innerHTML = `
    <div class="ficha-cabecera">
      <h2>${esc(r.nombre)}</h2>
      <span class="etiqueta ${r.abierta ? "ok" : "mal"}">${r.abierta ? "Abierta" : "Cerrada"}</span>
    </div>
    <p class="ficha-buses">${fmt(r.buses)} buses al día</p>
    <ul class="ficha-rutas">
      ${r.rutas.length
        ? r.rutas.map((ruta) => `<li><button type="button" class="pastilla-ruta" style="background:${colorRuta(ruta)}" data-ruta="${esc(ruta)}" data-estacion="${esc(r.nombre)}">${esc(ruta)}</button></li>`).join("")
        : `<li class="tenue">Ninguna ruta activa pasa por aquí.</li>`}
    </ul>
    <div class="detalle-ruta-estacion" id="detalle-ruta-estacion"></div>`;
}

async function alClicRuta(e) {
  const boton = e.target.closest("[data-ruta]");
  if (!boton) return;
  const detalle = $("detalle-ruta-estacion");
  detalle.innerHTML = `<p class="cargando">Consultando…</p>`;
  const r = await consultar("proximo_bus", { estacion: boton.dataset.estacion, ruta: boton.dataset.ruta, hora: horaActualTexto() });
  detalle.innerHTML = r.proximo
    ? `<p>Próximo bus de <b>${esc(boton.dataset.ruta)}</b>: <b>en ${minutosDesdeAhora(r.proximo)} min</b> (${r.proximo})</p>
       <div class="horas">${r.siguientes.map((h) => `<span>${h}</span>`).join("")}</div>`
    : `<p class="tenue">No hay más buses de esta ruta hoy en esta estación.</p>`;
}

// ------------------------------------------------------------------ R2/R3
let explorarCargado = false;
async function cargarExplorar() {
  const desde = $("in-rango-desde").value.trim().toUpperCase();
  const hasta = $("in-rango-hasta").value.trim().toUpperCase();
  const cont = $("out-explorar");
  cont.innerHTML = `<p class="cargando">Buscando…</p>`;
  const lista = await consultar("rango", { desde, hasta: hasta || "￿" });
  if (!lista.length) {
    cont.innerHTML = `<p class="vacio">Ninguna estación abierta en ese rango.</p>`;
    return;
  }
  const grupos = [];
  lista.forEach((nombre) => {
    const letra = nombre.charAt(0);
    const ultimo = grupos[grupos.length - 1];
    if (!ultimo || ultimo.letra !== letra) grupos.push({ letra, nombres: [nombre] });
    else ultimo.nombres.push(nombre);
  });
  cont.innerHTML =
    `<nav class="indice-letras" aria-label="Ir a la letra">
       ${grupos.map((g) => `<button type="button" data-letra="${esc(g.letra)}">${esc(g.letra)}</button>`).join("")}
     </nav>` +
    grupos.map((g) => `
      <div class="grupo-letra" id="letra-${esc(g.letra)}">
        <h3>${esc(g.letra)} · ${g.nombres.length}</h3>
        <ul class="lista-az">${g.nombres.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>
      </div>`).join("") +
    `<p class="tenue">${fmt(lista.length)} estaciones en total.</p>`;
}

// --------------------------------------------------------------------- R6
async function cargarConcurridas() {
  const k = Number($("in-rank-k").value) || 10;
  const lista = await consultar("ranking", { k });
  if (!lista.length) {
    $("out-podio").innerHTML = "";
    $("out-concurridas").innerHTML = `<p class="vacio">No hay estaciones abiertas.</p>`;
    return;
  }
  const top3 = lista.slice(0, 3);
  const resto = lista.slice(3);
  const medallas = ["🥇", "🥈", "🥉"];
  $("out-podio").innerHTML = top3.map((x, i) => `
    <div class="podio-puesto puesto-${i + 1}">
      <div class="medalla">${medallas[i]}</div>
      <div class="nombre">${esc(x.nombre)}</div>
      <div class="buses">${fmt(x.buses)} buses/día</div>
    </div>`).join("");
  const tope = lista[0].buses || 1;
  $("out-concurridas").innerHTML = resto.map((x, i) => `
    <div class="barra-fila"><span class="pos">${i + 4}</span><span>${esc(x.nombre)}</span>
      <span class="pista"><span class="relleno" style="width:${(100 * x.buses) / tope}%"></span></span>
      <span class="valor">${fmt(x.buses)}</span></div>`).join("");
}

// -------------------------------------------------------------- subpestañas
const SUBPANELES_ESTACIONES = ["buscar", "explorar", "concurridas"];
function mostrarSubpanelEstaciones(nombre) {
  SUBPANELES_ESTACIONES.forEach((p) => $(`sub-${p}`)?.classList.toggle("activo", p === nombre));
  $$(".subpestana").forEach((b) => b.classList.toggle("activa", b.dataset.sub === nombre));
  if (nombre === "explorar" && !explorarCargado) { explorarCargado = true; cargarExplorar(); }
  if (nombre === "concurridas") cargarConcurridas();
}

// Se llama la primera vez que el usuario entra a esta pantalla (ver comun.js).
let estacionesInicializado = false;
function alActivarEstaciones() {
  if (estacionesInicializado) return;
  estacionesInicializado = true;
  cargarConcurridas();
}

function cablearEstaciones() {
  crearAutocompletar($("in-estacion"), { onSeleccion: mostrarFicha });
  $("in-estacion").addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    const lista = $("in-estacion-lista");
    if (lista.hidden) { e.preventDefault(); mostrarFicha($("in-estacion").value); }
  });
  $$(".subpestana").forEach((b) => b.addEventListener("click", () => mostrarSubpanelEstaciones(b.dataset.sub)));
  $("btn-rango-explorar").addEventListener("click", cargarExplorar);
  $("out-explorar").addEventListener("click", (e) => {
    const b = e.target.closest("[data-letra]");
    if (b) $(`letra-${b.dataset.letra}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  $("ficha-estacion").addEventListener("click", alClicRuta);
  $("btn-rank").addEventListener("click", cargarConcurridas);
}

cablearEstaciones();
