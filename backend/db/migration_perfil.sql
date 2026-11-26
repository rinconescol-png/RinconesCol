-- ============================================================================
-- MIGRACIÓN: foto de perfil para "usuarios"
--
-- Qué hace:
-- Agrega la columna "foto_perfil" a la tabla "usuarios" para que cualquier
-- cuenta (admin, visitante o socio) pueda guardar su propia foto de perfil
-- desde la nueva funcionalidad "Editar perfil" (perfil.html). La imagen se
-- guarda como texto (data URL en base64), igual que ya se hace con las
-- fotos de "negocios" / "negocio_items" (columna TEXT).
--
-- Ejecutar UNA sola vez, contra tu base ya existente:
--   psql -h 127.0.0.1 -U postgres -d turismo_cultural_colombia -f migration_perfil.sql
-- ============================================================================

BEGIN;

ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS foto_perfil TEXT;

COMMIT;
