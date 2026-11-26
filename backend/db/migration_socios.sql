-- ============================================================================
-- MIGRACIÓN: rol "Socio" para negocios (Restaurantes, Hoteles/posadas,
-- Cafeterías, Experiencias turísticas, Artesanías/emprendimientos).
--
-- Qué hace:
-- 1) Amplía "solicitudes_convenio" (el formulario que ya existe) con:
--    contraseña (para que el negocio pueda loguearse luego), estado de la
--    solicitud (pendiente/aprobada/rechazada) y el usuario_id que queda
--    vinculado una vez se aprueba.
-- 2) Crea la tabla "negocios": el negocio ya aprobado, vinculado a un
--    usuario (el socio) y a un pueblo, con su categoría.
-- 3) Crea "negocio_fotos" (galería) y "negocio_items" (platos, productos o
--    servicios que ofrece el negocio).
-- 4) Quita el CHECK viejo del rol en "usuarios" (si existía) y agrega uno
--    nuevo que incluye "socio".
--
-- Ejecutar UNA sola vez, después de migration_convenio.sql:
--   psql -h 127.0.0.1 -U postgres -d turismo_cultural_colombia -f migration_socios.sql
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1) Rol "socio" habilitado en "usuarios"
-- ----------------------------------------------------------------------------
ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_rol_check;
ALTER TABLE usuarios ADD CONSTRAINT usuarios_rol_check
    CHECK (rol IN ('admin', 'visitante', 'socio'));

-- ----------------------------------------------------------------------------
-- 2) Ampliar "solicitudes_convenio"
-- ----------------------------------------------------------------------------
ALTER TABLE solicitudes_convenio
    ADD COLUMN IF NOT EXISTS contrasena VARCHAR(255),
    ADD COLUMN IF NOT EXISTS estado     VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE solicitudes_convenio DROP CONSTRAINT IF EXISTS solicitudes_convenio_estado_check;
ALTER TABLE solicitudes_convenio ADD CONSTRAINT solicitudes_convenio_estado_check
    CHECK (estado IN ('pendiente', 'aprobado', 'rechazado'));

-- ----------------------------------------------------------------------------
-- 3) Tabla "negocios": el negocio ya aprobado y visible dentro de su pueblo
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS negocios (
    id             SERIAL PRIMARY KEY,
    usuario_id     INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE,
    solicitud_id   INTEGER REFERENCES solicitudes_convenio(id) ON DELETE SET NULL,
    pueblo_id      INTEGER NOT NULL REFERENCES pueblos(id) ON DELETE CASCADE,
    nombre         VARCHAR(150) NOT NULL,
    categoria      VARCHAR(30)  NOT NULL
                   CHECK (categoria IN ('restaurante', 'hotel', 'cafeteria', 'experiencia', 'artesania')),
    descripcion    TEXT,
    foto           TEXT,
    correo         VARCHAR(150),
    telefono       VARCHAR(30),
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_negocios_pueblo ON negocios(pueblo_id);

-- ----------------------------------------------------------------------------
-- 4) Galería de fotos del negocio
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS negocio_fotos (
    id          SERIAL PRIMARY KEY,
    negocio_id  INTEGER NOT NULL REFERENCES negocios(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    orden       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_negocio_fotos_negocio ON negocio_fotos(negocio_id);

-- ----------------------------------------------------------------------------
-- 5) Platos / productos / servicios que ofrece el negocio
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS negocio_items (
    id          SERIAL PRIMARY KEY,
    negocio_id  INTEGER NOT NULL REFERENCES negocios(id) ON DELETE CASCADE,
    nombre      VARCHAR(150) NOT NULL,
    descripcion TEXT,
    precio      NUMERIC(10,2),
    foto        TEXT,
    orden       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_negocio_items_negocio ON negocio_items(negocio_id);

COMMIT;
