from fastapi import APIRouter, Depends, HTTPException, status
from models.pueblo_model import Pueblo
from models.user_model import Usuario, PerfilUpdate
from models.atraccion_model import Atraccion
from models.itinerario_model import ItinerarioItem
from models.gastronomia_model import Gastronomia
from models.tradicion_model import Tradicion
from models.resena_model import Resena
from models.auth_model import UsuarioLogin, SolicitudRecuperacion, RestablecerContrasena
from models.contacto_model import MensajeContacto
from models.convenio_model import SolicitudConvenio, AprobarSolicitud
from models.negocio_model import NegocioUpdate, NegocioFotoCreate, NegocioItem
from services.pueblo_service import PuebloService
from services.usuario_service import UsuarioService
from services.atraccion_service import AtraccionService
from services.itinerario_service import ItinerarioService
from services.gastronomia_service import GastronomiaService
from services.tradicion_service import TradicionService
from services.resena_service import ResenaService
from services.auth_service import AuthService
from services.contacto_service import ContactoService
from services.convenio_service import ConvenioService
from services.negocio_service import NegocioService
from security.security import get_current_active_user, requiere_rol

# ── Routers ───────────────────────────────────────────────────────────────────
routes_pueblos     = APIRouter(prefix="/pueblos",     tags=["Pueblos"])
routes_usuarios    = APIRouter(prefix="/usuarios",    tags=["Usuarios"])
routes_atracciones = APIRouter(prefix="/atracciones", tags=["Atracciones"])
routes_itinerario  = APIRouter(prefix="/itinerario",  tags=["Itinerario"])
routes_gastronomia = APIRouter(prefix="/gastronomia", tags=["Gastronomia"])
routes_tradiciones = APIRouter(prefix="/tradiciones", tags=["Tradiciones"])
routes_resenas     = APIRouter(prefix="/resenas",     tags=["Resenas"])
routes_auth        = APIRouter(prefix="/auth",        tags=["Auth"])
routes_contacto    = APIRouter(prefix="/contacto",     tags=["Contacto"])
routes_convenio    = APIRouter(prefix="/convenio",     tags=["Convenio"])
routes_negocio     = APIRouter(prefix="/negocio",      tags=["Negocio (Socio)"])

# ── Services ──────────────────────────────────────────────────────────────────
pueblo_service     = PuebloService()
usuario_service    = UsuarioService()
atraccion_service  = AtraccionService()
itinerario_service = ItinerarioService()
gastronomia_service = GastronomiaService()
tradicion_service  = TradicionService()
resena_service     = ResenaService()
auth_service       = AuthService()
contacto_service   = ContactoService()
convenio_service   = ConvenioService()
negocio_service    = NegocioService()

# ══════════════════════════════════════════════════════════════════════════════
# PUEBLOS  (lectura pública, escritura SOLO admin)
# ══════════════════════════════════════════════════════════════════════════════
@routes_pueblos.get("/")
async def get_pueblos():
    return await pueblo_service.get_pueblos()

@routes_pueblos.get("/{pueblo_id}")
async def get_pueblo(pueblo_id: int):
    return await pueblo_service.get_pueblo_by_id(pueblo_id)

@routes_pueblos.post("/")
async def create_pueblo(pueblo: Pueblo, current_user: dict = Depends(requiere_rol("admin"))):
    return await pueblo_service.create_pueblo(pueblo)

@routes_pueblos.put("/{pueblo_id}")
async def update_pueblo(pueblo_id: int, pueblo: Pueblo, current_user: dict = Depends(requiere_rol("admin"))):
    return await pueblo_service.update_pueblo(pueblo_id, pueblo)

@routes_pueblos.delete("/{pueblo_id}")
async def delete_pueblo(pueblo_id: int, current_user: dict = Depends(requiere_rol("admin"))):
    return await pueblo_service.delete_pueblo(pueblo_id)

# ══════════════════════════════════════════════════════════════════════════════
# USUARIOS  (listar/crear/editar/borrar cuentas es SOLO admin)
# ══════════════════════════════════════════════════════════════════════════════
@routes_usuarios.get("/")
async def get_usuarios(current_user: dict = Depends(requiere_rol("admin"))):
    return await usuario_service.get_usuarios()

@routes_usuarios.get("/{usuario_id}")
async def get_usuario(usuario_id: int, current_user: dict = Depends(get_current_active_user)):
    # Un usuario normal puede ver su propio perfil; un admin puede ver cualquiera.
    if current_user.get("rol") != "admin" and current_user.get("id") != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver este usuario")
    return await usuario_service.get_usuario_by_id(usuario_id)

