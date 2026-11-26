from pydantic import BaseModel
from typing import Optional


class Atraccion(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    descripcion: Optional[str] = None
    foto: Optional[str] = None
    pueblo_id: Optional[int] = None
    orden: Optional[int] = 0
