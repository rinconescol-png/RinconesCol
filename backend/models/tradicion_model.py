from pydantic import BaseModel
from typing import Optional


class Tradicion(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    epoca: Optional[str] = None
    foto: Optional[str] = None
    pueblo_id: Optional[int] = None
