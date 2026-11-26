from fastapi.responses import JSONResponse
import psycopg2.extras
from db.conexion import get_db_connection
from models.tradicion_model import Tradicion


class TradicionService:
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

    # ── GET ALL ──────────────────────────────────────────────
    async def get_tradiciones(self):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT t.id, t.nombre, t.descripcion, t.epoca, t.foto,
                                p.nombre AS pueblo
                         FROM tradiciones t
                         LEFT JOIN pueblos p ON p.id = t.pueblo_id"""
                cursor.execute(sql)
                tradiciones = [dict(r) for r in cursor.fetchall()]
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Tradiciones listadas correctamente",
                    "data": tradiciones
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar tradiciones: {str(e)}",
                "data": None
            })

    # ── GET BY ID ────────────────────────────────────────────
    async def get_tradicion_by_id(self, tradicion_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT t.id, t.nombre, t.descripcion, t.epoca, t.foto,
                                p.nombre AS pueblo
                         FROM tradiciones t
                         LEFT JOIN pueblos p ON p.id = t.pueblo_id
                         WHERE t.id = %s"""
                cursor.execute(sql, (tradicion_id,))
                tradicion = cursor.fetchone()
                if tradicion:
                    return JSONResponse(status_code=200, content={
                        "success": True, "message": "Tradición encontrada", "data": dict(tradicion)
                    })
                return JSONResponse(status_code=404, content={
                    "success": False, "message": "Tradición no encontrada", "data": None
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar tradición: {str(e)}",
                "data": None
            })

    # ── CREATE ───────────────────────────────────────────────
    async def create_tradicion(self, data: Tradicion):
        try:
            with self.con.cursor() as cursor:
                sql = """INSERT INTO tradiciones (nombre, descripcion, epoca, foto, pueblo_id)
                         VALUES (%s, %s, %s, %s, %s)
                         RETURNING id"""
                cursor.execute(sql, (data.nombre, data.descripcion, data.epoca, data.foto, data.pueblo_id))
                new_id = cursor.fetchone()[0]
                self.con.commit()
                return JSONResponse(status_code=201, content={
                    "success": True,
                    "message": "Tradición creada exitosamente",
                    "data": {"tradicion_id": new_id}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al crear tradición: {str(e)}",
                "data": None
            })

    # ── UPDATE ───────────────────────────────────────────────
    async def update_tradicion(self, tradicion_id: int, data: Tradicion):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM tradiciones WHERE id = %s", (tradicion_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Tradición no encontrada", "data": None
                    })
                sql = """UPDATE tradiciones
                         SET nombre=%s, descripcion=%s, epoca=%s, foto=%s, pueblo_id=%s
                         WHERE id=%s"""
                cursor.execute(sql, (data.nombre, data.descripcion, data.epoca, data.foto, data.pueblo_id, tradicion_id))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Tradición actualizada correctamente",
                    "data": {"filas_afectadas": cursor.rowcount}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al actualizar tradición: {str(e)}",
                "data": None
            })

    # ── DELETE ───────────────────────────────────────────────
    async def delete_tradicion(self, tradicion_id: int):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM tradiciones WHERE id = %s", (tradicion_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Tradición no encontrada", "data": None
                    })
                cursor.execute("DELETE FROM tradiciones WHERE id = %s", (tradicion_id,))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Tradición eliminada correctamente", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al eliminar tradición: {str(e)}",
                "data": None
            })
