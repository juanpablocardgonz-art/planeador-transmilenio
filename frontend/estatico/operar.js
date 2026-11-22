// ============================================================================
// frontend/estatico/operar.js
// ----------------------------------------------------------------------------
// Pantalla "Operar la red": diagrama de línea tipo metro para editar rutas
// (R7), cerrar/reabrir estaciones (R8) y deshacer/rehacer (R9). El motor
// decide si cada operación es válida; el front solo pinta el diagrama y
// lleva, en dos arreglos propios, la DESCRIPCIÓN de cada cambio para
// mostrarla en la barra de deshacer/rehacer (el servidor solo da contadores,
// no texto — ver README).
// ============================================================================

let rutaActual = null;
let alRevesActual = false;
let estacionFichaActual = null;
let despuesDeActual = null;

// ------------------------------------------------------------- diagrama R7
async function cargarRutaOperar() {
  const ruta = $("in-ruta-operar").value.trim();
  const diagrama = $("diagrama-ruta");
  if (!ruta) {
    diagrama.innerHTML = `<li class="vacio-diagrama">Elige una ruta para ver su recorrido.</li>`;
    rutaActual = null;
    return;
  }
  diagrama.innerHTML = `<li class="vacio-diagrama">Cargando…</li>`;
  const nombres = await consultar("recorrido", { ruta, al_reves: alRevesActual ? 1 : 0 });
  if (!nombres) {
    diagrama.innerHTML = `<li class="vacio-diagrama">La ruta "${esc(ruta)}" no existe.</li>`;
    rutaActual = null;
    return;
  }
  rutaActual = ruta;
  const estados = await Promise.all(nombres.map((n) => consultar("estado", { nombre: n })));
  dibujarDiagrama(nombres, estados);
}

function dibujarDiagrama(nombres, estados) {
  const diagrama = $("diagrama-ruta");
  if (!nombres.length) {
    diagrama.innerHTML = `<li class="vacio-diagrama">Esta ruta no tiene paradas.</li>`;
    return;
  }
  let html = `<li class="tramo-diagrama"><button type="button" class="boton-mas" data-despues="" aria-label="Insertar parada al inicio">+</button></li>`;
  nombres.forEach((nombre, i) => {
    const abierta = estados[i].abierta;
    html += `
      <li class="parada-diagrama ${abierta ? "" : "cerrada"}">
        <button type="button" class="circulo-parada ${estacionFichaActual === nombre ? "activa" : ""}" data-estacion="${esc(nombre)}" title="${esc(nombre)}">
          <span class="punto-parada"></span><span class="nombre-parada">${esc(nombre)}</span>
        </button>
      </li>
      <li class="tramo-diagrama"><button type="button" class="boton-mas" data-despues="${esc(nombre)}" aria-label="Insertar parada después de ${esc(nombre)}">+</button></li>`;
  });
  diagrama.innerHTML = html;
}

// ------------------------------------------------------------- insertar R7
function abrirPopoverInsertar(despues) {
  despuesDeActual = despues;
  const pop = $("popover-insertar");
  pop.hidden = false;
  $("texto-insertar").textContent = despues ? `Insertar después de ${despues}` : "Insertar al inicio de la ruta";
  $("in-nueva-parada").value = "";
  $("in-nueva-parada").focus();
}
function cerrarPopoverInsertar() {
  $("popover-insertar").hidden = true;
  despuesDeActual = null;
}
async function confirmarInsertar() {
  const nueva = $("in-nueva-parada").value.trim().toUpperCase();
  if (!nueva || !rutaActual) return;
  const r = await operar("agregar_parada", { ruta: rutaActual, nueva, despues_de: despuesDeActual || "" });
  if (r.ok) {
    registrarAccion(`agregar ${nueva} en ${rutaActual}`);
    aviso(`Se agregó ${nueva} a ${rutaActual}`, { texto: "Deshacer", fn: hacerDeshacer });
    cerrarPopoverInsertar();
    cargarRutaOperar();
  } else {
    aviso("No se pudo: revisa que la estación no esté ya en la ruta y que 'después de' sí exista ahí.");
  }
}

// --------------------------------------------------------------- ficha R7/R8
async function mostrarFichaParada(nombre) {
  estacionFichaActual = nombre;
  $$(".circulo-parada", $("diagrama-ruta")).forEach((b) => b.classList.toggle("activa", b.dataset.estacion === nombre));
  const r = await consultar("estado", { nombre });
  $("ficha-parada-operar").innerHTML = `
    <div class="ficha-parada">
      <div class="ficha-parada-cabecera">
        <h2>${esc(nombre)}</h2>
        <span class="etiqueta ${r.abierta ? "ok" : "mal"}">${r.abierta ? "Abierta" : "Cerrada"}</span>
      </div>
      <p class="tenue">${fmt(r.buses)} buses al día · rutas: ${r.rutas.map(esc).join(", ") || "ninguna"}</p>
      <div class="ficha-parada-acciones">
        <button type="button" id="btn-toggle-estacion">${r.abierta ? "Cerrar esta estación" : "Reabrir esta estación"}</button>
        <button type="button" id="btn-quitar-de-ruta" class="boton-peligro">Quitar de esta ruta</button>
      </div>
    </div>`;
  $("btn-toggle-estacion").addEventListener("click", () => alternarEstacion(nombre, r.abierta));
  $("btn-quitar-de-ruta").addEventListener("click", () => quitarDeRuta(nombre));
}

