// ── Reservas y reseñas de destino.html ───────────────────────────────────
// Reutiliza la sesión, token y funciones HTTP definidas en js/auth.js.

const WHATSAPP_NUMERO_RESERVAS = "573052369751";
const WHATSAPP_MENSAJE_RESERVAS = "¡Hola RinconesCol! Quiero más información sobre este destino";
const LIMITE_RESENAS_POR_PUEBLO = 3;

let resenasActuales = [];
let resenasExpandidas = false;
let puebloResenasActual = null;
let estadoLimiteResenas = null;

function escaparTexto(texto) {
  const div = document.createElement("div");
  div.textContent = texto == null ? "" : String(texto);
  return div.innerHTML;
}

function esAdministrador() {
  const usuario = typeof usuarioActual === "function" ? usuarioActual() : null;
  return Boolean(usuario && usuario.rol === "admin");
}

// ── Reservas por WhatsApp ───────────────────────────────────────────────
function inicializarReservaWhatsapp() {
  const enlace = document.getElementById("whatsapp-reserva");
  if (!enlace) return;
  enlace.href = "https://wa.me/" + WHATSAPP_NUMERO_RESERVAS + "?text=" + encodeURIComponent(WHATSAPP_MENSAJE_RESERVAS);
}

// ── Renderizado de reseñas ──────────────────────────────────────────────
function renderizarResenas(resenas) {
  const contenedor = document.getElementById("lista-resenas");
  const controles = document.getElementById("controles-resenas");
  if (!contenedor) return;

  resenasActuales = Array.isArray(resenas) ? resenas : [];

  if (resenasActuales.length === 0) {
    contenedor.innerHTML = '<p class="resenas-vacio">Aún no hay reseñas para este destino. ¡Sé el primero en compartir tu experiencia!</p>';
    if (controles) controles.innerHTML = "";
    return;
  }

  const resenasVisibles = resenasExpandidas
    ? resenasActuales
    : resenasActuales.slice(0, LIMITE_RESENAS_POR_PUEBLO);

  contenedor.innerHTML = resenasVisibles.map(function (r) {
    const calificacion = Math.max(0, Math.min(5, Number(r.calificacion) || 0));
    const estrellas = "★".repeat(calificacion) + "☆".repeat(5 - calificacion);
    const usuario = escaparTexto(r.usuario || "Viajero RinconesCol");
    const comentario = escaparTexto(r.comentario || "");
    const fecha = r.fecha ? '<span class="resena-fecha">' + escaparTexto(r.fecha) + "</span>" : "";
    const botonEliminar = esAdministrador()
      ? '<button type="button" class="boton-eliminar-resena" data-resena-id="' + Number(r.id) + '" aria-label="Eliminar reseña" title="Eliminar reseña"><i class="fa-solid fa-trash-can" aria-hidden="true"></i><span>Eliminar</span></button>'
      : "";

    return (
      '<article class="tarjeta-resena">' +
        '<div class="tarjeta-resena-cabecera">' +
          '<strong>' + usuario + "</strong>" +
          '<span class="estrellas-mostradas" aria-label="' + calificacion + ' de 5 estrellas">' + estrellas + "</span>" +
        "</div>" +
        '<p class="resena-comentario">' + comentario + "</p>" +
        '<div class="tarjeta-resena-pie">' + fecha + botonEliminar + "</div>" +
      "</article>"
    );
  }).join("");

  if (controles) {
    if (resenasActuales.length > LIMITE_RESENAS_POR_PUEBLO) {
      controles.innerHTML = '<button type="button" id="btn-ver-resenas" class="boton boton-secundario boton-ver-resenas">' +
        (resenasExpandidas ? "Ver menos" : "Ver todas las reseñas") + "</button>";
      document.getElementById("btn-ver-resenas").addEventListener("click", function () {
        resenasExpandidas = !resenasExpandidas;
        renderizarResenas(resenasActuales);
      });
    } else {
      controles.innerHTML = "";
    }
  }

  // Los controles de borrado solo existen en el DOM para ADMIN. El backend
  // vuelve a comprobar el rol antes de ejecutar DELETE.
  if (esAdministrador()) {
    contenedor.querySelectorAll(".boton-eliminar-resena").forEach(function (boton) {
      boton.addEventListener("click", function () {
        eliminarResenaComoAdmin(Number(boton.dataset.resenaId));
      });
    });
  }
}

