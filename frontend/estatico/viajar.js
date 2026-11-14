// ============================================================================
// frontend/estatico/viajar.js
// ----------------------------------------------------------------------------
// Pantalla "Viajar": busca un viaje (R5) y muestra, por cada tramo, el
// próximo bus (R4) calculado con la hora actual del computador. El motor
// decide todo (transbordos, horarios, estaciones cerradas); aquí solo se
// formatea la respuesta y se calcula "en N min" a partir de la hora que
// devuelve el motor.
// ============================================================================

function mensajeError(texto) {
  return `<p class="resultado-error"><span class="etiqueta mal">Sin viaje</span> ${texto}</p>`;
}

async function planearViaje() {
  const origen = $("in-origen").value.trim().toUpperCase();
  const destino = $("in-destino").value.trim().toUpperCase();
  const salida = $("out-viaje");
  if (!origen || !destino) {
    salida.innerHTML = `<p class="vacio">Escribe un origen y un destino, o prueba uno de los ejemplos de arriba.</p>`;
    return;
  }
  salida.innerHTML = `<p class="cargando">Buscando el mejor viaje…</p>`;

  const [resultado, estadoOrigen, estadoDestino] = await Promise.all([
    consultar("viaje", { origen, destino }),
    consultar("estado", { nombre: origen }),
    consultar("estado", { nombre: destino }),
  ]);

  if (!estadoOrigen.existe || !estadoDestino.existe) {
    const cual = !estadoOrigen.existe ? origen : destino;
    salida.innerHTML = mensajeError(`No encontramos una estación llamada <b>${esc(cual)}</b>. Revisa cómo se escribe.`);
    return;
  }
  if (!estadoOrigen.abierta || !estadoDestino.abierta) {
    const cual = !estadoOrigen.abierta ? origen : destino;
    salida.innerHTML = mensajeError(`<b>${esc(cual)}</b> está cerrada por ahora, así que no se puede planear un viaje desde o hacia ahí.`);
    return;
  }
  if (!resultado) {
    salida.innerHTML = mensajeError("No encontramos un viaje directo ni con un solo cambio de bus entre estas dos estaciones.");
    return;
  }
  if (resultado.tramos.length === 0) {
    salida.innerHTML = `<p class="vacio">Ya estás en el destino.</p>`;
    return;
  }
  salida.innerHTML = await lineaDeTiempo(destino, resultado);
}

async function lineaDeTiempo(destino, resultado) {
  const tipo = resultado.tramos.length === 1 ? "Directo" : "1 transbordo";
  const horaAhora = horaActualTexto();

  const tramosHtml = await Promise.all(resultado.tramos.map(async (t, i) => {
    const bus = await consultar("proximo_bus", { estacion: t.sube, ruta: t.ruta, hora: horaAhora });
    const esUltimo = i === resultado.tramos.length - 1;
    const infoBus = bus.proximo
      ? `<p class="bus-siguiente">Sale a las <b>${bus.proximo}</b> · en ${minutosDesdeAhora(bus.proximo)} min</p>
         <div class="horas">${bus.siguientes.map((h) => `<span>${h}</span>`).join("")}</div>`
      : `<p class="tenue">No hay más buses de esta ruta hoy en esta parada.</p>`;
    return `
      <li class="tramo-tiempo">
        <span class="punto origen"></span>
        <div class="tramo-cuerpo">
          <span class="pastilla-ruta" style="background:${colorRuta(t.ruta)}">${esc(t.ruta)}</span>
          <p>Sube en <b>${esc(t.sube)}</b></p>
          ${infoBus}
          <p class="${esUltimo ? "" : "cambia"}">${esUltimo ? "Baja en" : "Cambia aquí a la siguiente ruta — baja en"} <b>${esc(t.baja)}</b></p>
        </div>
      </li>`;
  }));

  return `
    <p class="resumen-viaje"><span class="etiqueta ok">${tipo}</span> <b>${resultado.paradas}</b> paradas</p>
    <ol class="linea-tiempo">
      ${tramosHtml.join("")}
      <li class="tramo-fin"><span class="punto destino"></span><p><b>${esc(destino)}</b> (destino)</p></li>
    </ol>`;
}

function usarEjemplo(origen, destino) {
  $("in-origen").value = origen;
  $("in-destino").value = destino;
  planearViaje();
}

function cablearViajar() {
  crearAutocompletar($("in-origen"));
  crearAutocompletar($("in-destino"));
  $("form-viaje").addEventListener("submit", (e) => { e.preventDefault(); planearViaje(); });
  $("btn-cambiar").addEventListener("click", () => {
    const o = $("in-origen").value;
    $("in-origen").value = $("in-destino").value;
    $("in-destino").value = o;
  });
  $$(".enlace-ejemplo").forEach((b) => b.addEventListener("click", () => usarEjemplo(b.dataset.origen, b.dataset.destino)));
}

cablearViajar();
