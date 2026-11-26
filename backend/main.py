from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from routes.routes import (
    routes_pueblos,
    routes_usuarios,
    routes_atracciones,
    routes_itinerario,
    routes_gastronomia,
    routes_tradiciones,
    routes_resenas,
    routes_auth,
    routes_contacto,
    routes_convenio,
    routes_negocio,
)

# Carga de variables de entorno
load_dotenv(override=True)

app = FastAPI(
    title="RinconesCol",
    description="APP WEB donde encontraras turismo y gastronomia",
    version="1.0.0",
)

# Incluir las rutas
app.include_router(routes_auth)
app.include_router(routes_pueblos)
app.include_router(routes_usuarios)
app.include_router(routes_atracciones)
app.include_router(routes_itinerario)
app.include_router(routes_gastronomia)
app.include_router(routes_tradiciones)
app.include_router(routes_resenas)
app.include_router(routes_contacto)
app.include_router(routes_convenio)
app.include_router(routes_negocio)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# =========================================================================
# CONFIGURACIÓN PERSONALIZADA DE SWAGGER: Esquema Bearer (botón Authorize)
# =========================================================================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="RinconesCol",
        version="1.0.0",
        description="APP WEB donde encontraras turismo y gastronomia",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Pega aquí tu token JWT con el formato: Bearer <token>",
        }
    }

    # Aplica el candado solo a las rutas protegidas (POST, PUT, DELETE), no a /auth
    for path, path_item in openapi_schema.get("paths", {}).items():
        if "/auth" in path:
            continue
        for method, operation in path_item.items():
            if method in ["post", "put", "patch", "delete"]:
                if "security" not in operation:
                    operation["security"] = [{"Bearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="DEFAULT API",
    tags=["APP"],
)
def message():
    """Home API"""
    return HTMLResponse("<h1> Bienvenido a RinconesCol </h1>")
