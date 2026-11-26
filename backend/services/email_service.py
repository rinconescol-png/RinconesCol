import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_ADMIN = os.environ.get("EMAIL_ADMIN", EMAIL_USER)


def enviar_correo(destinatarios, asunto: str, cuerpo_html: str) -> bool:
    """
    Envía un correo HTML a uno o varios destinatarios usando SMTP (Gmail).

    - `destinatarios` puede ser un string ("correo@ejemplo.com") o una lista
      de strings (["a@x.com", "b@x.com"]).
    - Si EMAIL_USER / EMAIL_PASSWORD no están configurados en el .env, o si
      el envío falla por cualquier razón (credenciales, red, etc.), la
      función NO lanza una excepción hacia quien la llama: solo imprime el
      error en consola y devuelve False. Así, un problema con el correo
      nunca tumba el registro, el login o el formulario de contacto.
    """
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("[email_service] EMAIL_USER / EMAIL_PASSWORD no configurados en .env, no se envía correo.")
        return False

    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = EMAIL_USER
    mensaje["To"] = ", ".join(destinatarios)
    mensaje.attach(MIMEText(cuerpo_html, "html"))

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as servidor:
            servidor.starttls()
            servidor.login(EMAIL_USER, EMAIL_PASSWORD)
            servidor.sendmail(EMAIL_USER, destinatarios, mensaje.as_string())
        print(f"[email_service] Correo '{asunto}' enviado a: {', '.join(destinatarios)}")
        return True
    except Exception as e:
        print(f"[email_service] Error al enviar correo: {e}")
        return False


# ── Plantillas de correo reutilizables ──────────────────────────────────────

def correo_bienvenida_usuario(nombre: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2 style="color:#2f6f4f;">¡Bienvenido a RinconesCol, {nombre}! 🌄</h2>
        <p>Tu cuenta se creó correctamente. Ya puedes iniciar sesión y explorar
        los mejores pueblos, gastronomía y tradiciones de Colombia.</p>
        <p>Gracias por unirte a nuestra comunidad.</p>
        <p style="color:#888; font-size:12px;">Este es un correo automático, no respondas a este mensaje.</p>
    </div>
    """


def correo_admin_nuevo_registro(nombre: str, correo: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Nuevo usuario registrado en RinconesCol</h2>
        <p><strong>Nombre:</strong> {nombre}</p>
        <p><strong>Correo:</strong> {correo}</p>
    </div>
    """


def correo_aviso_login_usuario(nombre: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Hola {nombre},</h2>
        <p>Detectamos un inicio de sesión en tu cuenta de RinconesCol.</p>
        <p>Si fuiste tú, no necesitas hacer nada. Si no reconoces este acceso,
        te recomendamos cambiar tu contraseña.</p>
        <p style="color:#888; font-size:12px;">Este es un correo automático, no respondas a este mensaje.</p>
    </div>
    """


def correo_admin_nuevo_login(nombre: str, correo: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Inicio de sesión en RinconesCol</h2>
        <p><strong>Usuario:</strong> {nombre}</p>
        <p><strong>Correo:</strong> {correo}</p>
    </div>
    """


def correo_recuperacion_contrasena(nombre: str, enlace: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2 style="color:#2f6f4f;">Recupera tu contraseña</h2>
        <p>Hola {nombre},</p>
        <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta
        en RinconesCol. Si fuiste tú, haz clic en el siguiente enlace para
        crear una nueva contraseña:</p>
        <p style="text-align:center; margin: 24px 0;">
            <a href="{enlace}" style="background:#2f6f4f; color:#fff; padding:12px 24px;
               border-radius:8px; text-decoration:none; font-weight:600;">
               Restablecer mi contraseña
            </a>
        </p>
        <p>Este enlace es válido por 30 minutos y solo se puede usar una vez.
        Si no solicitaste este cambio, puedes ignorar este correo: tu
        contraseña actual seguirá funcionando con normalidad.</p>
        <p style="color:#888; font-size:12px;">Este es un correo automático, no respondas a este mensaje.</p>
    </div>
    """


def correo_convenio_aprobado(nombre_negocio: str, propietario: str, correo: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2 style="color:#2f6f4f;">¡Tu negocio ya es parte de RinconesCol! 🎉</h2>
        <p>Hola {propietario},</p>
        <p>Tu solicitud de convenio para <strong>{nombre_negocio}</strong> fue aprobada.
        Ya puedes iniciar sesión en RinconesCol como <strong>Socio</strong>, usando
        el correo <strong>{correo}</strong> y la contraseña que registraste en el
        formulario de solicitud.</p>
        <p>Desde tu panel de socio podrás actualizar la descripción, las fotos y
        los platos/productos/servicios de tu negocio.</p>
        <p style="color:#888; font-size:12px;">Este es un correo automático, no respondas a este mensaje.</p>
    </div>
    """


def correo_convenio_rechazado(nombre_negocio: str, propietario: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Sobre tu solicitud de convenio</h2>
        <p>Hola {propietario},</p>
        <p>Gracias por tu interés en unir a <strong>{nombre_negocio}</strong> a
        RinconesCol. Por ahora no fue posible aprobar tu solicitud. Si crees que
        se trata de un error o quieres más información, puedes escribirnos por
        el formulario de contacto.</p>
        <p style="color:#888; font-size:12px;">Este es un correo automático, no respondas a este mensaje.</p>
    </div>
    """
