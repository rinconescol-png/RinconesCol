-- ----------------------------------------------------------------------------
-- Corrige el campo "imagen" de TODOS los pueblos para que apunte a la
-- carpeta local frontend/img/. La base de datos tenía valores viejos
-- (algunos sin el prefijo "img/", otros con picsum.photos) porque el
-- INSERT original usa ON CONFLICT DO NOTHING y nunca se volvió a aplicar
-- sobre las filas ya existentes.
--
-- Ejecutar esto directamente en tu BD (psql, DBeaver, pgAdmin, etc.)
-- Antes de correrlo, asegúrate de tener estos 6 archivos dentro de
-- RinconesCol/frontend/img/:
--   gachala.jpg, mompox.jpg (ya los tenías)
--   salento.jpg, guatape.jpg, jardin.jpg, villadeleyva.jpg (los nuevos)
-- ----------------------------------------------------------------------------

UPDATE pueblos SET imagen = 'img/gachala.jpg'      WHERE slug = 'gachala';
UPDATE pueblos SET imagen = 'img/mompox.jpg'       WHERE slug = 'mompox';
UPDATE pueblos SET imagen = 'img/salento.jpg'      WHERE slug = 'salento';
UPDATE pueblos SET imagen = 'img/guatape.jpg'      WHERE slug = 'guatape';
UPDATE pueblos SET imagen = 'img/jardin.jpg'       WHERE slug = 'jardin';
UPDATE pueblos SET imagen = 'img/villadeleyva.jpg' WHERE slug = 'villa-de-leyva';

-- Para verificar que quedó bien:
-- SELECT slug, imagen FROM pueblos ORDER BY slug;
