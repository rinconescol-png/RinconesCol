# RinconesCol — Frontend conectado al backend real

## Qué se cambió

**Frontend (NO se tocó ningún .html/.css):** solo se reescribieron
`js/auth.js` y `js/data.js` para que hablen con la API en vez de usar
`localStorage`/datos fijos. Las mismas funciones/variables que ya usaban
tus páginas (`iniciarSesion`, `registrarUsuario`, `usuarioActual`,
`DESTINOS`, `GASTRONOMIA`, etc.) siguen existiendo con el mismo
comportamiento — por eso ninguna página HTML necesitó cambios.

**Backend / Base de datos:** se adaptó el esquema para soportar todo lo
que el frontend necesita mostrar:

- `pueblos`: nuevas columnas `slug`, `region`, `sello`, `resumen`, `clima`,
  `ubicacion`, `alcalde`.
- Tablas nuevas: `pueblo_actividades`, `pueblo_platos_tipicos`,
  `pueblo_restaurantes` (lo que destino.html llama "actividades",
  "platosTipicos" y "dondeComer").
- `gastronomia`: nueva columna `region`.
- `services/pueblo_service.py` y `services/gastronomia_service.py` ahora
  arman la respuesta con exactamente la forma que el frontend espera
  (incluye alias `imagen`, `platosTipicos`, `dondeComer`, y usa el `slug`
  como `id` para que los enlaces `destino.html?id=gachala` sigan
  funcionando igual).
- `models/pueblo_model.py` y `models/gastronomia_model.py` actualizados
  con los campos nuevos.
- `db/conexion.py`: se agregó `client_encoding="UTF8"` en la conexión de
  psycopg2. Esto es lo que normalmente causa el `UnicodeDecodeError` en
  Windows (el driver toma el codepage local en vez de UTF-8 al leer
  tildes/ñ desde PostgreSQL).
- `db/migration_frontend.sql`: migración que agrega las columnas/tablas
  y siembra los 6 pueblos y los 6 platos de gastronomía que ya existían
  como contenido estático en `js/data.js`, ahora como datos reales en la
  base de datos.

## Pasos para levantar todo

1. **Aplica la migración** contra tu base ya existente
   (`turismo_cultural_colombia`):

   ```bash
   psql -h 127.0.0.1 -U postgres -d turismo_cultural_colombia -f db/migration_frontend.sql
   ```

2. **Instala dependencias y corre el backend** (usa tu mismo `.env`):

   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

   Por defecto queda en `http://127.0.0.1:8000`.

3. **Abre el frontend.** `js/auth.js` y `js/data.js` apuntan a
   `http://127.0.0.1:8000` mediante la constante `API_BASE_URL` al inicio
   de cada archivo. Si tu backend corre en otra URL/puerto, cambia esa
   constante en ambos archivos (son las únicas líneas que necesitarías
   tocar).

4. Prueba: registro (`registro.html`), login (`login.html`), y navega a
   `destinos.html` / `destino.html` / `gastronomia.html` / `home.html`:
   ahora todo viene de PostgreSQL. Si el backend no está corriendo, esas
   páginas usan datos de respaldo embebidos para no quedar en blanco.

## Administrador vs. usuario normal

- **Registro público (`registro.html` → `POST /auth/register`):** siempre
  crea el usuario con rol `"visitante"`, sin importar qué envíe el cliente.
  Antes el modelo confiaba en un campo `rol` que en teoría cualquiera podía
  mandar en el JSON del registro — eso ya no es posible: el backend lo
  ignora y fuerza `"visitante"`.
- **Crear un administrador:** no se hace por el registro público. Corre:

  ```bash
  cd RinconesCol
  python scripts/crear_admin.py
  ```

  Te pide nombre, correo y contraseña, y crea (o asciende, si el correo ya
  existe) una cuenta con rol `"admin"`, usando el mismo hash PBKDF2 que usa
  el resto del sistema — por lo tanto ese admin puede iniciar sesión
  normalmente desde `login.html`.
- **Rutas protegidas por rol:** crear/editar/borrar pueblos, atracciones,
  gastronomía, tradiciones y usuarios ahora requieren rol `admin`
  (`Depends(requiere_rol("admin"))`). Antes cualquier usuario autenticado
  (incluso "visitante") podía hacerlo con solo tener un token válido — era
  un hueco de seguridad, ya corregido.
- **Reseñas:** cualquier usuario logueado puede crear las suyas (el
  `usuario_id` se toma del token, nunca de lo que envíe el cliente, para
  que nadie pueda publicar a nombre de otro). Editar/borrar una reseña
  ajena solo lo puede hacer un admin.
- **Bug corregido:** cuando un admin crea o edita un usuario desde
  `POST/PUT /usuarios`, la contraseña ahora se guarda hasheada con
  PBKDF2 (antes se guardaba en texto plano y ese usuario no habría podido
  iniciar sesión).

## Nota sobre `iniciarSesion`/`registrarUsuario`

Ambas funciones ahora hacen una petición **síncrona** (XHR con
`async=false`) al backend, para no tener que convertir el HTML a
async/await. Es una técnica antigua pero funcional; si más adelante
migras el frontend a `fetch`/`async`, se puede modernizar sin problema.

---

## Rol "Socio" para negocios (nuevo)