function actualizarEstadoLimite(puebloId) {
  const mensaje = document.getElementById("resena-limite-mensaje");
  const boton = document.getElementById("btn-enviar-resena");
  const textarea = document.getElementById("comentario-resena");
  const selector = document.getElementById("selector-estrellas");
  const usuario = typeof usuarioActual === "function" ? usuarioActual() : null;

  if (!usuario || !puebloId || typeof peticionSincronaConToken !== "function") return;

  const respuesta = peticionSincronaConToken("GET", "/resenas/limite/" + encodeURIComponent(puebloId));
  if (!respuesta.body || !respuesta.body.success || !respuesta.body.data) return;

  estadoLimiteResenas = respuesta.body.data;
  const bloqueado = !estadoLimiteResenas.puede_publicar;

  if (mensaje) {
    mensaje.textContent = bloqueado
      ? "Has alcanzado el límite de 3 reseñas para este pueblo. Puedes seguir leyendo las opiniones publicadas."
      : "Te quedan " + estadoLimiteResenas.disponibles + " de 3 reseñas disponibles para este pueblo.";
    mensaje.classList.toggle("visible", bloqueado);
    mensaje.classList.toggle("informativo", !bloqueado);
  }
  if (boton) {
    boton.disabled = bloqueado;
    boton.textContent = bloqueado ? "Límite de reseñas alcanzado" : "Publicar reseña";
  }
  if (textarea) textarea.disabled = bloqueado;
  if (selector) {
    selector.classList.toggle("selector-bloqueado", bloqueado);
    selector.setAttribute("aria-disabled", bloqueado ? "true" : "false");
    selector.querySelectorAll("span").forEach(function (estrella) {
      estrella.setAttribute("aria-disabled", bloqueado ? "true" : "false");
      estrella.tabIndex = bloqueado ? -1 : 0;
    });
  }
}

function cargarResenas(puebloId) {
  const contenedor = document.getElementById("lista-resenas");
  if (!contenedor || !puebloId) return;

  const respuesta = peticionSincrona("GET", "/resenas/?pueblo_id=" + encodeURIComponent(puebloId));
  if (respuesta.body && respuesta.body.success) {
    renderizarResenas(respuesta.body.data);
  } else {
    renderizarResenas([]);
  }
  actualizarEstadoLimite(puebloId);
}

function eliminarResenaComoAdmin(resenaId) {
  if (!esAdministrador()) {
    mostrarErrorResena("Solo un administrador puede eliminar reseñas.");
    return;
  }

  const confirmar = window.confirm("¿Estás seguro de que deseas eliminar esta reseña? Esta acción también la borrará de la base de datos y no se puede deshacer.");
  if (!confirmar) return;

  const respuesta = peticionSincronaConToken("DELETE", "/resenas/" + encodeURIComponent(resenaId));
  if (respuesta.error || !respuesta.body || !respuesta.body.success) {
    const detalle = respuesta.body && (respuesta.body.message || respuesta.body.detail);
    mostrarErrorResena(detalle || "No se pudo eliminar la reseña. Verifica tus permisos e inténtalo de nuevo.");
    return;
  }

  // Actualiza la vista sin recargar el documento.
  resenasActuales = resenasActuales.filter(function (resena) {
    return Number(resena.id) !== resenaId;
  });
  if (resenasActuales.length <= LIMITE_RESENAS_POR_PUEBLO) resenasExpandidas = false;
  renderizarResenas(resenasActuales);
  cargarEstadoLimiteResenasTrasCambio();
  mostrarExitoResena("La reseña fue eliminada correctamente.");
}

function cargarEstadoLimiteResenasTrasCambio() {
  if (puebloResenasActual) actualizarEstadoLimite(puebloResenasActual);
}

// ── Selector de estrellas ───────────────────────────────────────────────
function inicializarSelectorEstrellas() {
  const selector = document.getElementById("selector-estrellas");
  if (!selector) return;
  const estrellas = selector.querySelectorAll("span");

  function pintarHasta(valor) {
    estrellas.forEach(function (estrella) {
      estrella.classList.toggle("activa", Number(estrella.dataset.valor) <= valor);
    });
  }

  estrellas.forEach(function (estrella) {
    estrella.addEventListener("click", function () {
      if (estadoLimiteResenas && !estadoLimiteResenas.puede_publicar) return;
      selector.dataset.calificacion = estrella.dataset.valor;
      pintarHasta(Number(estrella.dataset.valor));
    });
    estrella.addEventListener("mouseenter", function () {
      if (!(estadoLimiteResenas && !estadoLimiteResenas.puede_publicar)) {
        pintarHasta(Number(estrella.dataset.valor));
      }
    });
  });

  selector.addEventListener("mouseleave", function () {
    pintarHasta(Number(selector.dataset.calificacion || 0));
  });
}

