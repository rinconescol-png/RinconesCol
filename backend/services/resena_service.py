import os
from typing import Optional
from fastapi.responses import JSONResponse
import psycopg2.extras
from db.conexion import get_db_connection
from models.resena_model import Resena
from services.email_service import enviar_correo

EMAIL_ADMIN = os.environ.get("EMAIL_ADMIN")
LIMITE_RESENAS_POR_PUEBLO = 3


class ResenaService:
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

    # ── GET ALL (opcionalmente filtradas por pueblo) ─────────
    async def get_resenas(self, pueblo_id: Optional[int] = None):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT r.id, r.comentario, r.calificacion, r.fecha::text,
                                r.pueblo_id, u.nombre AS usuario, p.nombre AS pueblo
                         FROM resenas r
                         LEFT JOIN usuarios u ON u.id = r.usuario_id
                         LEFT JOIN pueblos  p ON p.id = r.pueblo_id"""
                parametros = ()
                if pueblo_id is not None:
                    sql += " WHERE r.pueblo_id = %s"
                    parametros = (pueblo_id,)
                sql += " ORDER BY r.fecha DESC"
                cursor.execute(sql, parametros)
                resenas = [dict(r) for r in cursor.fetchall()]
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Reseñas listadas correctamente",
                    "data": resenas
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar reseñas: {str(e)}",
                "data": None
            })

    # ── GET BY ID ────────────────────────────────────────────
    async def get_resena_by_id(self, resena_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """SELECT r.id, r.comentario, r.calificacion, r.fecha::text,
                                u.nombre AS usuario, p.nombre AS pueblo
                         FROM resenas r
                         LEFT JOIN usuarios u ON u.id = r.usuario_id
                         LEFT JOIN pueblos  p ON p.id = r.pueblo_id
                         WHERE r.id = %s"""
                cursor.execute(sql, (resena_id,))
                resena = cursor.fetchone()
                if resena:
                    return JSONResponse(status_code=200, content={
                        "success": True, "message": "Reseña encontrada", "data": dict(resena)
                    })
                return JSONResponse(status_code=404, content={
                    "success": False, "message": "Reseña no encontrada", "data": None
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar reseña: {str(e)}",
                "data": None
            })

    # ── Estado del límite de reseñas para el usuario autenticado ─────────
    async def get_estado_limite(self, usuario_id: int, pueblo_id: int):
        """Cuenta únicamente las reseñas que siguen guardadas en la tabla.

        El borrado administrativo es físico (DELETE), por lo que una reseña
        eliminada deja de participar automáticamente en este conteo.
        """
        try:
            with self.con.cursor() as cursor:
                cursor.execute(
                    """SELECT COUNT(*) FROM resenas
                       WHERE usuario_id = %s AND pueblo_id = %s""",
                    (usuario_id, pueblo_id),
                )
                publicadas = int(cursor.fetchone()[0])
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Límite de reseñas consultado correctamente",
                    "data": {
                        "publicadas": publicadas,
                        "limite": LIMITE_RESENAS_POR_PUEBLO,
                        "disponibles": max(0, LIMITE_RESENAS_POR_PUEBLO - publicadas),
                        "puede_publicar": publicadas < LIMITE_RESENAS_POR_PUEBLO,
                    },
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar el límite de reseñas: {str(e)}",
                "data": None,
            })

    # ── Propietario (para permisos: dueño o admin) ────────────
    async def obtener_propietario(self, resena_id: int):
        with self.con.cursor() as cursor:
            cursor.execute("SELECT usuario_id FROM resenas WHERE id = %s", (resena_id,))
            fila = cursor.fetchone()
            return fila[0] if fila else None

    # ── CREATE ───────────────────────────────────────────────
    async def create_resena(self, data: Resena):
        try:
            if not data.usuario_id or not data.pueblo_id:
                return JSONResponse(status_code=400, content={
                    "success": False,
                    "message": "No fue posible identificar al usuario o al pueblo de la reseña.",
                    "data": None,
                })
            if not data.comentario or not data.comentario.strip():
                return JSONResponse(status_code=400, content={
                    "success": False, "message": "Escribe un comentario antes de publicar.", "data": None,
                })
            if data.calificacion is None or not 1 <= data.calificacion <= 5:
                return JSONResponse(status_code=400, content={
                    "success": False, "message": "La calificación debe estar entre 1 y 5 estrellas.", "data": None,
                })

            with self.con.cursor() as cursor:
                # El bloqueo transaccional por usuario + pueblo evita que dos
                # peticiones simultáneas superen el máximo de tres reseñas.
                # Ambos identificadores son enteros de PostgreSQL.
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(%s, %s)",
                    (int(data.usuario_id), int(data.pueblo_id)),
                )

                cursor.execute("SELECT id FROM pueblos WHERE id = %s", (data.pueblo_id,))
                if cursor.fetchone() is None:
                    self.con.rollback()
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "El pueblo seleccionado no existe.", "data": None,
                    })

                cursor.execute(
                    """SELECT COUNT(*) FROM resenas
                       WHERE usuario_id = %s AND pueblo_id = %s""",
                    (data.usuario_id, data.pueblo_id),
                )
                total_actual = int(cursor.fetchone()[0])
                if total_actual >= LIMITE_RESENAS_POR_PUEBLO:
                    self.con.rollback()
                    return JSONResponse(status_code=409, content={
                        "success": False,
                        "message": "Ya alcanzaste el máximo de 3 reseñas para este pueblo. Puedes consultar las opiniones, pero no publicar otra por ahora.",
                        "data": {
                            "publicadas": total_actual,
                            "limite": LIMITE_RESENAS_POR_PUEBLO,
                            "puede_publicar": False,
                        },
                    })

                sql = """INSERT INTO resenas (comentario, calificacion, usuario_id, pueblo_id)
                         VALUES (%s, %s, %s, %s)
                         RETURNING id"""
                cursor.execute(sql, (
                    data.comentario.strip(), data.calificacion, data.usuario_id, data.pueblo_id
                ))
                new_id = cursor.fetchone()[0]

                # Datos legibles para el aviso de correo. Se consultan antes
                # del commit, dentro de la misma transacción.
                cursor.execute("SELECT nombre FROM pueblos WHERE id = %s", (data.pueblo_id,))
                fila_pueblo = cursor.fetchone()
                nombre_pueblo = fila_pueblo[0] if fila_pueblo else "un destino"
                cursor.execute("SELECT nombre FROM usuarios WHERE id = %s", (data.usuario_id,))
                fila_usuario = cursor.fetchone()
                nombre_usuario = fila_usuario[0] if fila_usuario else "Un viajero"
                self.con.commit()

            # Aviso al correo del negocio con el contenido de la reseña.
            # Si el envío falla, la reseña ya quedó guardada en la BD igual
            # (mismo criterio que usa contacto_service).
            if EMAIL_ADMIN:
                estrellas = "★" * (data.calificacion or 0) + "☆" * (5 - (data.calificacion or 0))
                cuerpo = f"""
                <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
                    <h2>Nueva reseña en RinconesCol</h2>
                    <p><strong>Destino:</strong> {nombre_pueblo}</p>
                    <p><strong>Usuario:</strong> {nombre_usuario}</p>
                    <p><strong>Calificación:</strong> {estrellas} ({data.calificacion}/5)</p>
                    <p><strong>Comentario:</strong></p>
                    <p>{data.comentario}</p>
                </div>
                """
                try:
                    enviar_correo(EMAIL_ADMIN, f"Nueva reseña de {nombre_usuario} sobre {nombre_pueblo}", cuerpo)
                except Exception as error_correo:
                    # Un error SMTP no debe convertir en fallida una reseña
                    # que ya quedó correctamente guardada en PostgreSQL.
                    print(f"No se pudo enviar el aviso de reseña: {error_correo}")

            return JSONResponse(status_code=201, content={
                "success": True,
                "message": "Reseña creada exitosamente",
                "data": {
                    "resena_id": new_id,
                    "publicadas": total_actual + 1,
                    "limite": LIMITE_RESENAS_POR_PUEBLO,
                    "puede_publicar": total_actual + 1 < LIMITE_RESENAS_POR_PUEBLO,
                }
            })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al crear reseña: {str(e)}",
                "data": None
            })

    # ── UPDATE ───────────────────────────────────────────────
    async def update_resena(self, resena_id: int, data: Resena):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM resenas WHERE id = %s", (resena_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Reseña no encontrada", "data": None
                    })
                sql = """UPDATE resenas
                         SET comentario=%s, calificacion=%s, usuario_id=%s, pueblo_id=%s
                         WHERE id=%s"""
                cursor.execute(sql, (data.comentario, data.calificacion, data.usuario_id, data.pueblo_id, resena_id))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Reseña actualizada correctamente",
                    "data": {"filas_afectadas": cursor.rowcount}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al actualizar reseña: {str(e)}",
                "data": None
            })

    # ── DELETE ───────────────────────────────────────────────
    async def delete_resena(self, resena_id: int):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM resenas WHERE id = %s", (resena_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Reseña no encontrada", "data": None
                    })
                cursor.execute("DELETE FROM resenas WHERE id = %s", (resena_id,))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Reseña eliminada correctamente", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al eliminar reseña: {str(e)}",
                "data": None
            })
