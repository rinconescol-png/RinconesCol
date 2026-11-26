import os
from datetime import datetime, timedelta, timezone
from fastapi.responses import JSONResponse
import psycopg2.extras

from db.conexion import get_db_connection
from models.user_model import Usuario
from models.auth_model import UsuarioLogin, SolicitudRecuperacion, RestablecerContrasena
from security.security import (
    hash_password,
    verify_password,
    create_access_token,
    generar_token_reset,
    hash_token_reset,
    RESET_TOKEN_EXPIRE_MINUTES,
)
from services.email_service import (
    enviar_correo,
    correo_bienvenida_usuario,
    correo_admin_nuevo_registro,
    correo_aviso_login_usuario,
    correo_admin_nuevo_login,
    correo_recuperacion_contrasena,
)

EMAIL_ADMIN = os.environ.get("EMAIL_ADMIN")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5500/frontend")


class AuthService:
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

    # ── REGISTRO (con hash de contraseña) ───────────────────────────────────
    async def registrar_usuario(self, data: Usuario):
        try:
            with self.con.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE correo = %s", (data.correo,))
                if cursor.fetchone()[0] > 0:
                    return JSONResponse(status_code=400, content={
                        "success": False,
                        "message": "El correo ya está registrado",
                        "data": None
                    })

                contrasena_hasheada = hash_password(data.contrasena)

                # El registro público SIEMPRE crea usuarios con rol "visitante",
                # sin importar lo que el cliente envíe en el campo "rol". Crear
                # administradores es una acción administrativa (ver
                # scripts/crear_admin.py o el endpoint POST /usuarios protegido).
                sql = """INSERT INTO usuarios (nombre, correo, contrasena, rol)
                         VALUES (%s, %s, %s, %s)
                         RETURNING id"""
                cursor.execute(sql, (data.nombre, data.correo, contrasena_hasheada, "visitante"))
                new_id = cursor.fetchone()[0]
                self.con.commit()

                access_token = create_access_token(data={"sub": data.correo})

                # Correo de bienvenida al usuario + aviso al correo del negocio.
                # Si el envío falla, no afecta el registro (ver email_service.py).
                enviar_correo(data.correo, "¡Bienvenido a RinconesCol!", correo_bienvenida_usuario(data.nombre))
                if EMAIL_ADMIN:
                    enviar_correo(EMAIL_ADMIN, "Nuevo registro en RinconesCol", correo_admin_nuevo_registro(data.nombre, data.correo))

                return JSONResponse(status_code=201, content={
                    "success": True,
                    "message": "Usuario registrado exitosamente",
                    "data": {
                        "usuario_id": new_id,
                        "access_token": access_token,
                        "token_type": "bearer"
                    }
                })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al registrar usuario: {str(e)}",
                "data": None
            })

    # ── LOGIN (verifica hash y entrega JWT) ─────────────────────────────────
    async def login(self, credenciales: UsuarioLogin):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, nombre, correo, contrasena, rol, foto_perfil FROM usuarios WHERE correo = %s",
                    (credenciales.correo,)
                )
                usuario = cursor.fetchone()

            if not usuario or not verify_password(credenciales.contrasena, usuario["contrasena"]):
                return JSONResponse(status_code=401, content={
                    "success": False,
                    "message": "Credenciales de acceso incorrectas",
                    "data": None
                })

            access_token = create_access_token(data={"sub": usuario["correo"]})

            # Aviso de inicio de sesión al usuario + aviso al correo del negocio.
            # Si el envío falla, no afecta el login (ver email_service.py).
            enviar_correo(usuario["correo"], "Inicio de sesión en RinconesCol", correo_aviso_login_usuario(usuario["nombre"]))
            if EMAIL_ADMIN:
                enviar_correo(EMAIL_ADMIN, "Nuevo inicio de sesión en RinconesCol", correo_admin_nuevo_login(usuario["nombre"], usuario["correo"]))

            return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Inicio de sesión exitoso",
                "data": {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "usuario": {
                        "id": usuario["id"],
                        "nombre": usuario["nombre"],
                        "correo": usuario["correo"],
                        "rol": usuario["rol"],
                        "foto_perfil": usuario["foto_perfil"]
                    }
                }
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al iniciar sesión: {str(e)}",
                "data": None
            })

    # ── RECUPERACIÓN DE CONTRASEÑA: paso 1, solicitar el enlace ─────────────
    async def solicitar_recuperacion(self, data: SolicitudRecuperacion):
        # Mensaje de respuesta SIEMPRE igual, exista o no el correo. Así no
        # se revela a quien pregunta si un correo está o no registrado.
        mensaje_generico = {
            "success": True,
            "message": "Si el correo está registrado, te enviamos un enlace para restablecer tu contraseña.",
            "data": None
        }
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, nombre, correo FROM usuarios WHERE correo = %s",
                    (data.correo,),
                )
                usuario = cursor.fetchone()

                if not usuario:
                    # No existe el correo: respondemos igual que si existiera,
                    # sin tocar la base de datos ni enviar correo. Esto SÍ se
                    # imprime en la consola del backend (nunca al cliente) para
                    # poder diagnosticar por qué "no llega el correo": si ves
                    # esta línea, la causa es que el correo ingresado no
                    # coincide con ningún registro en "usuarios".
                    print(f"[auth_service] solicitar_recuperacion: correo no registrado: {data.correo}")
                    return JSONResponse(status_code=200, content=mensaje_generico)

                token = generar_token_reset()
                token_hash = hash_token_reset(token)
                expira = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)

                cursor.execute(
                    """INSERT INTO password_reset_tokens (usuario_id, token_hash, fecha_expira)
                       VALUES (%s, %s, %s)""",
                    (usuario["id"], token_hash, expira),
                )
                self.con.commit()

            enlace = f"{FRONTEND_URL}/restablecer-contrasena.html?token={token}"
            enviado = enviar_correo(
                usuario["correo"],
                "Recupera tu contraseña en RinconesCol",
                correo_recuperacion_contrasena(usuario["nombre"], enlace),
            )
            if not enviado:
                # enviar_correo() ya imprime el detalle del error SMTP en la
                # consola (ver email_service.py); esta línea solo confirma
                # que el flujo llegó hasta aquí (el token SÍ se creó en la
                # BD) pero el correo no salió.
                print(f"[auth_service] solicitar_recuperacion: token creado pero el correo no se pudo enviar a {usuario['correo']}")

            return JSONResponse(status_code=200, content=mensaje_generico)
        except Exception as e:
            self.con.rollback()
            # El mensaje que ve el usuario sigue siendo genérico (no se
            # revela info al cliente), pero el error real SÍ queda impreso
            # en la consola del backend para poder diagnosticarlo. Antes
            # este error se perdía por completo.
            print(f"[auth_service] Error en solicitar_recuperacion: {e}")
            return JSONResponse(status_code=200, content=mensaje_generico)

    # ── RECUPERACIÓN DE CONTRASEÑA: paso 2, usar el token y cambiarla ───────
    async def restablecer_contrasena(self, data: RestablecerContrasena):
        try:
            token_hash = hash_token_reset(data.token)

            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """SELECT id, usuario_id, fecha_expira, usado
                       FROM password_reset_tokens WHERE token_hash = %s""",
                    (token_hash,),
                )
                registro = cursor.fetchone()

                token_invalido = JSONResponse(status_code=400, content={
                    "success": False,
                    "message": "El enlace de recuperación no es válido o ya expiró. Solicita uno nuevo.",
                    "data": None
                })

                # Diagnóstico en consola: por qué se rechazó el token.
                # (No se le muestra esto al usuario, solo al backend.)
                if not registro:
                    cursor.execute("SELECT COUNT(*) FROM password_reset_tokens")
                    total = cursor.fetchone()["count"]
                    print(f"[auth_service] reset-password: token no encontrado en la BD "
                          f"(hash={token_hash[:12]}...). Filas totales en password_reset_tokens: {total}. "
                          f"Si 'total' es 0, la tabla está vacía o el INSERT de forgot-password "
                          f"está fallando en silencio (revisa consola en ese paso).")
                    return token_invalido
                if registro["usado"]:
                    print(f"[auth_service] reset-password: token encontrado (id={registro['id']}) "
                          f"pero ya estaba marcado como usado.")
                    return token_invalido

                ahora = datetime.now(timezone.utc)
                fecha_expira = registro["fecha_expira"]
                if fecha_expira.tzinfo is None:
                    fecha_expira = fecha_expira.replace(tzinfo=timezone.utc)
                if ahora > fecha_expira:
                    print(f"[auth_service] reset-password: token encontrado (id={registro['id']}) "
                          f"pero ya expiró. Expiraba: {fecha_expira} — ahora: {ahora}.")
                    return token_invalido

                nueva_hasheada = hash_password(data.nueva_contrasena)

                cursor.execute(
                    "UPDATE usuarios SET contrasena = %s WHERE id = %s",
                    (nueva_hasheada, registro["usuario_id"]),
                )
                # El token deja de servir de inmediato, se haya o no usado antes:
                # de un solo uso, siempre.
                cursor.execute(
                    "UPDATE password_reset_tokens SET usado = TRUE WHERE id = %s",
                    (registro["id"],),
                )
                self.con.commit()

            return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Tu contraseña fue restablecida correctamente. Ya puedes iniciar sesión.",
                "data": None
            })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al restablecer la contraseña: {str(e)}",
                "data": None
            })