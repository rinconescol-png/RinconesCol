from pydantic import BaseModel
from typing import Optional


class ItinerarioItem(BaseModel):
    pueblo_id: int
    # 'manana' | 'tarde' | 'noche'
    franja: str
    orden: Optional[int] = 0
    hora_sugerida: Optional[str] = None
    actividad: str
    descripcion: Optional[str] = None
    # Opcional: enlaza este paso del itinerario a una fila concreta de "atracciones"
    atraccion_id: Optional[int] = None
