
// ── atracciones.js ──────────────────────────────────────────────────────
// Página "Atracciones y planes" de un pueblo específico. Es genérica: no
// tiene el nombre de ningún pueblo escrito a mano, funciona para cualquier
// pueblo que exista en DESTINOS (js/data.js). Se apoya en las funciones
// globales de js/auth.js (API_BASE_URL, peticionSincrona, etc.), así que
// auth.js debe cargarse ANTES que este archivo.

const WHATSAPP_NUMERO_ATRACCIONES = "573052369751";

function escaparTextoAtracciones(texto) {
  const div = document.createElement("div");
  div.textContent = texto == null ? "" : String(texto);
  return div.innerHTML;
}

function renderizarAtracciones(atracciones) {
  const contenedor = document.getElementById("lista-atracciones");
  if (!contenedor) return;

  if (!atracciones || atracciones.length === 0) {
    contenedor.innerHTML = '<p class="atracciones-vacio">Todavía no hay atracciones cargadas para este destino.</p>';
    return;
  }

  contenedor.innerHTML = atracciones.map(function (a) {
    const nombre = escaparTextoAtracciones(a.nombre);
    const tipo = escaparTextoAtracciones(a.tipo || "Plan");
    const descripcion = escaparTextoAtracciones(a.descripcion || "");
    const foto = a.foto || "https://picsum.photos/seed/" + encodeURIComponent(a.nombre || "atraccion") + "/700/500";
    return (
      '<div class="tarjeta-atraccion-item">' +
        '<div class="tarjeta-atraccion-imagen"><img src="' + foto + '" alt="' + nombre + '" loading="lazy" /></div>' +
        '<div class="tarjeta-atraccion-cuerpo">' +
          '<span class="tarjeta-atraccion-tipo">' + tipo + "</span>" +
          "<h3>" + nombre + "</h3>" +
          "<p>" + descripcion + "</p>" +
        "</div>" +
      "</div>"
    );
  }).join("");
}

function renderizarPasosFranja(contenedorId, pasos) {
  const contenedor = document.getElementById(contenedorId);
  if (!contenedor) return;

  if (!pasos || pasos.length === 0) {
    contenedor.innerHTML = '<p class="itinerario-paso-vacio">Sin actividades sugeridas en esta franja.</p>';
    return;
  }

  contenedor.innerHTML = pasos.map(function (paso) {
    const hora = paso.hora_sugerida ? '<span class="itinerario-paso-hora">' + escaparTextoAtracciones(paso.hora_sugerida) + "</span>" : "";
    const actividad = escaparTextoAtracciones(paso.actividad);
    const descripcion = paso.descripcion ? "<p>" + escaparTextoAtracciones(paso.descripcion) + "</p>" : "";
    return (
      '<div class="itinerario-paso">' +
        hora +
        "<h4>" + actividad + "</h4>" +
        descripcion +
      "</div>"
    );
  }).join("");
}

function renderizarItinerario(itinerario) {
  const total = (itinerario.manana || []).length + (itinerario.tarde || []).length + (itinerario.noche || []).length;
  const lineaEl = document.getElementById("itinerario-linea");
  const vacioEl = document.getElementById("itinerario-vacio");

  if (total === 0) {
    if (lineaEl) lineaEl.style.display = "none";
    if (vacioEl) vacioEl.style.display = "block";
    return;
  }

  renderizarPasosFranja("pasos-manana", itinerario.manana);
  renderizarPasosFranja("pasos-tarde", itinerario.tarde);
  renderizarPasosFranja("pasos-noche", itinerario.noche);
}


// ── Punto de entrada ───────────────────────────────────────────────────
protegerPagina();
mostrarNombreUsuario();

const parametrosAtracciones = new URLSearchParams(window.location.search);
const idDestinoAtracciones = parametrosAtracciones.get("id");
const destinoAtracciones = DESTINOS.find(function (d) { return d.id === idDestinoAtracciones; });

if (!destinoAtracciones) {
  window.location.href = "destinos.html";
} else {
  const puebloId = destinoAtracciones.pueblo_id || destinoAtracciones.id;

  document.getElementById("volver-destino").href = "destino.html?id=" + encodeURIComponent(destinoAtracciones.id);
  document.getElementById("atracciones-region").textContent = destinoAtracciones.region || "";
  document.getElementById("atracciones-titulo").textContent = "Atracciones y planes en " + destinoAtracciones.nombre;
  document.getElementById("atracciones-subtitulo").textContent = "Todo lo que puedes hacer en " + destinoAtracciones.nombre + ", más un itinerario sugerido de un día.";

  const enlaceWhatsapp = document.getElementById("whatsapp-atracciones");
  if (enlaceWhatsapp) {
    const mensaje = "¡Hola RinconesCol! Quiero armar un plan de un día en " + destinoAtracciones.nombre;
    enlaceWhatsapp.href = "https://wa.me/" + WHATSAPP_NUMERO_ATRACCIONES + "?text=" + encodeURIComponent(mensaje);
  }

  // Atracciones del pueblo
  const respuestaAtracciones = peticionSincrona("GET", "/atracciones/pueblo/" + encodeURIComponent(puebloId));
  if (respuestaAtracciones.body && respuestaAtracciones.body.success) {
    renderizarAtracciones(respuestaAtracciones.body.data);
  } else {
    renderizarAtracciones([]);
  }

  // Itinerario sugerido de 1 día, agrupado por franja (manana/tarde/noche)
  const respuestaItinerario = peticionSincrona("GET", "/itinerario/pueblo/" + encodeURIComponent(puebloId));
  if (respuestaItinerario.body && respuestaItinerario.body.success) {
    renderizarItinerario(respuestaItinerario.body.data || { manana: [], tarde: [], noche: [] });
  } else {
    renderizarItinerario({ manana: [], tarde: [], noche: [] });
  }
}
