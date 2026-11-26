-- ============================================================================
-- MIGRACIÓN: crea la tabla donde queda guardada la información que los
-- negocios envían desde el formulario "Solicitar convenio"
-- (frontend/login-convenio.html).
--
-- Ejecutar UNA sola vez contra la base ya existente, por ejemplo:
--   psql -h 127.0.0.1 -U postgres -d RinconesCol -f migration_convenio.sql
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS solicitudes_convenio (
    id             SERIAL PRIMARY KEY,
    nombre_negocio VARCHAR(150) NOT NULL,
    propietario    VARCHAR(150) NOT NULL,
    tipo_negocio   VARCHAR(100) NOT NULL,
    pueblo         VARCHAR(150) NOT NULL,
    correo         VARCHAR(150) NOT NULL,
    telefono       VARCHAR(30)  NOT NULL,
    mensaje        TEXT,
    fecha_envio    TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMIT;
