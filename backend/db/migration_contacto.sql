-- ============================================================================
-- MIGRACIÓN: crea la tabla donde queda guardada la información que los
-- usuarios envían desde el formulario de "Contáctanos" del frontend.
--
-- Ejecutar UNA sola vez contra la base ya existente, por ejemplo:
--   psql -h 127.0.0.1 -U postgres -d RinconesCol -f migration_contacto.sql
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS mensajes_contacto (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(150) NOT NULL,
    correo        VARCHAR(150) NOT NULL,
    mensaje       TEXT NOT NULL,
    fecha_envio   TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMIT;
