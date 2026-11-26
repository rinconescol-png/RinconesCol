from typing import Optional
from pydantic import BaseModel, field_validator

# Las fotos del negocio llegan como archivo local convertido a data URL (base64)
# desde panel-socio.html. Se siguen aceptando URLs http(s) ya guardadas.
# ~2 MB de imagen en base64 ocupan ~2.8 MB de texto; se deja margen.
MAX_LARGO_FOTO = 3_000_000


def _validar_foto(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        return v
    if not (v.startswith("data:image/") or v.startswith("http://") or v.startswith("https://")):
        raise ValueError("La foto debe ser una imagen válida")
    if len(v) > MAX_LARGO_FOTO:
        raise ValueError("La imagen es muy pesada. El tamaño máximo permitido es 2 MB")
    return v


# ── Lo único que el socio puede editar de su negocio ─────────────────────────
class NegocioUpdate(BaseModel):
    descripcion: Optional[str] = None
    foto: Optional[str] = None  # foto de portada
    ubicacion: Optional[str] = None  # dónde está ubicado el negocio

    @field_validator("foto")
    @classmethod
    def foto_valida(cls, v):
        return _validar_foto(v)

    @field_validator("ubicacion")
    @classmethod
    def ubicacion_valida(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 300:
            raise ValueError("La ubicación es muy larga (máximo 300 caracteres)")
        return v


class NegocioFotoCreate(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_valida(cls, v):
        v = _validar_foto(v)
        if not v:
            raise ValueError("Debes elegir una foto")
        return v


class NegocioItem(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    foto: Optional[str] = None
    orden: Optional[int] = 0

    @field_validator("foto")
    @classmethod
    def foto_valida(cls, v):
        return _validar_foto(v)
