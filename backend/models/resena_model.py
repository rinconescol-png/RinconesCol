from pydantic import BaseModel
from typing import Optional


class Resena(BaseModel):
    comentario: Optional[str] = None
    calificacion: Optional[int] = None   # valor entre 1 y 5
    usuario_id: Optional[int] = None
    pueblo_id: Optional[int] = None
