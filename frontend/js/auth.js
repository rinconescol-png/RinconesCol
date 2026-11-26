
// ── Conexión con el backend real (FastAPI + PostgreSQL) ─────────────────────
// Cambia esta URL si tu API corre en otro host/puerto.
const API_BASE_URL = "http://127.0.0.1:8000";

const CLAVE_SESION = "rinconescol_sesion";


// Petición HTTP síncrona (misma técnica que usan los <script> normales de
// esta página: nada aquí es async/await para no tener que tocar el HTML,
// que llama a estas funciones esperando una respuesta inmediata).
function peticionSincrona(metodo, ruta, cuerpo) {
  const xhr = new XMLHttpRequest();
  xhr.open(metodo, API_BASE_URL + ruta, false); // false = síncrona
  xhr.setRequestHeader("Content-Type", "application/json");
  try {
    xhr.send(cuerpo ? JSON.stringify(cuerpo) : null);
  } catch (e) {
    return { status: 0, body: null, error: "No se pudo conectar con el servidor. Verifica que el backend esté corriendo en " + API_BASE_URL };
  }

  let data = null;
  try {
    data = xhr.responseText ? JSON.parse(xhr.responseText) : null;
  } catch (e) {
    data = null;
  }

  return { status: xhr.status, body: data };
}


// Igual que peticionSincrona, pero agrega el header "Authorization: Bearer"
// con el token del usuario logueado. Se usa para endpoints protegidos como
// crear una reseña (POST /resenas/), donde el backend necesita saber quién
// es el usuario que está escribiendo.
function peticionSincronaConToken(metodo, ruta, cuerpo) {
  const token = tokenActual();
  const xhr = new XMLHttpRequest();
  xhr.open(metodo, API_BASE_URL + ruta, false); // false = síncrona
  xhr.setRequestHeader("Content-Type", "application/json");
  if (token) {
    xhr.setRequestHeader("Authorization", "Bearer " + token);
  }
  try {
    xhr.send(cuerpo ? JSON.stringify(cuerpo) : null);
  } catch (e) {
    return { status: 0, body: null, error: "No se pudo conectar con el servidor. Verifica que el backend esté corriendo en " + API_BASE_URL };
  }

  let data = null;
  try {
    data = xhr.responseText ? JSON.parse(xhr.responseText) : null;
  } catch (e) {
    data = null;
  }

  return { status: xhr.status, body: data };
}


function guardarSesion(usuario, token) {
  localStorage.setItem(CLAVE_SESION, JSON.stringify({
    id: usuario.id,
    nombre: usuario.nombre,
    correo: usuario.correo,
    rol: usuario.rol,
    foto_perfil: usuario.foto_perfil || null,
    access_token: token
  }));
}


// Actualiza solo los campos indicados de la sesión ya guardada en
// localStorage (por ejemplo, después de editar el perfil), sin perder el
// token de acceso ni el resto de los datos de la sesión.
function actualizarSesionLocal(cambios) {
  const usuario = usuarioActual();
  if (!usuario) return;
  Object.assign(usuario, cambios);
  localStorage.setItem(CLAVE_SESION, JSON.stringify(usuario));
}


function registrarUsuario(nombre, correo, contrasena) {
  const respuesta = peticionSincrona("POST", "/auth/register", {
    nombre: nombre,
    correo: correo,
    contrasena: contrasena
  });

  if (respuesta.error) {
    return { ok: false, error: respuesta.error };
  }

  if (!respuesta.body) {
    return { ok: false, error: "Respuesta inesperada del servidor." };
  }

  if (!respuesta.body.success) {
    return { ok: false, error: respuesta.body.message || "No se pudo registrar el usuario." };
  }

  const datos = respuesta.body.data || {};
  guardarSesion(
    { id: datos.usuario_id, nombre: nombre, correo: correo, rol: "visitante" },
    datos.access_token
  );

  return { ok: true };
}


