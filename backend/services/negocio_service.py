from fastapi.responses import JSONResponse
import psycopg2.extras

from db.conexion import get_db_connection
from models.negocio_model import NegocioUpdate, NegocioFotoCreate, NegocioItem


class NegocioService:
    """
    Todas las operaciones de este servicio resuelven el negocio a partir del
    usuario_id del socio autenticado (nunca de un negocio_id que venga en la
    URL o en el cuerpo de la petición). Así, a nivel de código, es imposible
    que un socio edite el negocio de otro: simplemente no hay forma de
    "apuntarle" a un negocio ajeno desde estos endpoints.
    """

    _columna_ubicacion_lista = False

    def __init__(self):
        # Verificación temprana: falla rápido en el arranque si no hay BD.
        if get_db_connection() is None:
            print("No se pudo establecer conexión a la BD")

    # Garantiza que exista la columna "ubicacion" en "negocios" (equivale a
    # db/migration_negocio_ubicacion.sql). Es idempotente y solo corre una vez.
    def _asegurar_columna_ubicacion(self):
        if NegocioService._columna_ubicacion_lista:
            return
        try:
            con = self.con
            with con.cursor() as cursor:
                cursor.execute("ALTER TABLE negocios ADD COLUMN IF NOT EXISTS ubicacion TEXT")
            con.commit()
            NegocioService._columna_ubicacion_lista = True
        except Exception as e:
            print(f"No se pudo asegurar la columna ubicacion: {e}")
            try:
                self.con.rollback()
            except Exception:
                pass

    @property
    def con(self):
        # Pide la conexión viva en cada acceso (en vez de guardarla una
        # sola vez al arrancar). get_db_connection() ya sabe reconectar
        # si la conexión se cerró (PC en reposo, Postgres reiniciado,
        # inactividad prolongada, etc.), así el servicio nunca se queda
        # pegado a una conexión muerta hasta reiniciar el backend.
        return get_db_connection()

    # ── Helper interno: negocio del usuario autenticado ─────────────────────
    def _obtener_negocio_id(self, cursor, usuario_id: int):
        cursor.execute("SELECT id FROM negocios WHERE usuario_id = %s", (usuario_id,))
        fila = cursor.fetchone()
        return fila["id"] if fila else None

    # ── Helper interno: los "items" (platos/productos) traen "precio" como
    # NUMERIC en PostgreSQL, que psycopg2 devuelve como Decimal. Decimal no
    # es serializable a JSON directamente (por eso el error "Object of type
    # Decimal is not JSON serializable"), así que se convierte a float antes
    # de devolverlo en la respuesta.
    def _items_serializables(self, filas):
        items = [dict(r) for r in filas]
        for item in items:
            if item.get("precio") is not None:
                item["precio"] = float(item["precio"])
        return items

    # ── GET: negocio del socio autenticado (con fotos e items) ─────────────
    async def get_mi_negocio(self, usuario_id: int):
        try:
            self._asegurar_columna_ubicacion()
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # LEFT JOIN (en vez de JOIN): así, si por cualquier motivo el
                # pueblo_id del negocio no existiera, igual se muestra el
                # negocio del socio (con pueblo_nombre en null) en lugar de
                # desaparecer por completo detrás de un "sin negocio".
                cursor.execute(
                    """SELECT n.*, p.nombre AS pueblo_nombre
                       FROM negocios n
                       LEFT JOIN pueblos p ON p.id = n.pueblo_id
                       WHERE n.usuario_id = %s""",
                    (usuario_id,),
                )
                negocio = cursor.fetchone()
                if not negocio:
                    return JSONResponse(status_code=404, content={
                        "success": False,
                        "message": "Tu cuenta de socio todavía no tiene un negocio asociado",
                        "data": None
                    })
                negocio = dict(negocio)
                # "fecha_creacion" llega como objeto datetime desde psycopg2;
                # JSONResponse no puede serializarlo tal cual (por eso el
                # error "Object of type datetime is not JSON serializable").
                # Se convierte a texto ISO igual que ya se hace en
                # convenio_service.py con "fecha_envio".
                if negocio.get("fecha_creacion") is not None:
                    negocio["fecha_creacion"] = negocio["fecha_creacion"].isoformat()

                cursor.execute(
                    "SELECT id, url, orden FROM negocio_fotos WHERE negocio_id = %s ORDER BY orden, id",
                    (negocio["id"],),
                )
                negocio["fotos"] = [dict(r) for r in cursor.fetchall()]

                cursor.execute(
                    "SELECT id, nombre, descripcion, precio, foto, orden FROM negocio_items "
                    "WHERE negocio_id = %s ORDER BY orden, id",
                    (negocio["id"],),
                )
                negocio["items"] = self._items_serializables(cursor.fetchall())

                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Negocio encontrado", "data": negocio
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al consultar tu negocio: {str(e)}", "data": None
            })

    # ── PUT: editar descripción / foto de portada ───────────────────────────
    async def actualizar_mi_negocio(self, usuario_id: int, data: NegocioUpdate):
        try:
            self._asegurar_columna_ubicacion()
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                negocio_id = self._obtener_negocio_id(cursor, usuario_id)
                if negocio_id is None:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "No tienes un negocio asociado", "data": None
                    })

                campos, valores = [], []
                if data.descripcion is not None:
                    campos.append("descripcion = %s")
                    valores.append(data.descripcion)
                if data.foto is not None:
                    campos.append("foto = %s")
                    valores.append(data.foto)
                if data.ubicacion is not None:
                    campos.append("ubicacion = %s")
                    valores.append(data.ubicacion)

                if not campos:
                    return JSONResponse(status_code=400, content={
                        "success": False, "message": "No enviaste ningún campo para actualizar", "data": None
                    })

                valores.append(negocio_id)
                cursor.execute(f"UPDATE negocios SET {', '.join(campos)} WHERE id = %s", valores)
                self.con.commit()

                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Negocio actualizado correctamente", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al actualizar tu negocio: {str(e)}", "data": None
            })

    # ── Fotos ────────────────────────────────────────────────────────────────
    async def agregar_foto(self, usuario_id: int, data: NegocioFotoCreate):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                negocio_id = self._obtener_negocio_id(cursor, usuario_id)
                if negocio_id is None:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "No tienes un negocio asociado", "data": None
                    })

                cursor.execute("SELECT COALESCE(MAX(orden), -1) + 1 AS siguiente FROM negocio_fotos WHERE negocio_id = %s", (negocio_id,))
                siguiente_orden = cursor.fetchone()["siguiente"]

                cursor.execute(
                    "INSERT INTO negocio_fotos (negocio_id, url, orden) VALUES (%s, %s, %s) RETURNING id",
                    (negocio_id, data.url, siguiente_orden),
                )
                nuevo_id = cursor.fetchone()["id"]
                self.con.commit()

                return JSONResponse(status_code=201, content={
                    "success": True, "message": "Foto agregada", "data": {"id": nuevo_id}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al agregar la foto: {str(e)}", "data": None
            })

    async def eliminar_foto(self, usuario_id: int, foto_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                negocio_id = self._obtener_negocio_id(cursor, usuario_id)
                if negocio_id is None:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "No tienes un negocio asociado", "data": None
                    })

                # El WHERE incluye negocio_id: aunque alguien adivine el id de
                # una foto ajena, la consulta no borra nada si no es suya.
                cursor.execute(
                    "DELETE FROM negocio_fotos WHERE id = %s AND negocio_id = %s",
                    (foto_id, negocio_id),
                )
                if cursor.rowcount == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Foto no encontrada en tu negocio", "data": None
                    })
                self.con.commit()

                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Foto eliminada", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al eliminar la foto: {str(e)}", "data": None
            })

    # ── Items: platos / productos / servicios ───────────────────────────────
    async def crear_item(self, usuario_id: int, data: NegocioItem):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                negocio_id = self._obtener_negocio_id(cursor, usuario_id)
                if negocio_id is None:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "No tienes un negocio asociado", "data": None
                    })

                cursor.execute(
                    """INSERT INTO negocio_items (negocio_id, nombre, descripcion, precio, foto, orden)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                    (negocio_id, data.nombre, data.descripcion, data.precio, data.foto, data.orden or 0),
                )
                nuevo_id = cursor.fetchone()["id"]
                self.con.commit()

                return JSONResponse(status_code=201, content={
                    "success": True, "message": "Ítem agregado", "data": {"id": nuevo_id}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al crear el ítem: {str(e)}", "data": None
            })

    async def actualizar_item(self, usuario_id: int, item_id: int, data: NegocioItem):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                negocio_id = self._obtener_negocio_id(cursor, usuario_id)
                if negocio_id is None:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "No tienes un negocio asociado", "data": None
                    })

                cursor.execute(
                    """UPDATE negocio_items
                       SET nombre = %s, descripcion = %s, precio = %s, foto = %s, orden = %s
                       WHERE id = %s AND negocio_id = %s""",
                    (data.nombre, data.descripcion, data.precio, data.foto, data.orden or 0, item_id, negocio_id),
                )
                if cursor.rowcount == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Ítem no encontrado en tu negocio", "data": None
                    })
                self.con.commit()

                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Ítem actualizado", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al actualizar el ítem: {str(e)}", "data": None
            })

    # ── Público: negocios aliados de un pueblo (para destino.html) ─────────
    async def listar_por_pueblo(self, pueblo_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """SELECT id, nombre, categoria, descripcion, foto
                       FROM negocios WHERE pueblo_id = %s ORDER BY id""",
                    (pueblo_id,),
                )
                negocios = [dict(r) for r in cursor.fetchall()]
                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Negocios listados correctamente", "data": negocios
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al consultar negocios del pueblo: {str(e)}", "data": None
            })

    # ── Público: detalle completo de un negocio (para negocio-detalle.html) ─
    async def get_negocio_publico(self, negocio_id: int):
        try:
            self._asegurar_columna_ubicacion()
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """SELECT n.id, n.nombre, n.categoria, n.descripcion, n.foto, n.ubicacion, n.pueblo_id,
                              p.nombre AS pueblo_nombre, p.slug AS pueblo_slug
                       FROM negocios n
                       LEFT JOIN pueblos p ON p.id = n.pueblo_id
                       WHERE n.id = %s""",
                    (negocio_id,),
                )
                negocio = cursor.fetchone()
                if not negocio:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Negocio no encontrado", "data": None
                    })
                negocio = dict(negocio)

                cursor.execute(
                    "SELECT id, url, orden FROM negocio_fotos WHERE negocio_id = %s ORDER BY orden, id",
                    (negocio["id"],),
                )
                negocio["fotos"] = [dict(r) for r in cursor.fetchall()]

                cursor.execute(
                    "SELECT id, nombre, descripcion, precio, foto, orden FROM negocio_items "
                    "WHERE negocio_id = %s ORDER BY orden, id",
                    (negocio["id"],),
                )
                negocio["items"] = self._items_serializables(cursor.fetchall())

                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Negocio encontrado", "data": negocio
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al consultar el negocio: {str(e)}", "data": None
            })

    async def eliminar_item(self, usuario_id: int, item_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                negocio_id = self._obtener_negocio_id(cursor, usuario_id)
                if negocio_id is None:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "No tienes un negocio asociado", "data": None
                    })

                cursor.execute(
                    "DELETE FROM negocio_items WHERE id = %s AND negocio_id = %s",
                    (item_id, negocio_id),
                )
                if cursor.rowcount == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Ítem no encontrado en tu negocio", "data": None
                    })
                self.con.commit()

                return JSONResponse(status_code=200, content={
                    "success": True, "message": "Ítem eliminado", "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False, "message": f"Error al eliminar el ítem: {str(e)}", "data": None
            })
