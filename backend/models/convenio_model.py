from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class SolicitudConvenio(BaseModel):
    nombre_negocio: str
    propietario: str
    tipo_negocio: str
    pueblo: str
    correo: EmailStr
    telefono: str
    mensaje: Optional[str] = None
    # Contraseña con la que el negocio podrá iniciar sesión como "Socio"
    # una vez que la solicitud sea aprobada manualmente por el equipo de
    # RinconesCol. Se guarda hasheada (ver ConvenioService.crear_solicitud).
    contrasena: str = Field(min_length=6)


class AprobarSolicitud(BaseModel):
    """Datos que el admin confirma al aprobar una solicitud de convenio."""
    # A qué pueblo real de la BD queda asociado el negocio (el texto libre
    # que el negocio escribió en "pueblo" es solo referencia para el admin).
    pueblo_id: int
    # Categoría bajo la cual el negocio aparecerá como atracción del pueblo.
    categoria: Literal["restaurante", "hotel", "cafeteria", "experiencia", "artesania"]