function iniciarSesion(correo, contrasena) {
  const respuesta = peticionSincrona("POST", "/auth/login", {
    correo: correo,
    contrasena: contrasena
  });

  if (respuesta.error) {
    return { ok: false, error: respuesta.error };
  }

  if (!respuesta.body) {
    return { ok: false, error: "Respuesta inesperada del servidor." };
  }

  if (!respuesta.body.success) {
    return { ok: false, error: respuesta.body.message || "Correo o contraseña incorrectos." };
  }

  const datos = respuesta.body.data || {};
  guardarSesion(datos.usuario || { nombre: correo, correo: correo }, datos.access_token);

  return { ok: true };
}


function cerrarSesion() {
  localStorage.removeItem(CLAVE_SESION);
  window.location.href = "login.html";
}


function usuarioActual() {
  const datos = localStorage.getItem(CLAVE_SESION);
  return datos ? JSON.parse(datos) : null;
}


function tokenActual() {
  const usuario = usuarioActual();
  return usuario ? usuario.access_token : null;
}


function protegerPagina() {
  if (!usuarioActual()) {
    const paginaActual = window.location.pathname.split("/").pop() + window.location.search;
    window.location.href = "login.html?redirect=" + encodeURIComponent(paginaActual);
  }
}


function requerirSesion(paginaDeRetorno) {
  if (!usuarioActual()) {
    window.location.href = "login.html?redirect=" + encodeURIComponent(paginaDeRetorno);
    return false;
  }
  return true;
}


function mostrarNombreUsuario() {
  const usuario = usuarioActual();
  const elemento = document.getElementById("nombre-usuario");
  if (usuario && elemento) {
    elemento.textContent = usuario.nombre;
  }

  // Si el que inició sesión es un Socio, le agregamos un enlace a su panel
  // de negocio junto a su nombre, sin tener que editar la navbar de cada
  // página HTML una por una. Se agrega SIEMPRE (incluida panel-socio.html),
  // para que el encabezado "Hola, [nombre] | Mi negocio | Salir" se vea
  // exactamente igual en todas las secciones a las que el socio entra.
  if (usuario && usuario.rol === "socio" && elemento) {
    const paginaActual = window.location.pathname.split("/").pop();
    if (!document.getElementById("enlace-panel-socio")) {
      const enlace = document.createElement("a");
      enlace.id = "enlace-panel-socio";
      enlace.href = "panel-socio.html";
      enlace.textContent = "Mi negocio";
      enlace.style.fontWeight = "600";
      enlace.style.color = "var(--oro-claro)";
      enlace.style.marginRight = "4px";
      if (paginaActual === "panel-socio.html") {
        enlace.style.textDecoration = "underline";
      }
      const contenedorUsuario = elemento.closest(".nav-usuario");
      if (contenedorUsuario) {
        contenedorUsuario.insertBefore(enlace, contenedorUsuario.querySelector(".enlace-salir"));
      }
    }
  }

  // Igual, pero para un Admin: enlace a panel-admin.html.
  if (usuario && usuario.rol === "admin" && elemento) {
    const paginaActual = window.location.pathname.split("/").pop();
    if (paginaActual !== "panel-admin.html" && !document.getElementById("enlace-panel-admin")) {
      const enlace = document.createElement("a");
      enlace.id = "enlace-panel-admin";
      enlace.href = "panel-admin.html";
      enlace.textContent = "Panel Admin";
      enlace.style.fontWeight = "600";
      enlace.style.color = "var(--oro-claro)";
      enlace.style.marginRight = "4px";
      const contenedorUsuario = elemento.closest(".nav-usuario");
      if (contenedorUsuario) {
        contenedorUsuario.insertBefore(enlace, contenedorUsuario.querySelector(".enlace-salir"));
      }
    }
  }

  // "Mi perfil": para CUALQUIER usuario logueado (admin, visitante o
  // socio), igual que los enlaces de arriba, para no tener que tocar la
  // navbar de cada página HTML una por una.
  if (usuario && elemento) {
    const paginaActual = window.location.pathname.split("/").pop();
    if (paginaActual !== "perfil.html" && !document.getElementById("enlace-perfil")) {
      const enlace = document.createElement("a");
      enlace.id = "enlace-perfil";
      enlace.href = "perfil.html";
      enlace.textContent = "Mi perfil";
      enlace.style.fontWeight = "600";
      enlace.style.color = "var(--oro-claro)";
      enlace.style.marginRight = "4px";
      const contenedorUsuario = elemento.closest(".nav-usuario");
      if (contenedorUsuario) {
        contenedorUsuario.insertBefore(enlace, contenedorUsuario.querySelector(".enlace-salir"));
      }
    }
  }
}


