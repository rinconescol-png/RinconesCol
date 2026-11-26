// ── negocio-panel.js ────────────────────────────────────────────────────
// Lógica de panel-socio.html. Depende de las funciones globales de
// js/auth.js (auth.js debe cargarse ANTES que este archivo).

const ETIQUETAS_CATEGORIA = {
  restaurante: "Restaurante",
  hotel: "Hotel / Posada",
  cafeteria: "Cafetería",
  experiencia: "Experiencia turística",
  artesania: "Artesanías / Emprendimiento"
};

let negocioActual = null;
let itemEnEdicion = null;

// ── Foto de portada por archivo (igual que en perfil.js) ────────────────
const TIPOS_IMAGEN_VALIDOS_PANEL = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"];
const EXTENSIONES_IMAGEN_VALIDAS_PANEL = [".jpg", ".jpeg", ".png", ".webp", ".gif"];
const TAMANO_MAXIMO_FOTO_PANEL = 2 * 1024 * 1024; // 2 MB
let fotoPortadaNuevaBase64 = null; // solo se llena si el socio elige un archivo nuevo válido
let fotoGaleriaNuevaBase64 = null; // foto nueva para la galería
let fotoItemNuevaBase64 = null;    // foto nueva para el plato/ítem
let fotoItemActual = null;         // foto ya guardada del ítem que se está editando

function extensionValidaPanel(nombreArchivo) {
  const nombre = (nombreArchivo || "").toLowerCase();
  return EXTENSIONES_IMAGEN_VALIDAS_PANEL.some(function (ext) { return nombre.endsWith(ext); });
}

// Valida un archivo de imagen local y lo devuelve como data URL (base64).
// Llama a alAceptar(dataUrl) si todo sale bien; si no, muestra el error y limpia el input.
function leerImagenLocal(input, alAceptar, alLimpiar) {
  const archivo = input.files && input.files[0];
  if (!archivo) {
    if (alLimpiar) alLimpiar();
    return;
  }
  const tipoValido = TIPOS_IMAGEN_VALIDOS_PANEL.indexOf(archivo.type) !== -1 || extensionValidaPanel(archivo.name);
  if (!tipoValido) {
    mostrarErrorPanel("Elige un archivo de imagen válido (JPG, PNG, WEBP o GIF).");
    input.value = "";
    if (alLimpiar) alLimpiar();
    return;
  }
  if (archivo.size > TAMANO_MAXIMO_FOTO_PANEL) {
    mostrarErrorPanel("La imagen es muy pesada. El tamaño máximo permitido es 2 MB.");
    input.value = "";
    if (alLimpiar) alLimpiar();
    return;
  }
  const lector = new FileReader();
  lector.onload = function () { alAceptar(lector.result); };
  lector.onerror = function () {
    mostrarErrorPanel("No se pudo leer la imagen seleccionada. Intenta con otro archivo.");
    input.value = "";
    if (alLimpiar) alLimpiar();
  };
  lector.readAsDataURL(archivo);
}

function actualizarVistaItemFoto(url) {
  const contenedor = document.getElementById("vista-item-foto");
  const img = document.getElementById("vista-item-foto-img");
  if (url) {
    img.src = url;
    contenedor.style.display = "";
  } else {
    contenedor.style.display = "none";
  }
}

function actualizarVistaPortada(url) {
  const contenedor = document.getElementById("vista-portada-negocio");
  const img = document.getElementById("vista-portada-negocio-img");
  if (url) {
    img.src = url;
    contenedor.style.display = "";
  } else {
    contenedor.style.display = "none";
  }
}

function escaparTextoPanel(texto) {
  const div = document.createElement("div");
  div.textContent = texto == null ? "" : String(texto);
  return div.innerHTML;
}

function mostrarErrorPanel(mensaje) {
  const caja = document.getElementById("error-panel");
  caja.textContent = mensaje;
  caja.classList.add("visible");
  setTimeout(function () { caja.classList.remove("visible"); }, 4000);
}

function mostrarExitoPanel() {
  const caja = document.getElementById("exito-panel");
  caja.classList.add("visible");
  setTimeout(function () { caja.classList.remove("visible"); }, 2500);
}

function renderizarFotos() {
  const contenedor = document.getElementById("lista-fotos");
  const fotos = negocioActual.fotos || [];

  if (fotos.length === 0) {
    contenedor.innerHTML = '<p class="sin-fotos">Todavía no has agregado fotos.</p>';
    return;
  }

  contenedor.innerHTML = fotos.map(function (foto) {
    return (
      '<div class="tarjeta-foto">' +
        '<img src="' + foto.url + '" alt="Foto de ' + escaparTextoPanel(negocioActual.nombre) + '" loading="lazy" />' +
        '<button type="button" class="boton-quitar" data-foto-id="' + foto.id + '" title="Eliminar foto">✕</button>' +
      "</div>"
    );
  }).join("");

  contenedor.querySelectorAll(".boton-quitar").forEach(function (boton) {
    boton.addEventListener("click", function () {
      if (!confirm("¿Eliminar esta foto?")) return;
      const resultado = eliminarFotoNegocio(boton.dataset.fotoId);
      if (!resultado.ok) {
        mostrarErrorPanel(resultado.error);
        return;
      }
      negocioActual.fotos = negocioActual.fotos.filter(function (f) { return String(f.id) !== String(boton.dataset.fotoId); });
      renderizarFotos();
      mostrarExitoPanel();
    });
  });
}

