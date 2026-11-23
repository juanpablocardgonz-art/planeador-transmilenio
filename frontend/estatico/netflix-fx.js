// ============================================================================
// frontend/estatico/netflix-fx.js
// ----------------------------------------------------------------------------
// Capa cinemática estilo Netflix: mosaico inclinado, cambio dinámico de fondo
// al hacer scroll, carruseles interactivos, revelado al desplazamiento y
// micro-interacciones.
// ============================================================================

(() => {
  const MOSAICO_ITEMS = [
    { ruta: "B75", nombre: "PORTAL NORTE", zona: "Autonorte", c1: "#b91c1c", c2: "#450a0a" },
    { ruta: "1-3", nombre: "PORTAL ELDORADO", zona: "Calle 26", c1: "#d97706", c2: "#451a03" },
    { ruta: "G43", nombre: "PORTAL SUR", zona: "NQS Sur", c1: "#1d4ed8", c2: "#172554" },
    { ruta: "2-3", nombre: "PORTAL 20 DE JULIO", zona: "Cra. 10", c1: "#047857", c2: "#022c22" },
    { ruta: "K54", nombre: "CAN", zona: "ElDorado", c1: "#b45309", c2: "#292524" },
    { ruta: "3-3", nombre: "PORTAL USME", zona: "Caracas Sur", c1: "#be123c", c2: "#3f0d1c" },
    { ruta: "F23", nombre: "BANDERAS", zona: "Américas", c1: "#7e22ce", c2: "#2e1065" },
    { ruta: "C15", nombre: "PORTAL SUBA", zona: "Av. Suba", c1: "#0f766e", c2: "#042f2e" },
    { ruta: "D22", nombre: "PORTAL 80", zona: "Calle 80", c1: "#c2410c", c2: "#431407" },
    { ruta: "H20", nombre: "PORTAL TUNAL", zona: "Tunjuelito", c1: "#dc2626", c2: "#3b0764" },
    { ruta: "J70", nombre: "UNIVERSIDADES", zona: "Eje Ambiental", c1: "#0284c7", c2: "#082f49" },
    { ruta: "4-1", nombre: "RICAURTE", zona: "NQS · Américas", c1: "#9333ea", c2: "#1e1b4b" },
    { ruta: "M47", nombre: "MUSEO NACIONAL", zona: "Centro", c1: "#059669", c2: "#064e3b" },
    { ruta: "A60", nombre: "CALLE 26", zona: "Caracas", c1: "#e11d48", c2: "#31102f" },
    { ruta: "L18", nombre: "AV. JIMENEZ", zona: "Conexión Central", c1: "#ea580c", c2: "#271710" },
    { ruta: "E42", nombre: "HEROES", zona: "Norte · Caracas", c1: "#2563eb", c2: "#0f172a" },
    { ruta: "B12", nombre: "CALLE 100", zona: "Autonorte", c1: "#b91c1c", c2: "#1f1215" },
    { ruta: "G11", nombre: "CAD", zona: "Troncal NQS", c1: "#4f46e5", c2: "#1e1b4b" },
    { ruta: "F19", nombre: "PORTAL AMERICAS", zona: "Suroccidente", c1: "#a21caf", c2: "#3b0764" },
    { ruta: "K10", nombre: "EL TIEMPO - MALOKA", zona: "Salitre", c1: "#ca8a04", c2: "#1c1917" },
    { ruta: "C25", nombre: "NIZA - CALLE 127", zona: "Suba", c1: "#0d9488", c2: "#111827" },
    { ruta: "D10", nombre: "MINUTO DE DIOS", zona: "Calle 80", c1: "#d97706", c2: "#27150a" },
    { ruta: "J24", nombre: "MARLY", zona: "Chapinero", c1: "#e50914", c2: "#18181b" },
    { ruta: "H15", nombre: "MOLINOS", zona: "Sur", c1: "#be185d", c2: "#1f1221" },
  ];

  const TOP_VIAJES = [
    { origen: "PORTAL NORTE", destino: "PORTAL SUR", tag: "Troncal Norte-Sur", badge: "EXPRESO", c1: "#e50914", c2: "#1b0b12" },
    { origen: "PORTAL ELDORADO", destino: "UNIVERSIDADES", tag: "Corredor Calle 26", badge: "DIRECTO", c1: "#d97706", c2: "#1c1408" },
    { origen: "CALLE 26", destino: "RICAURTE", tag: "Conexión Centro", badge: "RÁPIDO", c1: "#2563eb", c2: "#0b132b" },
    { origen: "PORTAL AMERICAS", destino: "AV. JIMENEZ", tag: "Corredor Américas", badge: "POPULAR", c1: "#9333ea", c2: "#1a0b2e" },
    { origen: "PORTAL 80", destino: "HEROES", tag: "Calle 80 → Norte", badge: "TRONCAL", c1: "#ea580c", c2: "#241007" },
    { origen: "PORTAL USME", destino: "CALLE 72", tag: "Caracas Completa", badge: "CLÁSICO", c1: "#059669", c2: "#071f18" },
  ];

  const PORTALES_DESTACADOS = [
    { nombre: "RICAURTE", sub: "Intercambiador NQS · Américas", icono: "🔀", color: "#9333ea" },
    { nombre: "CALLE 26", sub: "Corazón Troncal Caracas", icono: "🚇", color: "#e50914" },
    { nombre: "PORTAL NORTE", sub: "Cabecera Autopista Norte", icono: "🧭", color: "#2563eb" },
    { nombre: "PORTAL ELDORADO", sub: "Conexión Aeropuerto · Cl. 26", icono: "✈️", color: "#d97706" },
    { nombre: "AV. JIMENEZ", sub: "Eje Ambiental · Centro", icono: "🏛️", color: "#ea580c" },
    { nombre: "BANDERAS", sub: "Hub Troncal Américas", icono: "🚩", color: "#db2777" },
    { nombre: "UNIVERSIDADES", sub: "Zona Académica · Centro", icono: "🎓", color: "#0284c7" },
    { nombre: "PORTAL SUR", sub: "Cabecera Autopista Sur", icono: "🛣️", color: "#16a34a" },
  ];

  const NOMBRES_ESCENA = {
    hero: "Escena · Cartelera Troncal",
    carrusel: "Escena · Tendencias Bogotá",
    viajar: "Escena · Planificador en Vivo",
    estaciones: "Escena · Explorador de Red",
    operar: "Escena · Centro de Control O(1)",
    horapico: "Escena · Simulador Hora Pico",
    comofunciona: "Escena · Motor Algorítmico",
    "operar-banda": "Escena · Edición de Rutas",
    "horapico-banda": "Escena · Flujo Masivo",
    "motor-banda": "Escena · Estructuras de Datos",
  };

  function poblarMosaico() {
    const cont = document.getElementById("netflix-mosaico");
    if (!cont) return;
    const tarjetas = [...MOSAICO_ITEMS, ...MOSAICO_ITEMS.slice(0, 12)];
    cont.innerHTML = tarjetas
      .map((item, idx) => `
        <div class="mosaico-poster" style="--p1:${item.c1}; --p2:${item.c2}; --delay:${(idx % 8) * 0.4}s">
          <div class="mosaico-brillo"></div>
          <span class="mosaico-ruta">${item.ruta}</span>
          <div class="mosaico-info">
            <span class="mosaico-zona">${item.zona}</span>
            <strong>${item.nombre}</strong>
          </div>
        </div>`)
      .join("");
  }

  function poblarCarruseles() {
    const pistaTop = document.getElementById("carrusel-top");
    if (pistaTop) {
      pistaTop.innerHTML = TOP_VIAJES.map((v, i) => `
        <button type="button" class="tarjeta-top tarjeta-poster btn-magnetico"
          data-viaje-origen="${v.origen}" data-viaje-destino="${v.destino}"
          style="--c1:${v.c1}; --c2:${v.c2}">
          <span class="top-numero" aria-hidden="true">${i + 1}</span>
          <div class="top-afiche">
            <div class="top-cabecera">
              <span class="top-badge">${v.badge}</span>
              <span class="top-play">▶ Planear</span>
            </div>
            <div class="top-cuerpo">
              <span class="top-zona">${v.tag}</span>
              <strong class="top-titulo">${v.origen}</strong>
              <span class="top-flecha">↓ hacia</span>
              <strong class="top-titulo">${v.destino}</strong>
            </div>
          </div>
        </button>`).join("");
    }

    const pistaPortales = document.getElementById("carrusel-portales");
    if (pistaPortales) {
      pistaPortales.innerHTML = PORTALES_DESTACADOS.map((p) => `
        <button type="button" class="tarjeta-portal tarjeta-poster btn-magnetico"
          data-ver-estacion="${p.nombre}" style="--acento-card:${p.color}">
          <div class="portal-icono">${p.icono}</div>
          <div class="portal-texto">
            <strong>${p.nombre}</strong>
            <span>${p.sub}</span>
          </div>
          <span class="portal-ir">Inspeccionar ›</span>
        </button>`).join("");
    }
  }

  function cablearCarruseles() {
    document.querySelectorAll(".btn-carrusel").forEach((btn) => {
      btn.addEventListener("click", () => {
        const pista = document.getElementById(btn.dataset.target);
        if (!pista) return;
        const dir = Number(btn.dataset.dir || 1);
        const paso = Math.max(280, pista.clientWidth * 0.72);
        pista.scrollBy({ left: dir * paso, behavior: "smooth" });
      });
    });

    document.getElementById("carrusel-top")?.addEventListener("click", (e) => {
      const card = e.target.closest("[data-viaje-origen]");
      if (!card) return;
      const origen = card.dataset.viajeOrigen;
      const destino = card.dataset.viajeDestino;
      if (typeof mostrarPanel === "function") mostrarPanel("viajar", true);
      if (typeof usarEjemplo === "function") {
        usarEjemplo(origen, destino);
      } else {
        const inO = document.getElementById("in-origen");
        const inD = document.getElementById("in-destino");
        if (inO) inO.value = origen;
        if (inD) inD.value = destino;
      }
      if (typeof aviso === "function") aviso(`Planeando ${origen} → ${destino}`);
    });

    document.getElementById("carrusel-portales")?.addEventListener("click", (e) => {
      const card = e.target.closest("[data-ver-estacion]");
      if (!card) return;
      const nombre = card.dataset.verEstacion;
      if (typeof mostrarPanel === "function") mostrarPanel("estaciones", true);
      if (typeof mostrarSubpanelEstaciones === "function") mostrarSubpanelEstaciones("buscar");
      const input = document.getElementById("in-estacion");
      if (input) input.value = nombre;
      if (typeof mostrarFicha === "function") mostrarFicha(nombre);
    });
  }

  let escenaActual = "hero";

  function aplicarEscena(nombre) {
    const efectiva = nombre === "workspace" ? (document.body.dataset.panel || "viajar") : nombre;
    if (escenaActual === efectiva) return;
    escenaActual = efectiva;
    document.body.dataset.escena = efectiva;
    const hud = document.getElementById("hud-escena-texto");
    if (hud) hud.textContent = NOMBRES_ESCENA[efectiva] || "Escena · Red TransMilenio";
  }

  function iniciarScrollDinamico() {
    const barra = document.getElementById("cabecera-principal");
    const progreso = document.getElementById("progreso-scroll");
    const hud = document.getElementById("hud-flotante");
    let ticking = false;

    function actualizarPorScroll() {
      const y = window.scrollY || 0;
      const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      const pct = Math.min(1, Math.max(0, y / maxScroll));

      document.documentElement.style.setProperty("--scroll-y", `${y.toFixed(1)}px`);
      document.documentElement.style.setProperty("--scroll-pct", pct.toFixed(4));

      if (progreso) progreso.style.transform = `scaleX(${pct})`;
      if (barra) barra.classList.toggle("scrolled", y > 40);
      if (hud) hud.classList.toggle("visible", y > 260);
      ticking = false;
    }

    window.addEventListener("scroll", () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(actualizarPorScroll);
      }
    }, { passive: true });
    actualizarPorScroll();

    const triggers = document.querySelectorAll("[data-escena-trigger]");
    if ("IntersectionObserver" in window && triggers.length) {
      const obs = new IntersectionObserver((entries) => {
        let mejor = null;
        entries.forEach((entry) => {
          if (entry.isIntersecting && (!mejor || entry.intersectionRatio > mejor.intersectionRatio)) {
            mejor = entry;
          }
        });
        if (mejor) aplicarEscena(mejor.target.dataset.escenaTrigger);
      }, { threshold: [0.18, 0.45, 0.7] });

      triggers.forEach((el) => obs.observe(el));
    }

    document.addEventListener("panel-cambiado", (e) => {
      if (e.detail?.nombre) aplicarEscena(e.detail.nombre);
    });

    const reveals = document.querySelectorAll("[data-reveal]");
    if ("IntersectionObserver" in window && reveals.length) {
      const obsReveal = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("revelado");
            obsReveal.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12 });
      reveals.forEach((el) => obsReveal.observe(el));
    } else {
      reveals.forEach((el) => el.classList.add("revelado"));
    }
  }

  function iniciarInteraccionesBotones() {
    document.addEventListener("pointerdown", (e) => {
      const target = e.target.closest("button, .tarjeta-poster");
      if (!target || target.disabled) return;
      const rect = target.getBoundingClientRect();
      const onda = document.createElement("span");
      onda.className = "ripple-onda";
      const tam = Math.max(rect.width, rect.height) * 1.4;
      onda.style.width = onda.style.height = `${tam}px`;
      onda.style.left = `${e.clientX - rect.left - tam / 2}px`;
      onda.style.top = `${e.clientY - rect.top - tam / 2}px`;
      target.appendChild(onda);
      onda.addEventListener("animationend", () => onda.remove(), { once: true });
    });

    document.addEventListener("pointermove", (e) => {
      const el = e.target.closest(".btn-magnetico, .tarjeta-poster");
      if (!el) return;
      const r = el.getBoundingClientRect();
      const x = ((e.clientX - r.left) / r.width) * 100;
      const y = ((e.clientY - r.top) / r.height) * 100;
      el.style.setProperty("--mx", `${x.toFixed(1)}%`);
      el.style.setProperty("--my", `${y.toFixed(1)}%`);
      if (el.classList.contains("tarjeta-poster")) {
        const rx = ((y - 50) / 50) * -5;
        const ry = ((x - 50) / 50) * 6;
        el.style.setProperty("--rx", `${rx.toFixed(2)}deg`);
        el.style.setProperty("--ry", `${ry.toFixed(2)}deg`);
      }
    });

    document.addEventListener("pointerout", (e) => {
      const el = e.target.closest(".tarjeta-poster");
      if (el && !el.contains(e.relatedTarget)) {
        el.style.setProperty("--rx", "0deg");
        el.style.setProperty("--ry", "0deg");
      }
    });

    const btnCambiar = document.getElementById("btn-cambiar");
    if (btnCambiar) {
      btnCambiar.addEventListener("click", () => {
        btnCambiar.classList.remove("girando");
        void btnCambiar.offsetWidth;
        btnCambiar.classList.add("girando");
      });
    }
  }

  function cablearHeroYAcciones() {
    const heroForm = document.getElementById("hero-form");
    if (heroForm) {
      heroForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const o = (document.getElementById("hero-origen")?.value || "").trim();
        const d = (document.getElementById("hero-destino")?.value || "").trim();
        if (typeof mostrarPanel === "function") mostrarPanel("viajar", true);
        const inO = document.getElementById("in-origen");
        const inD = document.getElementById("in-destino");
        if (o && inO) inO.value = o;
        if (d && inD) inD.value = d;
        if (o && d && typeof planearViaje === "function") {
          planearViaje();
        } else if (inO && !o) {
          inO.focus();
        }
      });
    }

    document.querySelectorAll("[data-ir-panel]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const panel = btn.dataset.irPanel;
        const sub = btn.dataset.irSub;
        const ruta = btn.dataset.cargarRuta;
        if (typeof mostrarPanel === "function") mostrarPanel(panel, true);
        if (panel === "estaciones" && sub && typeof mostrarSubpanelEstaciones === "function") {
          mostrarSubpanelEstaciones(sub);
        }
        if (panel === "operar" && ruta) {
          const inRuta = document.getElementById("in-ruta-operar");
          if (inRuta) inRuta.value = ruta;
          if (typeof cargarRutaOperar === "function") cargarRutaOperar();
        }
      });
    });

    document.getElementById("btn-toggle-capo-banda")?.addEventListener("click", () => {
      if (typeof modoExplicacionActivo === "function" && typeof aplicarModoExplicacion === "function") {
        const nuevo = !modoExplicacionActivo();
        aplicarModoExplicacion(nuevo);
        if (typeof aviso === "function") {
          aviso(nuevo ? "Modo explicación activado: tarjetas técnicas visibles" : "Modo explicación desactivado");
        }
      }
    });

    document.getElementById("btn-bajar-explorar")?.addEventListener("click", () => {
      const sec = document.getElementById("seccion-carruseles");
      if (sec) sec.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    const irArriba = () => window.scrollTo({ top: 0, behavior: "smooth" });
    document.getElementById("btn-volver-arriba")?.addEventListener("click", irArriba);
    const marca = document.getElementById("btn-marca-inicio");
    if (marca) {
      marca.addEventListener("click", irArriba);
      marca.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); irArriba(); }
      });
    }
  }

  poblarMosaico();
  poblarCarruseles();
  cablearCarruseles();
  iniciarScrollDinamico();
  iniciarInteraccionesBotones();
  cablearHeroYAcciones();
})();
