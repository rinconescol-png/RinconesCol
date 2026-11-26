from pydantic import BaseModel
from typing import Optional


class Gastronomia(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    foto: Optional[str] = None
    pueblo_id: Optional[int] = None
    region: Optional[str] = None