function inicializarContadorComentario() {
  const textarea = document.getElementById("comentario-resena");
  const contador = document.getElementById("contador-actual");
  if (!textarea || !contador) return;
  textarea.addEventListener("input", function () {
    contador.textContent = textarea.value.length;
  });
}

// ── Mensajes del formulario ─────────────────────────────────────────────
function mostrarErrorResena(mensaje) {
  const error = document.getElementById("resena-mensaje-error");
  const exito = document.getElementById("resena-mensaje-exito");
  if (exito) exito.classList.remove("visible");
  if (error) {
    error.textContent = mensaje;
    error.classList.add("visible");
  }
}

function mostrarExitoResena(mensaje) {
  const error = document.getElementById("resena-mensaje-error");
  const exito = document.getElementById("resena-mensaje-exito");
  if (error) error.classList.remove("visible");
  if (exito) {
    exito.textContent = mensaje;
    exito.classList.add("visible");
  }
}

// ── Publicación ─────────────────────────────────────────────────────────
function inicializarEnvioResena(puebloId) {
  const boton = document.getElementById("btn-enviar-resena");
  if (!boton) return;

  boton.addEventListener("click", function () {
    if (!usuarioActual()) {
      window.location.href = "login.html?redirect=" + encodeURIComponent("destino.html" + window.location.search);
      return;
    }

    if (estadoLimiteResenas && !estadoLimiteResenas.puede_publicar) {
      mostrarErrorResena("Ya alcanzaste el máximo de 3 reseñas para este pueblo.");
      return;
    }

    const selector = document.getElementById("selector-estrellas");
    const textarea = document.getElementById("comentario-resena");
    const calificacion = Number((selector && selector.dataset.calificacion) || 0);
    const comentario = textarea ? textarea.value.trim() : "";

    if (calificacion < 1 || calificacion > 5) {
      mostrarErrorResena("Selecciona una calificación de 1 a 5 estrellas.");
      return;
    }
    if (!comentario) {
      mostrarErrorResena("Escribe un comentario antes de enviar tu reseña.");
      return;
    }
    if (comentario.length > 500) {
      mostrarErrorResena("El comentario no puede superar los 500 caracteres.");
      return;
    }

    boton.disabled = true;
    const textoOriginalBoton = boton.textContent;
    boton.textContent = "Enviando...";

    const respuesta = peticionSincronaConToken("POST", "/resenas/", {
      comentario: comentario,
      calificacion: calificacion,
      pueblo_id: puebloId
    });

    boton.disabled = false;
    boton.textContent = textoOriginalBoton;

    if (respuesta.error || !respuesta.body || !respuesta.body.success) {
      const mensaje = (respuesta.body && (respuesta.body.message || respuesta.body.detail)) || "No se pudo enviar tu reseña. Intenta de nuevo.";
      mostrarErrorResena(mensaje);
      if (respuesta.status === 409) actualizarEstadoLimite(puebloId);
      return;
    }

    mostrarExitoResena("¡Gracias por tu reseña! Ya quedó publicada.");
    if (textarea) textarea.value = "";
    const contador = document.getElementById("contador-actual");
    if (contador) contador.textContent = "0";
    if (selector) {
      selector.dataset.calificacion = "0";
      selector.querySelectorAll("span").forEach(function (e) { e.classList.remove("activa"); });
    }

    cargarResenas(puebloId);
  });
}

// ── Inicio del bloque de destino ────────────────────────────────────────
function inicializarBloqueDestino(destino) {
  if (!destino) return;
  puebloResenasActual = destino.pueblo_id || destino.id;

  inicializarReservaWhatsapp();
  inicializarSelectorEstrellas();
  inicializarContadorComentario();
  inicializarEnvioResena(puebloResenasActual);
  cargarResenas(puebloResenasActual);
}
