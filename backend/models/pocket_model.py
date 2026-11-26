from typing import Union
from pydantic import BaseModel

from models.user_model import User


class Pocket(BaseModel):
    nombre: str
    saldo: int
    usuario: Union[int, User]