@routes_usuarios.get("/perfil/me")
async def get_mi_perfil(current_user: dict = Depends(get_current_active_user)):
    # Cualquier usuario autenticado (admin, visitante o socio) puede ver SU
    # PROPIO perfil, con foto incluida. El id sale del token, nunca de la URL.
    return await usuario_service.get_mi_perfil(current_user["id"])

@routes_usuarios.put("/perfil/me")
async def actualizar_mi_perfil(datos: PerfilUpdate, current_user: dict = Depends(get_current_active_user)):
    # Igual que arriba: cualquier usuario autenticado puede editar SU PROPIO
    # nombre y/o foto de perfil, nunca el de otra cuenta.
    return await usuario_service.actualizar_mi_perfil(current_user["id"], datos)

@routes_usuarios.post("/")
async def create_usuario(usuario: Usuario, current_user: dict = Depends(requiere_rol("admin"))):
    # Vía admin sí se puede asignar rol="admin" a otra cuenta (a diferencia de /auth/register).
    return await usuario_service.create_usuario(usuario)

@routes_usuarios.put("/{usuario_id}")
async def update_usuario(usuario_id: int, usuario: Usuario, current_user: dict = Depends(requiere_rol("admin"))):
    return await usuario_service.update_usuario(usuario_id, usuario)

@routes_usuarios.delete("/{usuario_id}")
async def delete_usuario(usuario_id: int, current_user: dict = Depends(requiere_rol("admin"))):
    return await usuario_service.delete_usuario(usuario_id)

# ══════════════════════════════════════════════════════════════════════════════
# ATRACCIONES  (lectura pública, escritura SOLO admin)
# ══════════════════════════════════════════════════════════════════════════════
@routes_atracciones.get("/")
async def get_atracciones():
    return await atraccion_service.get_atracciones()

@routes_atracciones.get("/pueblo/{pueblo_id}")
async def get_atracciones_por_pueblo(pueblo_id: int):
    # Usada por atracciones.html: todas las atracciones de un pueblo puntual.
    return await atraccion_service.get_atracciones_por_pueblo(pueblo_id)

@routes_atracciones.get("/{atraccion_id}")
async def get_atraccion(atraccion_id: int):
    return await atraccion_service.get_atraccion_by_id(atraccion_id)

@routes_atracciones.post("/")
async def create_atraccion(atraccion: Atraccion, current_user: dict = Depends(requiere_rol("admin"))):
    return await atraccion_service.create_atraccion(atraccion)

@routes_atracciones.put("/{atraccion_id}")
async def update_atraccion(atraccion_id: int, atraccion: Atraccion, current_user: dict = Depends(requiere_rol("admin"))):
    return await atraccion_service.update_atraccion(atraccion_id, atraccion)

@routes_atracciones.delete("/{atraccion_id}")
async def delete_atraccion(atraccion_id: int, current_user: dict = Depends(requiere_rol("admin"))):
    return await atraccion_service.delete_atraccion(atraccion_id)

# ══════════════════════════════════════════════════════════════════════════════
# ITINERARIO  (itinerario sugerido de 1 día por pueblo; lectura pública,
#              escritura SOLO admin)
# ══════════════════════════════════════════════════════════════════════════════
@routes_itinerario.get("/")
async def get_itinerario():
    return await itinerario_service.get_itinerario()

@routes_itinerario.get("/pueblo/{pueblo_id}")
async def get_itinerario_por_pueblo(pueblo_id: int):
    # Usada por atracciones.html: devuelve { manana: [...], tarde: [...], noche: [...] }
    return await itinerario_service.get_itinerario_por_pueblo(pueblo_id)

@routes_itinerario.get("/{item_id}")
async def get_itinerario_item(item_id: int):
    return await itinerario_service.get_itinerario_by_id(item_id)

@routes_itinerario.post("/")
async def create_itinerario_item(item: ItinerarioItem, current_user: dict = Depends(requiere_rol("admin"))):
    return await itinerario_service.create_itinerario_item(item)

@routes_itinerario.put("/{item_id}")
async def update_itinerario_item(item_id: int, item: ItinerarioItem, current_user: dict = Depends(requiere_rol("admin"))):
    return await itinerario_service.update_itinerario_item(item_id, item)

@routes_itinerario.delete("/{item_id}")
async def delete_itinerario_item(item_id: int, current_user: dict = Depends(requiere_rol("admin"))):
    return await itinerario_service.delete_itinerario_item(item_id)

# ══════════════════════════════════════════════════════════════════════════════
# GASTRONOMIA  (lectura pública, escritura SOLO admin)
# ══════════════════════════════════════════════════════════════════════════════
@routes_gastronomia.get("/")
async def get_gastronomias():
    return await gastronomia_service.get_gastronomias()

@routes_gastronomia.get("/{item_id}")
async def get_gastronomia(item_id: int):
    return await gastronomia_service.get_gastronomia_by_id(item_id)

