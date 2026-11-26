import os
import hashlib
import hmac
import binascii
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
import psycopg2.extras

from db.conexion import get_db_connection

# Cargamos el archivo .env en el sistema operativo
load_dotenv(override=True)

_PBKDF2_ITERATIONS = 100_000
_SALT_BYTES = 16

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

if not SECRET_KEY:
    raise RuntimeError(
        "❌ ERROR CRÍTICO DE CONFIGURACIÓN: La variable 'SECRET_KEY' no está definida en el archivo .env."
    )

if not ACCESS_TOKEN_EXPIRE_MINUTES:
    raise RuntimeError(
        "❌ ERROR CRÍTICO DE CONFIGURACIÓN: La variable 'ACCESS_TOKEN_EXPIRE_MINUTES' no está definida en el archivo .env."
    )

ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES)


# ── Hashing de contraseñas (PBKDF2-HMAC-SHA256) ─────────────────────────────
def hash_password(password: str) -> str:
    """Hashea la contraseña con PBKDF2-HMAC-SHA256 y una sal aleatoria."""
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{_PBKDF2_ITERATIONS}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica la contraseña comparando el hash almacenado con el hash derivado de la ingresada."""
    try:
        iterations, salt_hex, dk_hex = hashed_password.split("$")
        salt = binascii.unhexlify(salt_hex)
        dk_stored = binascii.unhexlify(dk_hex)
        dk_new = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(dk_new, dk_stored)
    except Exception:
        return False


# ── Token de recuperación de contraseña ─────────────────────────────────────
# El token real (largo, aleatorio, imposible de adivinar) es lo único que se
# envía por correo al usuario y lo que va en el enlace. En la base de datos
# NUNCA se guarda el token en texto plano: solo se guarda su hash SHA-256.
# Así, aunque alguien tuviera acceso de lectura a la base de datos, no podría
# reconstruir el enlace de recuperación de ningún usuario.
RESET_TOKEN_EXPIRE_MINUTES = 30


def generar_token_reset() -> str:
    """Genera un token de recuperación aleatorio y criptográficamente seguro."""
    return secrets.token_urlsafe(32)


def hash_token_reset(token: str) -> str:
    """Hashea el token con SHA-256 para guardarlo en la base de datos (nunca el token real)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── Tokens JWT ───────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un JWT firmado que incluye fecha de expiración (por defecto 30 min)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_token_from_request(request: Request) -> str:
    """Extrae el token Bearer del header Authorization."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer inválido o ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_header[7:]  # Quita "Bearer " y retorna solo el token


def get_current_user(request: Request) -> dict:
    """Decodifica el token JWT desde el header Authorization y devuelve el usuario asociado."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = get_token_from_request(request)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    con = get_db_connection()
    with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id, nombre, correo, rol FROM usuarios WHERE correo = %s",
            (correo,),
        )
        usuario = cursor.fetchone()

    if usuario is None:
        raise credentials_exception
    return dict(usuario)


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Punto de extensión por si en el futuro se agrega columna 'activo' a usuarios."""
    return current_user


def requiere_rol(*roles_permitidos: str):
    """Dependencia de autorización: exige que el usuario autenticado tenga uno de los roles indicados."""

    def verificador(current_user: dict = Depends(get_current_active_user)) -> dict:
        if current_user.get("rol") not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción",
            )
        return current_user

    return verificador
