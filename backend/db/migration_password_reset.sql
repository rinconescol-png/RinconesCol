-- ============================================================================
-- MIGRACIÓN: Recuperación de contraseña
--
-- Qué hace:
-- 1) Crea la tabla "password_reset_tokens": guarda SOLO el hash SHA-256 del
--    token de recuperación (nunca el token en texto plano), con fecha de
--    expiración y fecha de uso (para invalidarlo tras usarse una vez).
--
-- No modifica ninguna tabla existente ni borra datos.
--
-- Ejecutar UNA sola vez:
--   psql -h 127.0.0.1 -U postgres -d RinconesCol -f migration_password_reset.sql
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id             SERIAL PRIMARY KEY,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token_hash     VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hex del token real
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_expira   TIMESTAMP NOT NULL,
    usado          BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_password_reset_usuario ON password_reset_tokens(usuario_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_token_hash ON password_reset_tokens(token_hash);

COMMIT;