@routes_gastronomia.post("/")
async def create_gastronomia(item: Gastronomia, current_user: dict = Depends(requiere_rol("admin"))):
    return await gastronomia_service.create_gastronomia(item)

@routes_gastronomia.put("/{item_id}")
async def update_gastronomia(item_id: int, item: Gastronomia, current_user: dict = Depends(requiere_rol("admin"))):
    return await gastronomia_service.update_gastronomia(item_id, item)

@routes_gastronomia.delete("/{item_id}")
async def delete_gastronomia(item_id: int, current_user: dict = Depends(requiere_rol("admin"))):
    return await gastronomia_service.delete_gastronomia(item_id)

# ══════════════════════════════════════════════════════════════════════════════
# TRADICIONES  (lectura pública, escritura SOLO admin)
# ══════════════════════════════════════════════════════════════════════════════
@routes_tradiciones.get("/")
async def get_tradiciones():
    return await tradicion_service.get_tradiciones()

@routes_tradiciones.get("/{tradicion_id}")
async def get_tradicion(tradicion_id: int):
    return await tradicion_service.get_tradicion_by_id(tradicion_id)

@routes_tradiciones.post("/")
async def create_tradicion(tradicion: Tradicion, current_user: dict = Depends(requiere_rol("admin"))):
    return await tradicion_service.create_tradicion(tradicion)

@routes_tradiciones.put("/{tradicion_id}")
async def update_tradicion(tradicion_id: int, tradicion: Tradicion, current_user: dict = Depends(requiere_rol("admin"))):
    return await tradicion_service.update_tradicion(tradicion_id, tradicion)

@routes_tradiciones.delete("/{tradicion_id}")
async def delete_tradicion(tradicion_id: int, current_user: dict = Depends(requiere_rol("admin"))):
    return await tradicion_service.delete_tradicion(tradicion_id)

# ══════════════════════════════════════════════════════════════════════════════
# RESEÑAS  (usuarios autenticados pueden crear y editar las propias;
#           solo ADMIN puede eliminar cualquier reseña).
# ══════════════════════════════════════════════════════════════════════════════
@routes_resenas.get("/")
async def get_resenas(pueblo_id: int | None = None):
    # Sin pueblo_id devuelve todas las reseñas; con pueblo_id devuelve solo
    # las de ese destino (esto es lo que usa destino.html para cada pueblo).
    return await resena_service.get_resenas(pueblo_id)

@routes_resenas.get("/limite/{pueblo_id}")
async def get_estado_limite_resenas(
    pueblo_id: int,
    current_user: dict = Depends(get_current_active_user),
):
    # El conteo se calcula con el usuario autenticado, no con un ID enviado
    # libremente por el navegador.
    return await resena_service.get_estado_limite(current_user["id"], pueblo_id)

@routes_resenas.get("/{resena_id}")
async def get_resena(resena_id: int):
    return await resena_service.get_resena_by_id(resena_id)

@routes_resenas.post("/")
async def create_resena(resena: Resena, current_user: dict = Depends(get_current_active_user)):
    # El usuario_id SIEMPRE se toma del token, nunca de lo que envíe el cliente
    # en el cuerpo de la petición (evita que alguien publique reseñas a nombre
    # de otro usuario).
    resena.usuario_id = current_user["id"]
    return await resena_service.create_resena(resena)