Permite que un negocio (Restaurante, Hotel/posada, Cafetería, Experiencia
turística o Artesanías/emprendimiento) que ya solicitó convenio y fue
aprobado manualmente, pueda iniciar sesión como **Socio** y editar SU
propio negocio (fotos, descripción, y los platos/productos/servicios que
ofrece), el cual queda visible dentro de su pueblo como una atracción más.

### 1) Aplica la nueva migración

```bash
psql -h 127.0.0.1 -U postgres -d turismo_cultural_colombia -f db/migration_socios.sql
```

Esto agrega:
- `socio` como rol válido en `usuarios`.
- Columnas `contrasena`, `estado` y `usuario_id` en `solicitudes_convenio`
  (el formulario que ya existía en `login-convenio.html`).
- Tablas nuevas `negocios`, `negocio_fotos` y `negocio_items`.

### 2) Flujo completo

1. Un visitante logueado llena `login-convenio.html` (ahora pide también
   una contraseña) → queda guardado en `solicitudes_convenio` con
   `estado = 'pendiente'`.
2. El equipo de RinconesCol revisa las solicitudes con
   `GET /convenio/` (requiere rol `admin`, se puede hacer desde `/docs`).
3. Para aprobar manualmente, se llama:

   ```
   POST /convenio/{solicitud_id}/aprobar
   Body: { "pueblo_id": 3, "categoria": "restaurante" }
   ```
   (`categoria` es una de: `restaurante`, `hotel`, `cafeteria`,
   `experiencia`, `artesania`). Esto crea (o sube de rol) al usuario con
   `rol = "socio"` y crea su fila en `negocios`, vinculada al pueblo real
   de la base de datos y a la contraseña que el negocio puso en el
   formulario.
4. Para rechazar: `POST /convenio/{solicitud_id}/rechazar`.
5. El negocio ya puede entrar por `login.html`, seleccionando el botón
   **"Socio"**, con el correo y la contraseña del formulario.
6. Al loguearse como socio, cae en `panel-socio.html`, donde solo puede
   editar: descripción, foto de portada, galería de fotos, y sus
   platos/productos/servicios (`negocio_items`). No puede tocar pueblos,
   ni el contenido de otros negocios — todos los endpoints de
   `/negocio/mi-negocio/...` resuelven el negocio a partir del usuario del
   token JWT, nunca de un id que venga en la URL.
7. Su negocio aparece automáticamente dentro de `atracciones.html` de su
   pueblo: `GET /atracciones/pueblo/{id}` ahora también incluye los
   negocios de socios aprobados con la misma forma que las atracciones
   normales (nombre, tipo, descripción, foto), así que no hizo falta tocar
   `atracciones.html` ni `atracciones.js`.

### 3) Archivos nuevos/afectados

**Backend:** `db/migration_socios.sql`, `models/negocio_model.py`,
`services/negocio_service.py`, cambios en `models/convenio_model.py`,
`models/user_model.py`, `services/convenio_service.py`,
`services/atraccion_service.py`, `services/email_service.py`,
`routes/routes.py`, `main.py`.

**Frontend:** `panel-socio.html` (nuevo), `css/panel-socio.css` (nuevo),
`js/negocio-panel.js` (nuevo), y cambios en `login.html` (selector
Turista/Socio), `css/login.css`, `login-convenio.html` (campo de
contraseña) y `js/auth.js` (funciones para hablar con
`/negocio/mi-negocio` + enlace automático "Mi negocio" en la navbar
cuando el usuario logueado es socio).


---

## Mejoras de reseñas y detalle de destinos (noviembre de 2026)

Se actualizaron los archivos existentes para incluir:

- `backend/routes/routes.py`: endpoint autenticado `GET /resenas/limite/{pueblo_id}`; el `usuario_id` de una reseña nueva se toma del token, y `DELETE /resenas/{id}` exige rol `admin`.
- `backend/services/resena_service.py`: límite de tres reseñas por usuario y pueblo comprobado en PostgreSQL dentro de una transacción; el borrado es físico (`DELETE`), así que las eliminadas por ADMIN ya no cuentan. No se requieren columnas ni tablas nuevas.
- `frontend/destino.html` y `frontend/css/destino.css`: orden nuevo de secciones, títulos y descripciones, tarjetas e identidad visual adaptable a móvil/tablet/escritorio. Atracciones e itinerarios se obtienen de los endpoints existentes; emprendimientos mantienen el enlace a su detalle.
- `frontend/js/resenas.js`: formulario bloqueado al alcanzar el máximo, confirmación antes del borrado ADMIN y expansión/contracción de reseñas sin recargar la página.

### Probar los cambios

Desde la carpeta `RinconesCol/backend` (con PostgreSQL encendido y el `.env` existente configurado):

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Abre el frontend con Live Server o el servidor estático que ya utilizas y entra a `destino.html?id=<id-del-pueblo>`. Prueba con un usuario visitante: publica tres reseñas para el mismo pueblo y verifica que la cuarta se rechace con HTTP 409 y que se muestre el aviso. Prueba con un usuario ADMIN: elimina una reseña, confirma el cuadro de diálogo y verifica que desaparezca; después comprueba que el usuario propietario vuelve a tener un cupo disponible. Para revisar el permiso del backend, intenta `DELETE /resenas/{id}` desde `/docs` con un token de visitante (debe responder 403) y luego con un token ADMIN (debe responder 200).

**Base de datos:** no se modifica el esquema ni se necesita una migración. El contador utiliza las filas existentes en `resenas`; el borrado físico hace que la reseña deje de contabilizarse.