// ── Perfil propio: ver y editar nombre / foto (perfil.html) ─────────────────
// Cualquier usuario autenticado (admin, visitante o socio) usa estas dos
// funciones para SU PROPIO perfil; el backend resuelve el usuario a partir
// del token, nunca de un id que se le pase desde aquí.

function obtenerMiPerfil() {
  const respuesta = peticionSincronaConToken("GET", "/usuarios/perfil/me");
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body) return { ok: false, error: "Respuesta inesperada del servidor." };
  if (!respuesta.body.success) return { ok: false, error: respuesta.body.message, status: respuesta.status };
  return { ok: true, data: respuesta.body.data };
}

function actualizarMiPerfil(cambios) {
  const respuesta = peticionSincronaConToken("PUT", "/usuarios/perfil/me", cambios);
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo guardar tu perfil." };
  }
  return { ok: true, data: respuesta.body.data };
}


// ── Panel de Socio: solo el negocio del usuario logueado ────────────────────
// Todas estas funciones usan peticionSincronaConToken, que manda el JWT del
// socio autenticado; el backend resuelve el negocio a partir de ese token,
// nunca de un id que se le pase desde aquí.

function protegerPaginaSocio() {
  const usuario = usuarioActual();
  if (!usuario) {
    window.location.href = "login.html?redirect=" + encodeURIComponent("panel-socio.html");
    return false;
  }
  if (usuario.rol !== "socio") {
    window.location.href = "home.html";
    return false;
  }
  return true;
}

function obtenerMiNegocio() {
  const respuesta = peticionSincronaConToken("GET", "/negocio/mi-negocio");
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body) return { ok: false, error: "Respuesta inesperada del servidor." };
  if (!respuesta.body.success) return { ok: false, error: respuesta.body.message, status: respuesta.status };
  return { ok: true, data: respuesta.body.data };
}

function actualizarMiNegocio(cambios) {
  const respuesta = peticionSincronaConToken("PUT", "/negocio/mi-negocio", cambios);
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo guardar el cambio." };
  }
  console.log("Respuesta de actualizarMiNegocio:", respuesta.body); // Depuración
  return { ok: true };
}

function agregarFotoNegocio(url) {
  const respuesta = peticionSincronaConToken("POST", "/negocio/mi-negocio/fotos", { url: url });
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo agregar la foto." };
  }
  return { ok: true, data: respuesta.body.data };
}

function eliminarFotoNegocio(fotoId) {
  const respuesta = peticionSincronaConToken("DELETE", "/negocio/mi-negocio/fotos/" + fotoId);
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo eliminar la foto." };
  }
  return { ok: true };
}

function crearItemNegocio(item) {
  const respuesta = peticionSincronaConToken("POST", "/negocio/mi-negocio/items", item);
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo agregar el ítem." };
  }
  return { ok: true, data: respuesta.body.data };
}

function actualizarItemNegocio(itemId, item) {
  const respuesta = peticionSincronaConToken("PUT", "/negocio/mi-negocio/items/" + itemId, item);
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo actualizar el ítem." };
  }
  return { ok: true };
}

function eliminarItemNegocio(itemId) {
  const respuesta = peticionSincronaConToken("DELETE", "/negocio/mi-negocio/items/" + itemId);
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo eliminar el ítem." };
  }
  return { ok: true };
}