@routes_resenas.put("/{resena_id}")
async def update_resena(resena_id: int, resena: Resena, current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") != "admin":
        propietario_id = await resena_service.obtener_propietario(resena_id)
        if propietario_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reseña no encontrada")
        if propietario_id != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes editar la reseña de otro usuario")
        resena.usuario_id = current_user["id"]
    return await resena_service.update_resena(resena_id, resena)

@routes_resenas.delete("/{resena_id}")
async def delete_resena(resena_id: int, current_user: dict = Depends(requiere_rol("admin"))):
    # Solo ADMIN puede eliminar reseñas. La autorización se valida en el
    # backend a partir del usuario y rol asociados al token JWT.
    return await resena_service.delete_resena(resena_id)

# ══════════════════════════════════════════════════════════════════════════════
# AUTH (Registro / Login con JWT)
# ══════════════════════════════════════════════════════════════════════════════
@routes_auth.post("/register")
async def registrar(usuario: Usuario):
    return await auth_service.registrar_usuario(usuario)

@routes_auth.post("/login")
async def login(credenciales: UsuarioLogin):
    return await auth_service.login(credenciales)

@routes_auth.post("/forgot-password")
async def forgot_password(datos: SolicitudRecuperacion):
    # Siempre responde igual exista o no el correo (ver AuthService); por
    # eso no lleva protección de rol, cualquiera puede pedir el enlace de
    # SU propio correo.
    return await auth_service.solicitar_recuperacion(datos)

@routes_auth.post("/reset-password")
async def reset_password(datos: RestablecerContrasena):
    return await auth_service.restablecer_contrasena(datos)

# ══════════════════════════════════════════════════════════════════════════════
# CONTACTO  (cualquiera puede enviar un mensaje; solo admin puede listarlos)
# ══════════════════════════════════════════════════════════════════════════════
@routes_contacto.post("/")
async def crear_mensaje_contacto(mensaje: MensajeContacto):
    return await contacto_service.crear_mensaje(mensaje)

@routes_contacto.get("/")
async def get_mensajes_contacto(current_user: dict = Depends(requiere_rol("admin"))):
    return await contacto_service.get_mensajes()

# ══════════════════════════════════════════════════════════════════════════════
# CONVENIO  (cualquiera puede solicitar; solo admin puede listar solicitudes)
# ══════════════════════════════════════════════════════════════════════════════
@routes_convenio.post("/")
async def crear_solicitud_convenio(solicitud: SolicitudConvenio):
    return await convenio_service.crear_solicitud(solicitud)

@routes_convenio.get("/")
async def get_solicitudes_convenio(current_user: dict = Depends(requiere_rol("admin"))):
    return await convenio_service.get_solicitudes()

# Aprobar/rechazar es la acción "manual" del equipo de RinconesCol: el admin
# revisa la solicitud (GET /convenio/) y, si decide aprobarla, confirma a qué
# pueblo real y bajo qué categoría queda el negocio. Esto crea (o sube de rol
# a) el usuario "socio" y su fila en "negocios".
@routes_convenio.post("/{solicitud_id}/aprobar")
async def aprobar_solicitud_convenio(solicitud_id: int, datos: AprobarSolicitud, current_user: dict = Depends(requiere_rol("admin"))):
    return await convenio_service.aprobar_solicitud(solicitud_id, datos)

@routes_convenio.post("/{solicitud_id}/rechazar")
async def rechazar_solicitud_convenio(solicitud_id: int, current_user: dict = Depends(requiere_rol("admin"))):
    return await convenio_service.rechazar_solicitud(solicitud_id)

# ══════════════════════════════════════════════════════════════════════════════
# NEGOCIO (panel del Socio)
#
# Ningún endpoint de aquí abajo recibe un "negocio_id" en la URL: el negocio
# siempre se resuelve a partir del usuario autenticado (current_user["id"]).
# Así, a nivel de endpoint, un socio JAMÁS puede editar el negocio de otro,
# ni ver ni tocar pueblos o contenido general de la plataforma.
# ══════════════════════════════════════════════════════════════════════════════
@routes_negocio.get("/mi-negocio")
async def get_mi_negocio(current_user: dict = Depends(requiere_rol("socio"))):
    return await negocio_service.get_mi_negocio(current_user["id"])

@routes_negocio.put("/mi-negocio")
async def actualizar_mi_negocio(data: NegocioUpdate, current_user: dict = Depends(requiere_rol("socio"))):
    return await negocio_service.actualizar_mi_negocio(current_user["id"], data)

@routes_negocio.post("/mi-negocio/fotos")
async def agregar_foto_negocio(data: NegocioFotoCreate, current_user: dict = Depends(requiere_rol("socio"))):
    return await negocio_service.agregar_foto(current_user["id"], data)

@routes_negocio.delete("/mi-negocio/fotos/{foto_id}")
async def eliminar_foto_negocio(foto_id: int, current_user: dict = Depends(requiere_rol("socio"))):
    return await negocio_service.eliminar_foto(current_user["id"], foto_id)

@routes_negocio.post("/mi-negocio/items")
async def crear_item_negocio(data: NegocioItem, current_user: dict = Depends(requiere_rol("socio"))):
    return await negocio_service.crear_item(current_user["id"], data)

@routes_negocio.put("/mi-negocio/items/{item_id}")
async def actualizar_item_negocio(item_id: int, data: NegocioItem, current_user: dict = Depends(requiere_rol("socio"))):
    return await negocio_service.actualizar_item(current_user["id"], item_id, data)

@routes_negocio.delete("/mi-negocio/items/{item_id}")
async def eliminar_item_negocio(item_id: int, current_user: dict = Depends(requiere_rol("socio"))):
    return await negocio_service.eliminar_item(current_user["id"], item_id)

# ── Endpoints públicos (sin login): para que destino.html y la página de
#    detalle de negocio muestren los negocios aliados de cada pueblo ────────
@routes_negocio.get("/pueblo/{pueblo_id}")
async def get_negocios_por_pueblo(pueblo_id: int):
    return await negocio_service.listar_por_pueblo(pueblo_id)

@routes_negocio.get("/publico/{negocio_id}")
async def get_negocio_publico(negocio_id: int):
    return await negocio_service.get_negocio_publico(negocio_id)