function renderizarItems() {
  const contenedor = document.getElementById("lista-items");
  const items = negocioActual.items || [];

  if (items.length === 0) {
    contenedor.innerHTML = '<p class="sin-items">Todavía no has agregado platos, productos o servicios.</p>';
    return;
  }

  contenedor.innerHTML = items.map(function (item) {
    const foto = item.foto
      ? '<img src="' + item.foto + '" alt="' + escaparTextoPanel(item.nombre) + '" />'
      : "";
    const precio = (item.precio !== null && item.precio !== undefined)
      ? '<p class="tarjeta-item-precio">$' + Number(item.precio).toLocaleString("es-CO") + "</p>"
      : "";
    return (
      '<div class="tarjeta-item">' +
        foto +
        '<div class="tarjeta-item-cuerpo">' +
          "<h4>" + escaparTextoPanel(item.nombre) + "</h4>" +
          (item.descripcion ? "<p>" + escaparTextoPanel(item.descripcion) + "</p>" : "") +
          precio +
        "</div>" +
        '<div class="tarjeta-item-acciones">' +
          '<button type="button" class="boton-editar" data-item-id="' + item.id + '">Editar</button>' +
          '<button type="button" class="boton-eliminar" data-item-id="' + item.id + '">Eliminar</button>' +
        "</div>" +
      "</div>"
    );
  }).join("");

  contenedor.querySelectorAll(".boton-editar").forEach(function (boton) {
    boton.addEventListener("click", function () {
      const item = negocioActual.items.find(function (i) { return String(i.id) === String(boton.dataset.itemId); });
      if (!item) return;
      itemEnEdicion = item.id;
      document.getElementById("item-id").value = item.id;
      document.getElementById("item-nombre").value = item.nombre || "";
      document.getElementById("item-precio").value = item.precio != null ? item.precio : "";
      document.getElementById("item-descripcion").value = item.descripcion || "";
      document.getElementById("item-foto-archivo").value = "";
      fotoItemNuevaBase64 = null;
      fotoItemActual = item.foto || null;
      actualizarVistaItemFoto(fotoItemActual);
      document.getElementById("boton-guardar-item").textContent = "Guardar cambios";
      document.getElementById("boton-cancelar-item").style.display = "";
      window.scrollTo({ top: document.getElementById("form-item").offsetTop - 100, behavior: "smooth" });
    });
  });

  contenedor.querySelectorAll(".boton-eliminar").forEach(function (boton) {
    boton.addEventListener("click", function () {
      if (!confirm("¿Eliminar este ítem?")) return;
      const resultado = eliminarItemNegocio(boton.dataset.itemId);
      if (!resultado.ok) {
        mostrarErrorPanel(resultado.error);
        return;
      }
      negocioActual.items = negocioActual.items.filter(function (i) { return String(i.id) !== String(boton.dataset.itemId); });
      renderizarItems();
      mostrarExitoPanel();
    });
  });
}

function cancelarEdicionItem() {
  itemEnEdicion = null;
  document.getElementById("form-item").reset();
  document.getElementById("item-id").value = "";
  fotoItemNuevaBase64 = null;
  fotoItemActual = null;
  actualizarVistaItemFoto(null);
  document.getElementById("boton-guardar-item").textContent = "Agregar";
  document.getElementById("boton-cancelar-item").style.display = "none";
}

function pintarNegocio() {
  document.getElementById("negocio-nombre").textContent = negocioActual.nombre;
  document.getElementById("negocio-categoria").textContent = ETIQUETAS_CATEGORIA[negocioActual.categoria] || "Negocio aliado";
  document.getElementById("negocio-pueblo").textContent = negocioActual.pueblo_nombre || "";
  document.getElementById("negocio-ubicacion").value = negocioActual.ubicacion || "";
  document.getElementById("negocio-descripcion").value = negocioActual.descripcion || "";
  actualizarVistaPortada(negocioActual.foto);

  renderizarFotos();
  renderizarItems();
}