// ── Negocios públicos: para destino.html y negocio-detalle.html ─────────────
// No necesitan token: cualquier viajero (con sesión o sin ella) puede ver
// los negocios aliados de un pueblo y el detalle de cada uno.

function obtenerNegociosPorPueblo(puebloId) {
  const respuesta = peticionSincrona("GET", "/negocio/pueblo/" + puebloId);
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body) return { ok: false, error: "Respuesta inesperada del servidor." };
  if (!respuesta.body.success) return { ok: false, error: respuesta.body.message, status: respuesta.status };
  return { ok: true, data: respuesta.body.data };
}

function obtenerNegocioPublico(negocioId) {
  const respuesta = peticionSincrona("GET", "/negocio/publico/" + negocioId);
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body) return { ok: false, error: "Respuesta inesperada del servidor." };
  if (!respuesta.body.success) return { ok: false, error: respuesta.body.message, status: respuesta.status };
  return { ok: true, data: respuesta.body.data };
}


// ── Panel de Admin: solicitudes de convenio ──────────────────────────────────
// Igual que protegerPaginaSocio: valida sesión Y rol en el cliente para la
// experiencia de usuario (ocultar el panel, redirigir), pero la seguridad
// real la impone el backend con requiere_rol("admin") en cada endpoint de
// /convenio/ — si alguien fuerza la entrada sin token de admin, la API
// igual le responde 401/403.

function protegerPaginaAdmin() {
  const usuario = usuarioActual();
  if (!usuario) {
    window.location.href = "login.html?redirect=" + encodeURIComponent("panel-admin.html");
    return false;
  }
  if (usuario.rol !== "admin") {
    window.location.href = "home.html";
    return false;
  }
  return true;
}

function obtenerSolicitudesConvenio() {
  const respuesta = peticionSincronaConToken("GET", "/convenio/");
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body) return { ok: false, error: "Respuesta inesperada del servidor." };
  if (!respuesta.body.success) return { ok: false, error: respuesta.body.message, status: respuesta.status };
  return { ok: true, data: respuesta.body.data };
}

function aprobarSolicitudConvenio(solicitudId, puebloId, categoria) {
  const respuesta = peticionSincronaConToken("POST", "/convenio/" + solicitudId + "/aprobar", {
    pueblo_id: puebloId,
    categoria: categoria
  });
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo aprobar la solicitud." };
  }
  return { ok: true, data: respuesta.body.data };
}

function rechazarSolicitudConvenio(solicitudId) {
  const respuesta = peticionSincronaConToken("POST", "/convenio/" + solicitudId + "/rechazar");
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body || !respuesta.body.success) {
    return { ok: false, error: (respuesta.body && respuesta.body.message) || "No se pudo rechazar la solicitud." };
  }
  return { ok: true };
}


// ── Recuperación de contraseña ("¿Olvidaste tu contraseña?") ────────────────
// El backend siempre responde con el mismo mensaje exista o no el correo
// (para no revelar qué correos están registrados), así que aquí no hay
// distinción de casos: se muestra el mismo mensaje que llegue del servidor.

function solicitarRecuperacionContrasena(correo) {
  const respuesta = peticionSincrona("POST", "/auth/forgot-password", { correo: correo });
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body) return { ok: false, error: "Respuesta inesperada del servidor." };
  return { ok: !!respuesta.body.success, mensaje: respuesta.body.message };
}

function restablecerContrasena(token, nuevaContrasena) {
  const respuesta = peticionSincrona("POST", "/auth/reset-password", {
    token: token,
    nueva_contrasena: nuevaContrasena
  });
  if (respuesta.error) return { ok: false, error: respuesta.error };
  if (!respuesta.body) return { ok: false, error: "Respuesta inesperada del servidor." };
  if (!respuesta.body.success) return { ok: false, error: respuesta.body.message };
  return { ok: true, mensaje: respuesta.body.message };
}
