// nav.js — solo interfaz: menú hamburguesa para móvil.
// No toca autenticación, datos ni lógica de negocio.
(function () {
  const barra = document.querySelector(".navbar .contenedor");
  const enlaces = document.querySelector(".nav-enlaces");
  if (!barra || !enlaces || barra.querySelector(".nav-toggle")) return;

  const btn = document.createElement("button");
  btn.className = "nav-toggle";
  btn.type = "button";
  btn.setAttribute("aria-label", "Abrir menú");
  btn.setAttribute("aria-expanded", "false");
  btn.innerHTML = "<span></span><span></span><span></span>";
  barra.appendChild(btn);

  function cerrar() {
    enlaces.classList.remove("abierto");
    btn.classList.remove("abierto");
    btn.setAttribute("aria-expanded", "false");
  }

  btn.addEventListener("click", function () {
    const abierto = enlaces.classList.toggle("abierto");
    btn.classList.toggle("abierto", abierto);
    btn.setAttribute("aria-expanded", String(abierto));
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") cerrar(); });
  window.addEventListener("resize", function () { if (window.innerWidth > 760) cerrar(); });
})();

// ── Flecha "volver atrás" en todas las páginas (excepto el inicio) ──────────
// Lleva su propio historial de páginas visitadas (sessionStorage), así funciona
// aunque la página anterior haya sido un login/redirección o se haya abierto
// con otra pestaña, y nunca devuelve a login/registro estando ya dentro.
(function () {
  const archivo = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  const actual = (location.pathname.split("/").pop() || "index.html") + location.search;
  const CLAVE = "rc_historial";
  const PAGINAS_AUTH = ["login.html", "registro.html", "olvide-contrasena.html", "restablecer-contrasena.html", "login-convenio.html"];

  let pila = [];
  try { pila = JSON.parse(sessionStorage.getItem(CLAVE) || "[]"); } catch (e) { pila = []; }
  if (!Array.isArray(pila)) pila = [];

  // Registrar esta página en la pila
  const ultimo = pila[pila.length - 1];
  if (ultimo !== actual) {
    if (pila.length >= 2 && pila[pila.length - 2] === actual) {
      pila.pop(); // el usuario volvió con el botón del navegador
    } else {
      pila.push(actual);
    }
  }
  if (pila.length > 40) pila = pila.slice(-40);
  try { sessionStorage.setItem(CLAVE, JSON.stringify(pila)); } catch (e) {}

  if (archivo === "index.html" || archivo === "home.html" || archivo === "") return;
  if (document.querySelector(".boton-volver-atras")) return;

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "boton-volver-atras";
  btn.setAttribute("aria-label", "Volver atrás");
  btn.title = "Volver atrás";
  btn.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg><span>Volver</span>';

  btn.addEventListener("click", function () {
    const estaEnAuth = PAGINAS_AUTH.indexOf(archivo) !== -1;
    let p = [];
    try { p = JSON.parse(sessionStorage.getItem(CLAVE) || "[]"); } catch (e) { p = []; }

    // Buscar hacia atrás la última página distinta a la actual (y que no sea login si ya estamos dentro)
    let destino = null;
    for (let i = p.length - 2; i >= 0; i--) {
      const nombre = (p[i].split("?")[0] || "").toLowerCase();
      if (p[i] === actual) continue;
      if (!estaEnAuth && PAGINAS_AUTH.indexOf(nombre) !== -1) continue;
      destino = p[i];
      p = p.slice(0, i + 1);
      break;
    }
    try { sessionStorage.setItem(CLAVE, JSON.stringify(p)); } catch (e) {}

    document.body.classList.remove("fx-listo");
    document.body.classList.add("fx-saliendo");
    setTimeout(function () { window.location.href = destino || "home.html"; }, 300);
  });

  document.body.appendChild(btn);
})();
