from fastapi.responses import JSONResponse
import psycopg2.extras
from db.conexion import get_db_connection
from models.atraccion_model import Atraccion

# Etiqueta legible que se muestra como "tipo" cuando un negocio de un socio
# aparece mezclado en la lista de atracciones de su pueblo.
ETIQUETA_CATEGORIA_NEGOCIO = {
    "restaurante": "Restaurante",
    "hotel": "Hotel / Posada",
    "cafeteria": "Cafetería",
    "experiencia": "Experiencia turística",
    "artesania": "Artesanías / Emprendimiento",
}


class AtraccionService:
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

    # ── Negocios de socios aprobados, con forma de "atracción" ──────────────
    # Esto es lo que hace que un negocio (restaurante, hotel, cafetería,
    # experiencia o emprendimiento) quede visible dentro de su pueblo "como
    # una atracción/actividad más", sin tener que tocar atracciones.html ni
    # atracciones.js: se les da exactamente la misma forma (nombre, tipo,
    # descripcion, foto) que ya consume el frontend.
    def _negocios_como_atracciones(self, cursor, pueblo_id: int):
        cursor.execute(
            """SELECT id AS negocio_id, nombre, categoria, descripcion, foto
               FROM negocios
               WHERE pueblo_id = %s AND activo = TRUE
               ORDER BY id""",
            (pueblo_id,),
        )
        negocios = []
        for fila in cursor.fetchall():
            fila = dict(fila)
            negocios.append({
                "id": None,
                "negocio_id": fila["negocio_id"],
                "es_negocio": True,
                "nombre": fila["nombre"],
                "tipo": ETIQUETA_CATEGORIA_NEGOCIO.get(fila["categoria"], "Negocio aliado"),
                "descripcion": fila["descripcion"],
                "foto": fila["foto"],
                "orden": 999999,  # los negocios de socios van al final de la lista
            })
        return negocios

    # ── GET ALL ──────────────────────────────────────────────
    async def get_atracciones(self):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT a.id, a.nombre, a.tipo, a.descripcion, a.foto, a.orden,
                                p.nombre AS pueblo
                         FROM atracciones a
                         LEFT JOIN pueblos p ON p.id = a.pueblo_id
                         ORDER BY a.pueblo_id, a.orden, a.id"""
                cursor.execute(sql)
                atracciones = [dict(r) for r in cursor.fetchall()]
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Atracciones listadas correctamente",
                    "data": atracciones
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar atracciones: {str(e)}",
                "data": None
            })

    # ── GET POR PUEBLO ───────────────────────────────────────
    # Usada por la nueva página "atracciones.html": todas las atracciones
    # de un pueblo específico, en el orden definido por el campo "orden".
    async def get_atracciones_por_pueblo(self, pueblo_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT a.id, a.nombre, a.tipo, a.descripcion, a.foto, a.orden
                         FROM atracciones a
                         WHERE a.pueblo_id = %s
                         ORDER BY a.orden, a.id"""
                cursor.execute(sql, (pueblo_id,))
                atracciones = [dict(r) for r in cursor.fetchall()]
                atracciones.extend(self._negocios_como_atracciones(cursor, pueblo_id))
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Atracciones del pueblo listadas correctamente",
                    "data": atracciones
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar atracciones del pueblo: {str(e)}",
                "data": None
            })

    # ── GET BY ID ────────────────────────────────────────────
    async def get_atraccion_by_id(self, atraccion_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT a.id, a.nombre, a.tipo, a.descripcion, a.foto,
                                p.nombre AS pueblo
                         FROM atracciones a
                         LEFT JOIN pueblos p ON p.id = a.pueblo_id
                         WHERE a.id = %s"""
                cursor.execute(sql, (atraccion_id,))
                atraccion = cursor.fetchone()
                if atraccion:
                    return JSONResponse(status_code=200, content={
                        "success": True, "message": "Atracción encontrada", "data": dict(atraccion)
                    })
                return JSONResponse(status_code=404, content={
                    "success": False, "message": "Atracción no encontrada", "data": None
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar atracción: {str(e)}",
                "data": None
            })

    # ── CREATE ───────────────────────────────────────────────
    async def create_atraccion(self, data: Atraccion):
        try:
            with self.con.cursor() as cursor:
                sql = """INSERT INTO atracciones (nombre, tipo, descripcion, foto, pueblo_id, orden)
                         VALUES (%s, %s, %s, %s, %s, %s)
                         RETURNING id"""
                cursor.execute(sql, (data.nombre, data.tipo, data.descripcion, data.foto, data.pueblo_id, data.orden or 0))
                new_id = cursor.fetchone()[0]
                self.con.commit()
                return JSONResponse(status_code=201, content={
                    "success": True,
                    "message": "Atracción creada exitosamente",
                    "data": {"atraccion_id": new_id}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al crear atracción: {str(e)}",
                "data": None
            })

    # ── UPDATE ───────────────────────────────────────────────
    async def update_atraccion(self, atraccion_id: int, data: Atraccion):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM atracciones WHERE id = %s", (atraccion_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Atracción no encontrada", "data": None
                    })
                sql = """UPDATE atracciones
                         SET nombre=%s, tipo=%s, descripcion=%s, foto=%s, pueblo_id=%s, orden=%s
                         WHERE id=%s"""
                cursor.execute(sql, (data.nombre, data.tipo, data.descripcion, data.foto, data.pueblo_id, data.orden or 0, atraccion_id))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Atracción actualizada correctamente",
                    "data": {"filas_afectadas": cursor.rowcount}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al actualizar atracción: {str(e)}",
                "data": None
            })

    # ── DELETE ───────────────────────────────────────────────
    async def delete_atraccion(self, atraccion_id: int):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM atracciones WHERE id = %s", (atraccion_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Atracción no encontrada", "data": None
                    })
                cursor.execute("DELETE FROM atracciones WHERE id = %s", (atraccion_id,))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Atracción eliminada correctamente", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al eliminar atracción: {str(e)}",
                "data": None
            })
