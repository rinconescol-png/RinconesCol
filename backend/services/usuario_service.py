from fastapi.responses import JSONResponse
import psycopg2.extras
from db.conexion import get_db_connection
from models.user_model import Usuario, PerfilUpdate
from security.security import hash_password


class UsuarioService:
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
    async def get_usuarios(self):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, nombre, correo, rol, fecha_registro::text FROM usuarios"
                )
                usuarios = [dict(r) for r in cursor.fetchall()]
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Usuarios listados correctamente",
                    "data": usuarios
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar usuarios: {str(e)}",
                "data": None
            })

    # ── GET BY ID ────────────────────────────────────────────
    async def get_usuario_by_id(self, usuario_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, nombre, correo, rol, fecha_registro::text FROM usuarios WHERE id = %s",
                    (usuario_id,)
                )
                usuario = cursor.fetchone()
                if usuario:
                    return JSONResponse(status_code=200, content={
                        "success": True,
                        "message": "Usuario encontrado",
                        "data": dict(usuario)
                    })
                return JSONResponse(status_code=404, content={
                    "success": False,
                    "message": "Usuario no encontrado",
                    "data": None
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar usuario: {str(e)}",
                "data": None
            })

    # ── CREATE ───────────────────────────────────────────────
    async def create_usuario(self, data: Usuario):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE correo = %s", (data.correo,))
                if cursor.fetchone()[0] > 0:
                    return JSONResponse(status_code=400, content={
                        "success": False,
                        "message": "El correo ya está registrado",
                        "data": None
                    })
                sql = """INSERT INTO usuarios (nombre, correo, contrasena, rol)
                         VALUES (%s, %s, %s, %s)
                         RETURNING id"""
                cursor.execute(sql, (data.nombre, data.correo, hash_password(data.contrasena), data.rol))
                new_id = cursor.fetchone()[0]
                self.con.commit()
                return JSONResponse(status_code=201, content={
                    "success": True,
                    "message": "Usuario creado exitosamente",
                    "data": {"usuario_id": new_id}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al crear usuario: {str(e)}",
                "data": None
            })

    # ── UPDATE ───────────────────────────────────────────────
    async def update_usuario(self, usuario_id: int, data: Usuario):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE id = %s", (usuario_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Usuario no encontrado", "data": None
                    })
                sql = """UPDATE usuarios
                         SET nombre=%s, correo=%s, contrasena=%s, rol=%s
                         WHERE id=%s"""
                cursor.execute(sql, (data.nombre, data.correo, hash_password(data.contrasena), data.rol, usuario_id))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Usuario actualizado correctamente",
                    "data": {"filas_afectadas": cursor.rowcount}
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al actualizar usuario: {str(e)}",
                "data": None
            })

    # ── PERFIL PROPIO: consultar (incluye foto_perfil) ─────────────────────
    async def get_mi_perfil(self, usuario_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, nombre, correo, rol, foto_perfil, fecha_registro::text "
                    "FROM usuarios WHERE id = %s",
                    (usuario_id,)
                )
                usuario = cursor.fetchone()
                if usuario:
                    return JSONResponse(status_code=200, content={
                        "success": True,
                        "message": "Perfil encontrado",
                        "data": dict(usuario)
                    })
                return JSONResponse(status_code=404, content={
                    "success": False, "message": "Usuario no encontrado", "data": None
                })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al consultar tu perfil: {str(e)}",
                "data": None
            })

    # ── PERFIL PROPIO: editar nombre y/o foto ───────────────────────────────
    # El usuario_id SIEMPRE viene del token del usuario autenticado (ver
    # routes.py), nunca de la URL ni del cuerpo de la petición: así, a nivel
    # de código, es imposible que alguien edite el perfil de otra cuenta.
    async def actualizar_mi_perfil(self, usuario_id: int, data: PerfilUpdate):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Solo se arma el UPDATE con los campos que realmente
                # llegaron; el campo que el usuario no tocó conserva el
                # valor que ya tenía en la base de datos.
                campos, valores = [], []
                if data.nombre is not None:
                    campos.append("nombre = %s")
                    valores.append(data.nombre)
                if data.foto_perfil is not None:
                    campos.append("foto_perfil = %s")
                    valores.append(data.foto_perfil)

                if not campos:
                    return JSONResponse(status_code=400, content={
                        "success": False, "message": "No enviaste ningún cambio para guardar", "data": None
                    })

                valores.append(usuario_id)
                cursor.execute(
                    f"UPDATE usuarios SET {', '.join(campos)} WHERE id = %s "
                    f"RETURNING id, nombre, correo, rol, foto_perfil",
                    valores
                )
                actualizado = cursor.fetchone()
                self.con.commit()

                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Perfil actualizado correctamente",
                    "data": dict(actualizado)
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al actualizar tu perfil: {str(e)}",
                "data": None
            })

    # ── DELETE ───────────────────────────────────────────────
    async def delete_usuario(self, usuario_id: int):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE id = %s", (usuario_id,))
                if cursor.fetchone()[0] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Usuario no encontrado", "data": None
                    })
                cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
                self.con.commit()
                return JSONResponse(status_code=200, content={
                    "success": True,
                    "message": "Usuario eliminado correctamente",
                    "data": None
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al eliminar usuario: {str(e)}",
                "data": None
            })
