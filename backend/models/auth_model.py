from pydantic import BaseModel, EmailStr


class UsuarioLogin(BaseModel):
    """Esquema de entrada para el login."""
    correo: EmailStr
    contrasena: str


class Token(BaseModel):
    """Estructura de respuesta del login/registro exitoso."""
    access_token: str
    token_type: str = "bearer"


class SolicitudRecuperacion(BaseModel):
    """Esquema de entrada para pedir el correo de recuperación de contraseña."""
    correo: EmailStr


class RestablecerContrasena(BaseModel):
    """Esquema de entrada para establecer la nueva contraseña desde el enlace."""
    token: str
    nueva_contrasena: str
