import os
from fastapi.responses import JSONResponse
import psycopg2.extras

from db.conexion import get_db_connection
from models.contacto_model import MensajeContacto
from services.email_service import enviar_correo

EMAIL_ADMIN = os.environ.get("EMAIL_ADMIN")


class ContactoService:
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

    # ── Guardar mensaje del formulario de contacto ──────────────────────────
    async def crear_mensaje(self, data: MensajeContacto):
        try:
            with self.con.cursor() as cursor:
                sql = """INSERT INTO mensajes_contacto (nombre, correo, mensaje)
                         VALUES (%s, %s, %s)
                         RETURNING id, fecha_envio"""
                cursor.execute(sql, (data.nombre, data.correo, data.mensaje))
                nuevo_id, fecha_envio = cursor.fetchone()
                self.con.commit()

            # Aviso al correo del negocio con el contenido del mensaje.
            # Si falla el envío, el mensaje ya quedó guardado en la BD igual.
            if EMAIL_ADMIN:
                cuerpo = f"""
                <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
                    <h2>Nuevo mensaje de contacto - RinconesCol</h2>
                    <p><strong>Nombre:</strong> {data.nombre}</p>
                    <p><strong>Correo:</strong> {data.correo}</p>
                    <p><strong>Mensaje:</strong></p>
                    <p>{data.mensaje}</p>
                    <p style="color:#888; font-size:12px;">Enviado el {fecha_envio}</p>
                </div>
                """
                enviar_correo(EMAIL_ADMIN, f"Nuevo mensaje de contacto de {data.nombre}", cuerpo)

            return JSONResponse(status_code=201, content={
                "success": True,
                "message": "Tu mensaje fue enviado con éxito",
                "data": {"id": nuevo_id}
            })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al guardar el mensaje: {str(e)}",
                "data": None
            })

    # ── Listar mensajes (solo admin, para revisarlos desde el panel) ────────
    async def get_mensajes(self):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, nombre, correo, mensaje, fecha_envio "
                    "FROM mensajes_contacto ORDER BY fecha_envio DESC"
                )
                filas = cursor.fetchall()

            # fecha_envio llega como datetime; se convierte a texto para que
            # JSONResponse pueda serializarlo sin errores.
            mensajes = []
            for fila in filas:
                fila = dict(fila)
                if fila.get("fecha_envio") is not None:
                    fila["fecha_envio"] = fila["fecha_envio"].isoformat()
                mensajes.append(fila)

            return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Mensajes obtenidos correctamente",
                "data": mensajes
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al obtener mensajes: {str(e)}",
                "data": None
            })
