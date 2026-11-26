// fx.js — solo interfaz: animaciones (parallax, reveal, tilt, cursor, transiciones).
// No toca autenticación, datos ni lógica de negocio.
(function () {
  const reducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const $ = (s, r) => Array.from((r || document).querySelectorAll(s));

  // ── Telón de entrada/salida de página ─────────────────────────────
  const telon = document.createElement("div");
  telon.className = "fx-telon";
  document.body.appendChild(telon);
  requestAnimationFrame(() => requestAnimationFrame(() => document.body.classList.add("fx-listo")));
  window.addEventListener("pageshow", e => {
    // Al volver atrás, el navegador puede restaurar la página tal como quedó
    // (con el telón de salida puesto). Se restablece para que no quede en negro.
    if (e.persisted || document.body.classList.contains("fx-saliendo")) {
      document.body.classList.remove("fx-saliendo");
      document.body.classList.add("fx-listo");
    }
  });

  if (!reducido) {
    document.addEventListener("click", function (e) {
      const a = e.target.closest("a[href]");
      if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
      const href = a.getAttribute("href");
      if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:") || a.target === "_blank") return;
      const url = new URL(a.href, location.href);
      if (url.origin !== location.origin || (url.pathname === location.pathname && url.hash)) return;
      e.preventDefault();
      document.body.classList.remove("fx-listo");
      document.body.classList.add("fx-saliendo");
      setTimeout(() => { location.href = a.href; }, 480);
    });
  }

  // ── Barra de progreso + navbar ────────────────────────────────────
  const barra = document.createElement("div");
  barra.className = "fx-progreso";
  document.body.appendChild(barra);
  const nav = document.querySelector(".navbar");
  let ultimoY = 0;

  // ── Parallax ──────────────────────────────────────────────────────
  const paralajes = $("[data-parallax]");
  let ticking = false;
  function alScroll() {
    const y = window.scrollY, h = document.documentElement.scrollHeight - window.innerHeight;
    barra.style.transform = "scaleX(" + (h > 0 ? y / h : 0) + ")";
    if (nav) {
      nav.classList.toggle("nav-scrolled", y > 30);
      nav.classList.toggle("nav-oculta", y > ultimoY && y > 400 && !nav.querySelector(".nav-enlaces.abierto"));
    }
    ultimoY = y;
    if (!reducido) paralajes.forEach(el => {
      const v = parseFloat(el.dataset.parallax) || 0.2;
      el.style.setProperty("--py", (y * v).toFixed(1) + "px");
      el.style.translate = "0 " + (y * v).toFixed(1) + "px";
    });
    ticking = false;
  }
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(alScroll); } }, { passive: true });
  alScroll();

  // Parallax automático en imágenes de tarjetas y hero de detalle
  function parallaxFondo() {
    if (reducido) return;
    $(".detalle-hero, .negocio-hero, .hero-interno").forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.bottom < 0 || r.top > innerHeight) return;
      el.style.backgroundPositionY = "calc(50% + " + (-r.top * 0.25).toFixed(1) + "px)";
    });
  }
  window.addEventListener("scroll", parallaxFondo, { passive: true });
  parallaxFondo();

  // ── Titulares palabra por palabra ────────────────────────────────
  function partir(h) {
    if (h.dataset.fxHecho) return;
    h.dataset.fxHecho = "1";
    let i = 0;
    (function rec(nodo) {
      Array.from(nodo.childNodes).forEach(n => {
        if (n.nodeType === 3) {
          const frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(t => {
            if (!t) return;
            if (/^\s+$/.test(t)) { frag.appendChild(document.createTextNode(" ")); return; }
            const w = document.createElement("span"); w.className = "fx-palabra";
            const s = document.createElement("span"); s.textContent = t; s.style.setProperty("--i", i++);
            w.appendChild(s); frag.appendChild(w);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1) rec(n);
      });
    })(h);
  }
  if (!reducido) $("[data-split], .hero-interno h1, .detalle-hero-texto h1, .negocio-hero-texto h1").forEach(partir);

  // ── Reveal al hacer scroll (también para tarjetas creadas por JS) ─
  const io = "IntersectionObserver" in window ? new IntersectionObserver(entradas => {
    entradas.forEach(en => { if (en.isIntersecting) { en.target.classList.add("fx-visto"); io.unobserve(en.target); } });
  }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }) : null;

  const SEL = ".tarjeta, .tarjeta-feature, .galeria-explora-col, .seccion-titulo, .seccion-cabecera, .nosotros-texto, .negocio-caja, " +
    ".detalle-lateral, .tarjeta-restaurante, .tarjeta-resena, .formulario-resena, .caja-atencion, .valor, .paso, .negocio-cta-caja, " +
    ".galeria-comparte > div, .nosotros-imagen, .detalle-info > *, .login-caja, .fila-aprobar";
  function preparar(raiz) {
    if (reducido || !io) return;
    $(SEL, raiz).forEach(el => {
      if (el.dataset.fxOk) return;
      el.dataset.fxOk = "1";
      const hermanos = el.parentElement ? Array.from(el.parentElement.children).filter(c => c.dataset && c.dataset.fxOk) : [];
      el.style.setProperty("--fx-delay", (Math.min(hermanos.indexOf(el), 6) * 0.09).toFixed(2) + "s");
      el.classList.add(el.matches(".nosotros-texto") ? "fx-reveal-der" : el.matches(".nosotros-imagen") ? "fx-reveal-izq" : "fx-reveal");
      el.classList.add("fx-reveal");
      io.observe(el);
      if (el.matches(".tarjeta")) tilt(el);
    });
  }
  preparar(document);
  new MutationObserver(m => m.forEach(x => x.addedNodes.forEach(n => { if (n.nodeType === 1) { if (n.matches && n.matches(SEL)) preparar(n.parentElement); else preparar(n); } })))
    .observe(document.body, { childList: true, subtree: true });

  // ── Tilt 3D + brillo que sigue al mouse ──────────────────────────
  function tilt(el) {
    if (!finePointer || reducido || el.dataset.fxTilt) return;
    el.dataset.fxTilt = "1";
    el.classList.add("fx-tilt");
    const b = document.createElement("span"); b.className = "fx-brillo"; el.appendChild(b);
    el.addEventListener("mousemove", e => {
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      el.classList.add("fx-tilt-activo");
      el.style.transform = "perspective(900px) rotateX(" + ((0.5 - y) * 7).toFixed(2) + "deg) rotateY(" + ((x - 0.5) * 9).toFixed(2) + "deg) translateY(-6px)";
      el.style.setProperty("--mx", (x * 100) + "%"); el.style.setProperty("--my", (y * 100) + "%");
    });
    el.addEventListener("mouseleave", () => { el.classList.remove("fx-tilt-activo"); el.style.transform = ""; });
  }

  // ── Botones magnéticos ───────────────────────────────────────────
  if (finePointer && !reducido) {
    document.addEventListener("mousemove", e => {
      const b = e.target.closest && e.target.closest(".boton-primario, .boton-claro, .boton-secundario");
      $(".boton[data-mag]").forEach(x => { if (x !== b) { x.style.translate = ""; x.removeAttribute("data-mag"); } });
      if (!b || b.closest(".tarjeta")) return;
      const r = b.getBoundingClientRect();
      b.setAttribute("data-mag", "1");
      b.style.translate = ((e.clientX - (r.left + r.width / 2)) * 0.22).toFixed(1) + "px " + ((e.clientY - (r.top + r.height / 2)) * 0.3).toFixed(1) + "px";
    });
  }

  // ── Cursor con halo ──────────────────────────────────────────────
  if (finePointer && !reducido) {
    const c = document.createElement("div"); c.className = "fx-cursor"; document.body.appendChild(c);
    let x = 0, y = 0, cx = 0, cy = 0;
    document.addEventListener("mousemove", e => { x = e.clientX; y = e.clientY; c.classList.add("fx-cursor-on");
      c.classList.toggle("fx-cursor-grande", !!e.target.closest("a, button, .tarjeta, .galeria-explora-media, input, select, textarea")); });
    document.addEventListener("mouseleave", () => c.classList.remove("fx-cursor-on"));
    (function loop() { cx += (x - cx) * 0.18; cy += (y - cy) * 0.18; c.style.transform = "translate(" + cx.toFixed(1) + "px," + cy.toFixed(1) + "px)"; requestAnimationFrame(loop); })();
  }
})();
