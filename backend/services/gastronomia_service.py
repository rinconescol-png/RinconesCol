from fastapi.responses import JSONResponse
import psycopg2.extras
from db.conexion import get_db_connection
from models.gastronomia_model import Gastronomia


class GastronomiaService:
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

    @staticmethod
    def _con_alias_imagen(item: dict) -> dict:
        # El frontend (gastronomia.html / home.html) espera el campo "imagen".
        item["imagen"] = item.get("foto")
        return item

    # ── GET ALL ──────────────────────────────────────────────
    async def get_gastronomias(self):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT g.id, g.nombre, g.descripcion, g.foto, g.region,
                                p.nombre AS pueblo
                         FROM gastronomia g
                         LEFT JOIN pueblos p ON p.id = g.pueblo_id
                         ORDER BY g.id"""
                cursor.execute(sql)
                items = [self._con_alias_imagen(dict(r)) for r in cursor.fetchall()]
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Gastronomía listada correctamente",
                    "data": items
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar gastronomía: {str(e)}",
                "data": None
            })

    # ── GET BY ID ────────────────────────────────────────────
    async def get_gastronomia_by_id(self, item_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT g.id, g.nombre, g.descripcion, g.foto, g.region,
                                p.nombre AS pueblo
                         FROM gastronomia g
                         LEFT JOIN pueblos p ON p.id = g.pueblo_id
                         WHERE g.id = %s"""
                cursor.execute(sql, (item_id,))
                item = cursor.fetchone()
                if item:
                    return JSONResponse(status_code=200, content={
                        "success": True, "message": "Item encontrado",
                        "data": self._con_alias_imagen(dict(item))
                    })
                return JSONResponse(status_code=404, content={
                    "success": False, "message": "Item no encontrado", "data": None
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar gastronomía: {str(e)}",
                "data": None
            })

    # ── CREATE ───────────────────────────────────────────────
    async def create_gastronomia(self, data: Gastronomia):
        try:
            with self.con.cursor() as cursor:
                sql = """INSERT INTO gastronomia (nombre, descripcion, foto, pueblo_id, region)
                         VALUES (%s, %s, %s, %s, %s)
                         RETURNING id"""
                cursor.execute(sql, (data.nombre, data.descripcion, data.foto, data.pueblo_id, data.region))
                new_id = cursor.fetchone()[0]
                self.con.commit()
                return JSONResponse(status_code=201, content={
                    "success": True,
                    "message": "Gastronomía creada exitosamente",
                    "data": {"gastronomia_id": new_id}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al crear gastronomía: {str(e)}",
                "data": None
            })

    # ── UPDATE ───────────────────────────────────────────────
    async def update_gastronomia(self, item_id: int, data: Gastronomia):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM gastronomia WHERE id = %s", (item_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Item no encontrado", "data": None
                    })
                sql = """UPDATE gastronomia
                         SET nombre=%s, descripcion=%s, foto=%s, pueblo_id=%s, region=%s
                         WHERE id=%s"""
                cursor.execute(sql, (data.nombre, data.descripcion, data.foto, data.pueblo_id, data.region, item_id))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Gastronomía actualizada correctamente",
                    "data": {"filas_afectadas": cursor.rowcount}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al actualizar gastronomía: {str(e)}",
                "data": None
            })

    # ── DELETE ───────────────────────────────────────────────
    async def delete_gastronomia(self, item_id: int):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM gastronomia WHERE id = %s", (item_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Item no encontrado", "data": None
                    })
                cursor.execute("DELETE FROM gastronomia WHERE id = %s", (item_id,))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Gastronomía eliminada correctamente", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al eliminar gastronomía: {str(e)}",
                "data": None
            })
