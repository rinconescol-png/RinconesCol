from pydantic import BaseModel, EmailStr


class MensajeContacto(BaseModel):
    nombre: str
    correo: EmailStr
    mensaje: str