async function alternarEstacion(nombre, estabaAbierta) {
  const accion = estabaAbierta ? "cerrar" : "reabrir";
  const r = await operar(accion, { nombre });
  if (r.ok) {
    registrarAccion(`${accion} ${nombre}`);
    aviso(`Se ${estabaAbierta ? "cerró" : "reabrió"} ${nombre}`, { texto: "Deshacer", fn: hacerDeshacer });
    await cargarRutaOperar();
    mostrarFichaParada(nombre);
  } else {
    aviso(`No se pudo ${accion === "cerrar" ? "cerrar" : "reabrir"}: ${nombre} ya estaba así.`);
  }
}

async function quitarDeRuta(nombre) {
  if (!confirm(`¿Quitar ${nombre} de la ruta ${rutaActual}? Esto no cierra la estación, solo la saca de esta ruta.`)) return;
  const r = await operar("quitar_parada", { ruta: rutaActual, estacion: nombre });
  if (r.ok) {
    registrarAccion(`quitar ${nombre} de ${rutaActual}`);
    aviso(`Se quitó ${nombre} de ${rutaActual}`, { texto: "Deshacer", fn: hacerDeshacer });
    estacionFichaActual = null;
    $("ficha-parada-operar").innerHTML = "";
    cargarRutaOperar();
  } else {
    aviso("No se pudo quitar esa parada.");
  }
}

// ---------------------------------------------------------- deshacer/rehacer R9
// El servidor solo da CONTADORES (cuántos cambios se pueden deshacer/rehacer);
// la descripción de cada uno la lleva el front, en dos pilas que se llenan
// cuando el propio front ejecuta una operación. Si el contador del servidor
// queda desincronizado de estas pilas (por ejemplo al recargar la página a
// mitad de sesión), se usa un texto genérico.
let descripcionesDeshacer = [];
let descripcionesRehacer = [];

function registrarAccion(descripcion) {
  descripcionesDeshacer.push(descripcion);
  descripcionesRehacer = [];
  // El evento "red-actualizada" (que repinta esta barra) se dispara DENTRO
  // de operar(), antes de que quien llamó a operar() alcance a registrar la
  // descripción. Por eso se repinta otra vez aquí, con la pila ya al día.
  actualizarBarraHistorial();
}

function actualizarBarraHistorial() {
  const textoD = descripcionesDeshacer[descripcionesDeshacer.length - 1];
  const textoR = descripcionesRehacer[descripcionesRehacer.length - 1];
  $("texto-deshacer").textContent = textoD ? `Deshacer: ${textoD}` : "Deshacer";
  $("texto-rehacer").textContent = textoR ? `Rehacer: ${textoR}` : "Rehacer";
}

async function refrescarTrasHistorial() {
  if (rutaActual) await cargarRutaOperar();
  if (estacionFichaActual) mostrarFichaParada(estacionFichaActual);
}

async function hacerDeshacer() {
  const descripcion = descripcionesDeshacer.pop();
  const r = await operar("deshacer");
  if (r.ok) {
    if (descripcion) descripcionesRehacer.push(descripcion);
    aviso(`Se deshizo: ${descripcion ?? "el último cambio"}`);
    await refrescarTrasHistorial();
  } else {
    if (descripcion) descripcionesDeshacer.push(descripcion);
    aviso("No había nada que deshacer");
  }
  actualizarBarraHistorial();
}

async function hacerRehacer() {
  const descripcion = descripcionesRehacer.pop();
  const r = await operar("rehacer");
  if (r.ok) {
    if (descripcion) descripcionesDeshacer.push(descripcion);
    aviso(`Se rehizo: ${descripcion ?? "el último cambio"}`);
    await refrescarTrasHistorial();
  } else {
    if (descripcion) descripcionesRehacer.push(descripcion);
    aviso("No había nada que rehacer");
  }
  actualizarBarraHistorial();
}

document.addEventListener("red-actualizada", (e) => {
  const r = e.detail;
  $("btn-deshacer").disabled = r.deshacer === 0;
  $("btn-rehacer").disabled = r.rehacer === 0;
  actualizarBarraHistorial();
});

// ------------------------------------------------------------------- cablear
function cablearOperar() {
  crearAutocompletar($("in-ruta-operar"), { onSeleccion: cargarRutaOperar });
  $("btn-ver-ruta").addEventListener("click", cargarRutaOperar);
  $("in-ruta-operar").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && $("in-ruta-operar-lista").hidden) { e.preventDefault(); cargarRutaOperar(); }
  });
  $$(".segmento").forEach((b) => b.addEventListener("click", () => {
    $$(".segmento").forEach((x) => x.classList.toggle("activo", x === b));
    alRevesActual = b.dataset.sentido === "reves";
    cargarRutaOperar();
  }));
  $("diagrama-ruta").addEventListener("click", (e) => {
    const circulo = e.target.closest("[data-estacion]");
    if (circulo) return mostrarFichaParada(circulo.dataset.estacion);
    const mas = e.target.closest("[data-despues]");
    if (mas) abrirPopoverInsertar(mas.dataset.despues);
  });
  crearAutocompletar($("in-nueva-parada"));
  $("btn-confirmar-insertar").addEventListener("click", confirmarInsertar);
  $("btn-cancelar-insertar").addEventListener("click", cerrarPopoverInsertar);
  $("in-nueva-parada").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && $("in-nueva-parada-lista").hidden) { e.preventDefault(); confirmarInsertar(); }
  });
  $("btn-deshacer").addEventListener("click", hacerDeshacer);
  $("btn-rehacer").addEventListener("click", hacerRehacer);
}

cablearOperar();
