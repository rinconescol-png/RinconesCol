"""
Descarga fotos reales desde Wikimedia Commons y las guarda en frontend/img/.

Descarga:
  - La foto que falta de Villa de Leyva (img/villadeleyva.jpg)
  - Una foto para cada plato de gastronomía (img/gastronomia/...)

Uso (desde la carpeta backend, donde está main.py):
    python scripts/descargar_imagenes.py

Si un archivo ya existe NO lo sobrescribe, así puedes cambiar a mano
cualquier foto que no te guste y volver a correr el script sin perderla.
Al final crea frontend/img/CREDITOS_IMAGENES.txt con autor y licencia.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia exige un User-Agent; sin esto responde 403
HEADERS = {"User-Agent": "RinconesCol-ProyectoAcademico/1.0 (proyecto SENA)"}

CARPETA_IMG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend", "img"
)

# (archivo dentro de frontend/img, texto para buscar en Commons)
IMAGENES = [
    ("villadeleyva.jpg", "Plaza Central Plaza Principal Villa de Leyva Boyacá Colombia"),
    ("gastronomia/trucha-guavio.jpg", "trucha frita con patacón"),
    ("gastronomia/ajiaco.jpg", "ajiaco santafereño"),
    ("gastronomia/arepa-choclo.jpg", "arepa de choclo"),
    ("gastronomia/sancocho.jpg", "sancocho de gallina"),
    ("gastronomia/mote-queso.jpg", "mote de queso"),
    ("gastronomia/bunuelos-natilla.jpg", "buñuelos natilla"),
]


def pedir(url):
    peticion = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(peticion, timeout=30) as respuesta:
        return respuesta.read()


def buscar_imagen(texto):
    """Busca en Commons y devuelve la primera foto JPG grande, o None."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": texto,
        "gsrnamespace": 6,  # 6 = archivos
        "gsrlimit": 10,
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": 1000,  # pide una versión de 1000 px, más liviana
    }
    datos = json.loads(pedir(API + "?" + urllib.parse.urlencode(params)))
    paginas = datos.get("query", {}).get("pages", {})

    # "index" es el orden de relevancia que da Commons
    for pagina in sorted(paginas.values(), key=lambda p: p["index"]):
        if "imageinfo" not in pagina:
            continue
        info = pagina["imageinfo"][0]
        if info["mime"] == "image/jpeg" and info["width"] >= 600:
            return pagina["title"], info
    return None


def limpiar_html(texto):
    return re.sub(r"<[^>]+>", "", texto or "").strip()


def main():
    creditos = []

    for archivo, busqueda in IMAGENES:
        destino = os.path.join(CARPETA_IMG, archivo)

        if os.path.exists(destino):
            print("Ya existe, se omite: " + archivo)
            continue

        print("Buscando: " + busqueda)
        resultado = buscar_imagen(busqueda)
        if resultado is None:
            print("  ✗ No encontré foto para " + archivo + ". Pon una a mano.")
            continue

        titulo, info = resultado
        url_foto = info.get("thumburl") or info["url"]

        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as f:
            f.write(pedir(url_foto))
        print("  ✓ " + archivo + "  ←  " + titulo)

        meta = info.get("extmetadata", {})
        autor = limpiar_html(meta.get("Artist", {}).get("value"))
        licencia = limpiar_html(meta.get("LicenseShortName", {}).get("value"))
        creditos.append(
            archivo + " | " + titulo + " | " + autor + " | " + licencia
            + " | " + info["descriptionurl"]
        )
        time.sleep(1)  # pausa corta para no saturar a Commons

    if creditos:
        ruta = os.path.join(CARPETA_IMG, "CREDITOS_IMAGENES.txt")
        with open(ruta, "a", encoding="utf-8") as f:
            f.write("\n".join(creditos) + "\n")
        print("\nCréditos guardados en frontend/img/CREDITOS_IMAGENES.txt")
        print("Revisa las fotos: si alguna no se parece al plato, reemplázala a mano.")


if __name__ == "__main__":
    main()
