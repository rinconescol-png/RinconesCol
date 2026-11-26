from fastapi.responses import JSONResponse
import psycopg2.extras
from db.conexion import get_db_connection
from models.itinerario_model import ItinerarioItem


class ItinerarioService:
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
    async def get_itinerario(self):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT i.id, i.pueblo_id, i.franja, i.orden, i.hora_sugerida,
                                i.actividad, i.descripcion, i.atraccion_id,
                                p.nombre AS pueblo
                         FROM pueblo_itinerario i
                         LEFT JOIN pueblos p ON p.id = i.pueblo_id
                         ORDER BY i.pueblo_id,
                                  CASE i.franja WHEN 'manana' THEN 1 WHEN 'tarde' THEN 2 ELSE 3 END,
                                  i.orden, i.id"""
                cursor.execute(sql)
                items = [dict(r) for r in cursor.fetchall()]
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Itinerario listado correctamente",
                    "data": items
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar itinerario: {str(e)}",
                "data": None
            })

    # ── GET BY ID ────────────────────────────────────────────
    async def get_itinerario_by_id(self, item_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """SELECT id, pueblo_id, franja, orden, hora_sugerida, actividad, descripcion, atraccion_id
                       FROM pueblo_itinerario WHERE id = %s""",
                    (item_id,),
                )
                item = cursor.fetchone()
                if item:
                    return JSONResponse(status_code=200, content={
                        "success": True, "message": "Item de itinerario encontrado", "data": dict(item)
                    })
                return JSONResponse(status_code=404, content={
                    "success": False, "message": "Item de itinerario no encontrado", "data": None
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar item de itinerario: {str(e)}",
                "data": None
            })

    # ── GET POR PUEBLO (agrupado por franja) ────────────────
    # Usada por atracciones.html: arma directamente el objeto
    # { manana: [...], tarde: [...], noche: [...] } para ese pueblo.
    async def get_itinerario_por_pueblo(self, pueblo_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT i.id, i.franja, i.orden, i.hora_sugerida, i.actividad,
                                i.descripcion, i.atraccion_id, a.nombre AS atraccion_nombre
                         FROM pueblo_itinerario i
                         LEFT JOIN atracciones a ON a.id = i.atraccion_id
                         WHERE i.pueblo_id = %s
                         ORDER BY CASE i.franja WHEN 'manana' THEN 1 WHEN 'tarde' THEN 2 ELSE 3 END,
                                  i.orden, i.id"""
                cursor.execute(sql, (pueblo_id,))
                filas = [dict(r) for r in cursor.fetchall()]

                agrupado = {"manana": [], "tarde": [], "noche": []}
                for fila in filas:
                    franja = fila.get("franja")
                    if franja in agrupado:
                        agrupado[franja].append(fila)

                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Itinerario del pueblo listado correctamente",
                    "data": agrupado
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar itinerario del pueblo: {str(e)}",
                "data": None
            })

    # ── CREATE ───────────────────────────────────────────────
    async def create_itinerario_item(self, data: ItinerarioItem):
        try:
            with self.con.cursor() as cursor:
                sql = """INSERT INTO pueblo_itinerario
                         (pueblo_id, franja, orden, hora_sugerida, actividad, descripcion, atraccion_id)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)
                         RETURNING id"""
                cursor.execute(sql, (
                    data.pueblo_id, data.franja, data.orden or 0, data.hora_sugerida,
                    data.actividad, data.descripcion, data.atraccion_id,
                ))
                new_id = cursor.fetchone()[0]
                self.con.commit()
                return JSONResponse(status_code=201, content={
                    "success": True,
                    "message": "Item de itinerario creado exitosamente",
                    "data": {"itinerario_id": new_id}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al crear item de itinerario: {str(e)}",
                "data": None
            })

    # ── UPDATE ───────────────────────────────────────────────
    async def update_itinerario_item(self, item_id: int, data: ItinerarioItem):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM pueblo_itinerario WHERE id = %s", (item_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Item de itinerario no encontrado", "data": None
                    })
                sql = """UPDATE pueblo_itinerario
                         SET pueblo_id=%s, franja=%s, orden=%s, hora_sugerida=%s,
                             actividad=%s, descripcion=%s, atraccion_id=%s
                         WHERE id=%s"""
                cursor.execute(sql, (
                    data.pueblo_id, data.franja, data.orden or 0, data.hora_sugerida,
                    data.actividad, data.descripcion, data.atraccion_id, item_id,
                ))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Item de itinerario actualizado correctamente",
                    "data": {"filas_afectadas": cursor.rowcount}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al actualizar item de itinerario: {str(e)}",
                "data": None
            })

    # ── DELETE ───────────────────────────────────────────────
    async def delete_itinerario_item(self, item_id: int):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM pueblo_itinerario WHERE id = %s", (item_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Item de itinerario no encontrado", "data": None
                    })
                cursor.execute("DELETE FROM pueblo_itinerario WHERE id = %s", (item_id,))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Item de itinerario eliminado correctamente", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al eliminar item de itinerario: {str(e)}",
                "data": None
            })
