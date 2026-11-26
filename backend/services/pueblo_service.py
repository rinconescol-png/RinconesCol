from fastapi.responses import JSONResponse
import psycopg2.extras
from db.conexion import get_db_connection
from models.pueblo_model import Pueblo


class PuebloService:
    def __init__(self):
        # Verificación temprana: falla rápido en el arranque si no hay BD.
        if get_db_connection() is None:
            print("No se pudo establecer conexión a la BD")

    @property
    def con(self):
        # Pide la conexión viva en cada acceso (en vez de guardarla una
        # sola vez al arrancar). get_db_connection() ya sabe reconectar
        # si la conexión se cerró (PC en reposo, Postgres reiniciado,
        # inactividad prolongada, etc.), así el servicio nunca se queda
        # pegado a una conexión muerta hasta reiniciar el backend.
        return get_db_connection()

    # ── Helpers internos para armar el objeto que espera el frontend ───────
    def _adjuntar_listas_hijas(self, cursor, pueblo: dict):
        pueblo_id = pueblo["id"]

        cursor.execute(
            "SELECT actividad FROM pueblo_actividades WHERE pueblo_id = %s ORDER BY orden, id",
            (pueblo_id,),
        )
        pueblo["actividades"] = [r["actividad"] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT plato FROM pueblo_platos_tipicos WHERE pueblo_id = %s ORDER BY orden, id",
            (pueblo_id,),
        )
        pueblo["platosTipicos"] = [r["plato"] for r in cursor.fetchall()]

        cursor.execute(
            """SELECT nombre, tipo, descripcion FROM pueblo_restaurantes
               WHERE pueblo_id = %s ORDER BY orden, id""",
            (pueblo_id,),
        )
        pueblo["dondeComer"] = [dict(r) for r in cursor.fetchall()]

        # Alias en formato "camelCase"/nombres exactos que usa destino.html,
        # además de conservar los nombres originales de columna.
        # "pueblo_id" guarda SIEMPRE el id numérico real (clave foránea en la
        # BD, la que necesitan /resenas/ y el enlace de WhatsApp) antes de
        # que "id" se reemplace por el slug para que destino.html?id=slug
        # siga funcionando igual que antes.
        pueblo["pueblo_id"] = pueblo["id"]
        pueblo["id"] = pueblo.get("slug") or pueblo["id"]
        return pueblo

    def _reemplazar_listas_hijas(self, cursor, pueblo_id: int, data: Pueblo):
        if data.actividades is not None:
            cursor.execute("DELETE FROM pueblo_actividades WHERE pueblo_id = %s", (pueblo_id,))
            for i, actividad in enumerate(data.actividades):
                cursor.execute(
                    "INSERT INTO pueblo_actividades (pueblo_id, actividad, orden) VALUES (%s, %s, %s)",
                    (pueblo_id, actividad, i),
                )

        if data.platos_tipicos is not None:
            cursor.execute("DELETE FROM pueblo_platos_tipicos WHERE pueblo_id = %s", (pueblo_id,))
            for i, plato in enumerate(data.platos_tipicos):
                cursor.execute(
                    "INSERT INTO pueblo_platos_tipicos (pueblo_id, plato, orden) VALUES (%s, %s, %s)",
                    (pueblo_id, plato, i),
                )

        if data.donde_comer is not None:
            cursor.execute("DELETE FROM pueblo_restaurantes WHERE pueblo_id = %s", (pueblo_id,))
            for i, r in enumerate(data.donde_comer):
                cursor.execute(
                    """INSERT INTO pueblo_restaurantes (pueblo_id, nombre, tipo, descripcion, orden)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (pueblo_id, r.nombre, r.tipo, r.descripcion, i),
                )

    # ── GET ALL ──────────────────────────────────────────────
    async def get_pueblos(self):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM pueblos ORDER BY id")
                pueblos = [dict(r) for r in cursor.fetchall()]
                for p in pueblos:
                    self._adjuntar_listas_hijas(cursor, p)
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Pueblos listados correctamente",
                    "data": pueblos
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar pueblos: {str(e)}",
                "data": None
            })

    # ── GET BY ID ────────────────────────────────────────────
    async def get_pueblo_by_id(self, pueblo_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM pueblos WHERE id = %s", (pueblo_id,))
                pueblo = cursor.fetchone()
                if pueblo:
                    pueblo = self._adjuntar_listas_hijas(cursor, dict(pueblo))
                    return JSONResponse(status_code=200, content={
                        "success": True,
                        "message": "Pueblo encontrado",
                        "data": pueblo
                    })
                return JSONResponse(status_code=404, content={
                    "success": False,
                    "message": "Pueblo no encontrado",
                    "data": None
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar pueblo: {str(e)}",
                "data": None
            })

    # ── CREATE ───────────────────────────────────────────────
    async def create_pueblo(self, data: Pueblo):
        try:
            with self.con.cursor() as cursor:
                sql = """INSERT INTO pueblos
                         (nombre, departamento, municipio, descripcion, historia, imagen, latitud, longitud,
                          slug, region, sello, resumen, clima, ubicacion, alcalde)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                         RETURNING id"""
                cursor.execute(sql, (
                    data.nombre, data.departamento, data.municipio,
                    data.descripcion, data.historia, data.imagen,
                    data.latitud, data.longitud,
                    data.slug, data.region, data.sello, data.resumen,
                    data.clima, data.ubicacion, data.alcalde,
                ))
                new_id = cursor.fetchone()[0]
                self._reemplazar_listas_hijas(cursor, new_id, data)
                self.con.commit()
                return JSONResponse(status_code=201, content={
                    "success": True,
                    "message": "Pueblo creado exitosamente",
                    "data": {"pueblo_id": new_id}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al crear pueblo: {str(e)}",
                "data": None
            })

    # ── UPDATE ───────────────────────────────────────────────
    async def update_pueblo(self, pueblo_id: int, data: Pueblo):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM pueblos WHERE id = %s", (pueblo_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Pueblo no encontrado", "data": None
                    })
                sql = """UPDATE pueblos
                         SET nombre=%s, departamento=%s, municipio=%s, descripcion=%s,
                             historia=%s, imagen=%s, latitud=%s, longitud=%s,
                             slug=%s, region=%s, sello=%s, resumen=%s, clima=%s,
                             ubicacion=%s, alcalde=%s
                         WHERE id=%s"""
                cursor.execute(sql, (
                    data.nombre, data.departamento, data.municipio,
                    data.descripcion, data.historia, data.imagen,
                    data.latitud, data.longitud,
                    data.slug, data.region, data.sello, data.resumen,
                    data.clima, data.ubicacion, data.alcalde,
                    pueblo_id,
                ))
                self._reemplazar_listas_hijas(cursor, pueblo_id, data)
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Pueblo actualizado correctamente",
                    "data": {"filas_afectadas": cursor.rowcount}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al actualizar pueblo: {str(e)}",
                "data": None
            })

    # ── DELETE ───────────────────────────────────────────────
    async def delete_pueblo(self, pueblo_id: int):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM pueblos WHERE id = %s", (pueblo_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Pueblo no encontrado", "data": None
                    })
                cursor.execute("DELETE FROM pueblos WHERE id = %s", (pueblo_id,))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Pueblo eliminado correctamente",
                    "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al eliminar pueblo: {str(e)}",
                "data": None
            })