document.addEventListener("DOMContentLoaded", function () {
  if (!protegerPaginaSocio()) return;
  mostrarNombreUsuario();

  const resultado = obtenerMiNegocio();

  document.getElementById("cargando-negocio").style.display = "none";

  if (!resultado.ok) {
    if (resultado.status === 404) {
      document.getElementById("sin-negocio").style.display = "";
    } else {
      mostrarErrorPanel(resultado.error || "No se pudo cargar tu negocio.");
    }
    return;
  }

  negocioActual = resultado.data;
  document.getElementById("contenido-negocio").style.display = "";
  pintarNegocio();

  // ── Elegir portada desde el dispositivo: validar y previsualizar ──────
  document.getElementById("negocio-foto-portada-archivo").addEventListener("change", function (evento) {
    leerImagenLocal(evento.target, function (dataUrl) {
      fotoPortadaNuevaBase64 = dataUrl;
      actualizarVistaPortada(dataUrl);
    }, function () {
      fotoPortadaNuevaBase64 = null;
      actualizarVistaPortada(negocioActual.foto);
    });
  });

  // ── Elegir foto de galería ───────────────────────────────────────────
  document.getElementById("nueva-foto-archivo").addEventListener("change", function (evento) {
    leerImagenLocal(evento.target, function (dataUrl) {
      fotoGaleriaNuevaBase64 = dataUrl;
    }, function () {
      fotoGaleriaNuevaBase64 = null;
    });
  });

  // ── Elegir foto del plato / ítem ─────────────────────────────────────
  document.getElementById("item-foto-archivo").addEventListener("change", function (evento) {
    leerImagenLocal(evento.target, function (dataUrl) {
      fotoItemNuevaBase64 = dataUrl;
      actualizarVistaItemFoto(dataUrl);
    }, function () {
      fotoItemNuevaBase64 = null;
      actualizarVistaItemFoto(fotoItemActual);
    });
  });

  // ── Guardar descripción / foto de portada ──────────────────────────────
  document.getElementById("form-negocio").addEventListener("submit", function (evento) {
    evento.preventDefault();
    const cambios = {
      descripcion: document.getElementById("negocio-descripcion").value.trim(),
      ubicacion: document.getElementById("negocio-ubicacion").value.trim(),
      // Si no se eligió archivo nuevo, se conserva la portada actual.
      foto: fotoPortadaNuevaBase64 || negocioActual.foto || ""
    };
    const res = actualizarMiNegocio(cambios);
    if (!res.ok) {
      mostrarErrorPanel(res.error);
      return;
    }
    negocioActual.descripcion = cambios.descripcion;
    negocioActual.ubicacion = cambios.ubicacion;
    negocioActual.foto = cambios.foto;
    fotoPortadaNuevaBase64 = null;
    document.getElementById("negocio-foto-portada-archivo").value = "";
    actualizarVistaPortada(cambios.foto);
    mostrarExitoPanel();
  });

  // ── Agregar foto ─────────────────────────────────────────────────────
  document.getElementById("form-foto").addEventListener("submit", function (evento) {
    evento.preventDefault();
    const input = document.getElementById("nueva-foto-archivo");
    if (!fotoGaleriaNuevaBase64) {
      mostrarErrorPanel("Primero elige una foto desde tu equipo.");
      return;
    }
    const url = fotoGaleriaNuevaBase64;

    const res = agregarFotoNegocio(url);
    if (!res.ok) {
      mostrarErrorPanel(res.error);
      return;
    }
    negocioActual.fotos = negocioActual.fotos || [];
    negocioActual.fotos.push({ id: res.data.id, url: url, orden: negocioActual.fotos.length });
    fotoGaleriaNuevaBase64 = null;
    input.value = "";
    renderizarFotos();
    mostrarExitoPanel();
  });

  // ── Crear / editar ítem ──────────────────────────────────────────────
  document.getElementById("form-item").addEventListener("submit", function (evento) {
    evento.preventDefault();

    const precioValor = document.getElementById("item-precio").value;
    const item = {
      nombre: document.getElementById("item-nombre").value.trim(),
      descripcion: document.getElementById("item-descripcion").value.trim() || null,
      precio: precioValor === "" ? null : Number(precioValor),
      foto: fotoItemNuevaBase64 || fotoItemActual || null,
      orden: 0
    };

    if (itemEnEdicion) {
      const res = actualizarItemNegocio(itemEnEdicion, item);
      if (!res.ok) {
        mostrarErrorPanel(res.error);
        return;
      }
      const idx = negocioActual.items.findIndex(function (i) { return String(i.id) === String(itemEnEdicion); });
      if (idx !== -1) negocioActual.items[idx] = Object.assign({ id: itemEnEdicion }, item);
    } else {
      const res = crearItemNegocio(item);
      if (!res.ok) {
        mostrarErrorPanel(res.error);
        return;
      }
      negocioActual.items = negocioActual.items || [];
      negocioActual.items.push(Object.assign({ id: res.data.id }, item));
    }

    cancelarEdicionItem();
    renderizarItems();
    mostrarExitoPanel();
  });

  document.getElementById("boton-cancelar-item").addEventListener("click", cancelarEdicionItem);
});
