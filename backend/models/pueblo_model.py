from pydantic import BaseModel
from typing import Optional, List


class Restaurante(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    descripcion: Optional[str] = None


class Pueblo(BaseModel):
    nombre: str
    departamento: Optional[str] = None
    municipio: Optional[str] = None
    descripcion: Optional[str] = None
    historia: Optional[str] = None
    imagen: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    # Campos que necesita el frontend (destinos.html / destino.html)
    slug: Optional[str] = None
    region: Optional[str] = None
    sello: Optional[str] = None
    resumen: Optional[str] = None
    clima: Optional[str] = None
    ubicacion: Optional[str] = None
    alcalde: Optional[str] = None

    # Listas hijas (opcionales al crear/actualizar)
    actividades: Optional[List[str]] = None
    platos_tipicos: Optional[List[str]] = None
    donde_comer: Optional[List[Restaurante]] = None
