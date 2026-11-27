"""
Ejecuta archivos .sql contra la base de datos de Render usando psycopg2.

Se usa porque el psql 12 portable es muy viejo y Render lo rechaza
("No SNI information found"). psycopg2 trae una librería más nueva.

Uso (desde la carpeta backend):
    $env:RENDER_URL = "la External Database URL"
    python scripts/ejecutar_sql_render.py archivo1.sql archivo2.sql

Todo se ejecuta en una sola transacción: si algo falla, no se guarda nada.
"""
import os
import sys

import psycopg2

url = os.environ.get("RENDER_URL")
if not url:
    sys.exit("Falta la variable RENDER_URL (la External Database URL de Render).")

if len(sys.argv) < 2:
    sys.exit("Indica al menos un archivo .sql")

conexion = psycopg2.connect(url)
try:
    cursor = conexion.cursor()
    for archivo in sys.argv[1:]:
        print("Ejecutando " + archivo + " ...")
        with open(archivo, encoding="utf-8-sig") as f:
            lineas = f.read().splitlines()

        # Render no deja cambiar el comentario de la extensión plpgsql
        # (el respaldo lo trae) y daría error, así que se quita esa línea.
        lineas = [l for l in lineas if not l.startswith("COMMENT ON EXTENSION")]

        cursor.execute("\n".join(lineas))

        # El respaldo deja vacío el search_path de la sesión; se restablece
        # para que los archivos siguientes encuentren las tablas (pueblos, etc.)
        cursor.execute("SET search_path TO public")

    conexion.commit()
    print("Listo: todo se ejecutó bien.")
except Exception as e:
    conexion.rollback()
    print("ERROR, no se guardó nada:")
    print(e)
finally:
    conexion.close()