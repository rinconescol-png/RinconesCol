// ── perfil.js ────────────────────────────────────────────────────────────
// Lógica de perfil.html: ver y editar el nombre y la foto de perfil del
// usuario que inició sesión (admin, visitante o socio). Depende de las
// funciones globales de js/auth.js (auth.js debe cargarse ANTES que este
// archivo).

const ETIQUETAS_ROL_PERFIL = {
  admin: "Administrador",
  visitante: "Viajero",
  socio: "Socio"
};

// Se valida tanto el "type" del archivo como su extensión, porque algunos
// navegadores/sistemas no siempre entregan un "type" MIME confiable.
const TIPOS_IMAGEN_VALIDOS = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"];
const EXTENSIONES_IMAGEN_VALIDAS = [".jpg", ".jpeg", ".png", ".webp", ".gif"];
const TAMANO_MAXIMO_FOTO = 2 * 1024 * 1024; // 2 MB

let perfilActual = null;
let fotoNuevaBase64 = null; // solo se llena si el usuario elige un archivo nuevo válido

function escaparTextoPerfil(texto) {
  const div = document.createElement("div");
  div.textContent = texto == null ? "" : String(texto);
  return div.innerHTML;
}

function mostrarErrorPerfil(mensaje) {
  const caja = document.getElementById("error-perfil");
  caja.textContent = mensaje;
  caja.classList.add("visible");
  setTimeout(function () { caja.classList.remove("visible"); }, 4000);
}

function mostrarExitoPerfil() {
  const caja = document.getElementById("exito-perfil");
  caja.classList.add("visible");
  setTimeout(function () { caja.classList.remove("visible"); }, 2500);
}

function inicialNombre(nombre) {
  const limpio = (nombre || "").trim();
  return limpio ? limpio.charAt(0).toUpperCase() : "?";
}

function pintarAvatar(contenedorId, foto, nombre) {
  const contenedor = document.getElementById(contenedorId);
  if (foto) {
    contenedor.innerHTML = '<img src="' + foto + '" alt="Foto de perfil" />';
  } else {
    contenedor.innerHTML = '<span class="avatar-inicial">' + escaparTextoPerfil(inicialNombre(nombre)) + "</span>";
  }
}

function pintarPerfil() {
  document.getElementById("perfil-nombre").textContent = perfilActual.nombre;
  document.getElementById("perfil-correo").textContent = perfilActual.correo;
  document.getElementById("perfil-rol").textContent = ETIQUETAS_ROL_PERFIL[perfilActual.rol] || perfilActual.rol;
  pintarAvatar("avatar-vista", perfilActual.foto_perfil, perfilActual.nombre);
  pintarAvatar("avatar-formulario", perfilActual.foto_perfil, perfilActual.nombre);
  document.getElementById("input-nombre").value = perfilActual.nombre || "";
}

function mostrarFormularioEdicion() {
  fotoNuevaBase64 = null;
  document.getElementById("input-foto").value = "";
  document.getElementById("vista-perfil").style.display = "none";
  document.getElementById("formulario-perfil").style.display = "flex";
}

function ocultarFormularioEdicion() {
  fotoNuevaBase64 = null;
  document.getElementById("formulario-perfil").style.display = "none";
  document.getElementById("vista-perfil").style.display = "flex";
  pintarPerfil(); // por si había una previsualización de foto sin guardar
}

function extensionValida(nombreArchivo) {
  const nombre = (nombreArchivo || "").toLowerCase();
  return EXTENSIONES_IMAGEN_VALIDAS.some(function (ext) { return nombre.endsWith(ext); });
}

document.addEventListener("DOMContentLoaded", function () {
  protegerPagina();
  mostrarNombreUsuario();

  const resultado = obtenerMiPerfil();
  document.getElementById("cargando-perfil").style.display = "none";

  if (!resultado.ok) {
    mostrarErrorPerfil(resultado.error || "No se pudo cargar tu perfil.");
    return;
  }

  perfilActual = resultado.data;
  document.getElementById("contenido-perfil").style.display = "";
  pintarPerfil();

  document.getElementById("boton-editar-perfil").addEventListener("click", mostrarFormularioEdicion);
  document.getElementById("boton-cancelar-perfil").addEventListener("click", ocultarFormularioEdicion);

  // ── Elegir foto desde el dispositivo: validar y previsualizar ─────────
  document.getElementById("input-foto").addEventListener("change", function (evento) {
    const archivo = evento.target.files && evento.target.files[0];
    if (!archivo) {
      fotoNuevaBase64 = null;
      return;
    }

    const tipoValido = TIPOS_IMAGEN_VALIDOS.indexOf(archivo.type) !== -1 || extensionValida(archivo.name);
    if (!tipoValido) {
      mostrarErrorPerfil("Elige un archivo de imagen válido (JPG, PNG, WEBP o GIF).");
      evento.target.value = "";
      fotoNuevaBase64 = null;
      return;
    }

    if (archivo.size > TAMANO_MAXIMO_FOTO) {
      mostrarErrorPerfil("La imagen es muy pesada. El tamaño máximo permitido es 2 MB.");
      evento.target.value = "";
      fotoNuevaBase64 = null;
      return;
    }

    const lector = new FileReader();
    lector.onload = function () {
      fotoNuevaBase64 = lector.result;
      pintarAvatar("avatar-formulario", fotoNuevaBase64, perfilActual.nombre);
    };
    lector.onerror = function () {
      mostrarErrorPerfil("No se pudo leer la imagen seleccionada. Intenta con otro archivo.");
      evento.target.value = "";
      fotoNuevaBase64 = null;
    };
    lector.readAsDataURL(archivo);
  });

  // ── Guardar cambios ─────────────────────────────────────────────────
  document.getElementById("formulario-perfil").addEventListener("submit", function (evento) {
    evento.preventDefault();

    const nombreNuevo = document.getElementById("input-nombre").value.trim();
    if (!nombreNuevo) {
      mostrarErrorPerfil("El nombre no puede quedar vacío.");
      return;
    }

    // Solo se envía lo que realmente cambió; si el usuario no tocó un
    // campo, el backend conserva lo que ya tenía guardado.
    const cambios = {};
    if (nombreNuevo !== perfilActual.nombre) cambios.nombre = nombreNuevo;
    if (fotoNuevaBase64) cambios.foto_perfil = fotoNuevaBase64;

    if (Object.keys(cambios).length === 0) {
      ocultarFormularioEdicion();
      return;
    }

    const res = actualizarMiPerfil(cambios);
    if (!res.ok) {
      mostrarErrorPerfil(res.error);
      return;
    }

    perfilActual.nombre = res.data.nombre;
    perfilActual.foto_perfil = res.data.foto_perfil;

    // El "Hola, X" de la navbar y la sesión guardada también se actualizan,
    // así que el cambio se ve de inmediato en toda la página. El dato real
    // vive en la base de datos, por eso sigue igual aunque cierre sesión y
    // vuelva a entrar.
    actualizarSesionLocal({ nombre: perfilActual.nombre, foto_perfil: perfilActual.foto_perfil });
    mostrarNombreUsuario();

    ocultarFormularioEdicion();
    mostrarExitoPerfil();
  });
});
