-- ============================================================================
-- MIGRACIÓN: ubicación (dirección / cómo llegar) del negocio del socio
-- Ejecutar UNA vez (es seguro repetirla):
--   psql -h 127.0.0.1 -U postgres -d turismo_cultural_colombia -f db/migration_negocio_ubicacion.sql
-- ============================================================================
ALTER TABLE negocios ADD COLUMN IF NOT EXISTS ubicacion TEXT;
