import os
from fastapi.responses import JSONResponse
import psycopg2.extras

from db.conexion import get_db_connection
from models.convenio_model import SolicitudConvenio, AprobarSolicitud
from security.security import hash_password
from services.email_service import (
    enviar_correo,
    correo_convenio_aprobado,
    correo_convenio_rechazado,
)

EMAIL_ADMIN = os.environ.get("EMAIL_ADMIN")

# Mapa entre la categoría interna (la que usan "negocios" y AprobarSolicitud)
# y una etiqueta legible para mostrar como "tipo" de atracción en el pueblo.
ETIQUETA_CATEGORIA = {
    "restaurante": "Restaurante",
    "hotel": "Hotel / Posada",
    "cafeteria": "Cafetería",
    "experiencia": "Experiencia turística",
    "artesania": "Artesanías / Emprendimiento",
}


class ConvenioService:
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

    # ── Guardar solicitud de convenio ────────────────────────────────────────
    async def crear_solicitud(self, data: SolicitudConvenio):
        try:
            contrasena_hasheada = hash_password(data.contrasena)
            with self.con.cursor() as cursor:
                sql = """INSERT INTO solicitudes_convenio
                         (nombre_negocio, propietario, tipo_negocio, pueblo, correo, telefono, mensaje, contrasena)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                         RETURNING id, fecha_envio"""
                cursor.execute(sql, (
                    data.nombre_negocio, data.propietario, data.tipo_negocio,
                    data.pueblo, data.correo, data.telefono, data.mensaje,
                    contrasena_hasheada,
                ))
                nuevo_id, fecha_envio = cursor.fetchone()
                self.con.commit()

            # Aviso al correo del negocio con el contenido de la solicitud.
            # Si falla el envío, la solicitud ya quedó guardada en la BD igual.
            if EMAIL_ADMIN:
                cuerpo = f"""
                <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
                    <h2>Nueva solicitud de convenio - RinconesCol</h2>
                    <p><strong>Negocio:</strong> {data.nombre_negocio}</p>
                    <p><strong>Propietario:</strong> {data.propietario}</p>
                    <p><strong>Tipo de negocio:</strong> {data.tipo_negocio}</p>
                    <p><strong>Pueblo/región:</strong> {data.pueblo}</p>
                    <p><strong>Correo:</strong> {data.correo}</p>
                    <p><strong>Teléfono:</strong> {data.telefono}</p>
                    <p><strong>Mensaje:</strong></p>
                    <p>{data.mensaje or "(sin mensaje adicional)"}</p>
                    <p style="color:#888; font-size:12px;">Enviado el {fecha_envio}</p>
                </div>
                """
                enviar_correo(EMAIL_ADMIN, f"Nueva solicitud de convenio: {data.nombre_negocio}", cuerpo)

            return JSONResponse(status_code=201, content={
                "success": True,
                "message": "Tu solicitud fue enviada con éxito",
                "data": {"id": nuevo_id}
            })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al guardar la solicitud: {str(e)}",
                "data": None
            })

    # ── Listar solicitudes (solo admin, para revisarlas desde el panel) ─────
    async def get_solicitudes(self):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, nombre_negocio, propietario, tipo_negocio, pueblo, "
                    "correo, telefono, mensaje, fecha_envio, estado, usuario_id "
                    "FROM solicitudes_convenio ORDER BY fecha_envio DESC"
                )
                filas = cursor.fetchall()

            solicitudes = []
            for fila in filas:
                fila = dict(fila)
                if fila.get("fecha_envio") is not None:
                    fila["fecha_envio"] = fila["fecha_envio"].isoformat()
                solicitudes.append(fila)

            return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Solicitudes obtenidas correctamente",
                "data": solicitudes
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al obtener solicitudes: {str(e)}",
                "data": None
            })

    # ── Aprobar solicitud: crea el usuario "socio" + el negocio ─────────────
    async def aprobar_solicitud(self, solicitud_id: int, datos: AprobarSolicitud):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM solicitudes_convenio WHERE id = %s", (solicitud_id,)
                )
                solicitud = cursor.fetchone()

                if not solicitud:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Solicitud no encontrada", "data": None
                    })
                if solicitud["estado"] != "pendiente":
                    return JSONResponse(status_code=400, content={
                        "success": False,
                        "message": f"La solicitud ya fue {solicitud['estado']}",
                        "data": None
                    })

                cursor.execute("SELECT COUNT(*) AS c FROM pueblos WHERE id = %s", (datos.pueblo_id,))
                if cursor.fetchone()["c"] == 0:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "El pueblo indicado no existe", "data": None
                    })

                # Si el correo ya tiene una cuenta (ej. ya era "visitante"),
                # no se crea otra: simplemente se sube su rol a "socio".
                cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (solicitud["correo"],))
                usuario_existente = cursor.fetchone()

                if usuario_existente:
                    usuario_id = usuario_existente["id"]
                    cursor.execute(
                        "UPDATE usuarios SET rol = 'socio' WHERE id = %s", (usuario_id,)
                    )
                else:
                    cursor.execute(
                        """INSERT INTO usuarios (nombre, correo, contrasena, rol)
                           VALUES (%s, %s, %s, 'socio') RETURNING id""",
                        (solicitud["propietario"], solicitud["correo"], solicitud["contrasena"]),
                    )
                    usuario_id = cursor.fetchone()["id"]

                cursor.execute(
                    """INSERT INTO negocios
                       (usuario_id, solicitud_id, pueblo_id, nombre, categoria, descripcion, correo, telefono)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        usuario_id, solicitud_id, datos.pueblo_id, solicitud["nombre_negocio"],
                        datos.categoria, solicitud["mensaje"], solicitud["correo"], solicitud["telefono"],
                    ),
                )
                negocio_id = cursor.fetchone()["id"]

                cursor.execute(
                    "UPDATE solicitudes_convenio SET estado = 'aprobado', usuario_id = %s WHERE id = %s",
                    (usuario_id, solicitud_id),
                )
                self.con.commit()

            enviar_correo(
                solicitud["correo"],
                "¡Tu negocio ya es parte de RinconesCol!",
                correo_convenio_aprobado(solicitud["nombre_negocio"], solicitud["propietario"], solicitud["correo"]),
            )

            return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Solicitud aprobada: el negocio ya puede iniciar sesión como Socio",
                "data": {"usuario_id": usuario_id, "negocio_id": negocio_id}
            })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al aprobar la solicitud: {str(e)}",
                "data": None
            })

    # ── Rechazar solicitud ───────────────────────────────────────────────────
    async def rechazar_solicitud(self, solicitud_id: int):
        try:
            with self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM solicitudes_convenio WHERE id = %s", (solicitud_id,))
                solicitud = cursor.fetchone()
                if not solicitud:
                    return JSONResponse(status_code=404, content={
                        "success": False, "message": "Solicitud no encontrada", "data": None
                    })
                if solicitud["estado"] != "pendiente":
                    return JSONResponse(status_code=400, content={
                        "success": False,
                        "message": f"La solicitud ya fue {solicitud['estado']}",
                        "data": None
                    })

                cursor.execute(
                    "UPDATE solicitudes_convenio SET estado = 'rechazado' WHERE id = %s",
                    (solicitud_id,),
                )
                self.con.commit()

            enviar_correo(
                solicitud["correo"],
                "Sobre tu solicitud de convenio en RinconesCol",
                correo_convenio_rechazado(solicitud["nombre_negocio"], solicitud["propietario"]),
            )

            return JSONResponse(status_code=200, content={
                "success": True, "message": "Solicitud rechazada", "data": None
            })
        except Exception as e:
            self.con.rollback()
            return JSONResponse(status_code=500, content={
                "success": False,
                "message": f"Error al rechazar la solicitud: {str(e)}",
                "data": None
            })
