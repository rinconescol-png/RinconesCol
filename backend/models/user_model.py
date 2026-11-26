from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, field_validator


# Modelo para crear / actualizar un usuario
class Usuario(BaseModel):
    nombre: str
    correo: str
    contrasena: str
    rol: Optional[Literal["admin", "visitante", "socio"]] = "visitante"


# Modelo para actualizar solo la contraseña
class CambioContrasena(BaseModel):
    nueva_contrasena: str


# Modelo para que el propio usuario (admin, visitante o socio) edite su
# nombre y/o su foto de perfil desde "Editar perfil". Ambos campos son
# opcionales: si el usuario no cambia alguno, el frontend simplemente no lo
# envía y el servicio conserva el valor que ya tenía en la base de datos.
class PerfilUpdate(BaseModel):
    nombre: Optional[str] = None
    foto_perfil: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El nombre no puede quedar vacío")
        return v

    @field_validator("foto_perfil")
    @classmethod
    def foto_formato_valido(cls, v):
        if v is not None:
            v = v.strip()
            # La foto llega como data URL en base64 (ver perfil.js, que ya
            # valida el tipo de archivo en el navegador antes de leerlo), o
            # como una URL http(s) por si en el futuro se permite pegar un
            # enlace en vez de subir un archivo.
            if v and not (v.startswith("data:image/") or v.startswith("http://") or v.startswith("https://")):
                raise ValueError("La foto de perfil debe ser una imagen válida")
        return v
