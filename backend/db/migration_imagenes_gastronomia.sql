-- ----------------------------------------------------------------------------
-- Cambia la foto de cada plato de gastronomía: antes usaban picsum.photos
-- (fotos aleatorias que no tenían que ver con el plato) y ahora apuntan a
-- las fotos reales guardadas en frontend/img/gastronomia/.
--
-- Antes de correrlo, ejecuta: python scripts/descargar_imagenes.py
-- ----------------------------------------------------------------------------

UPDATE gastronomia SET foto = 'img/gastronomia/trucha-guavio.jpg'   WHERE nombre = 'Trucha del Guavio';
UPDATE gastronomia SET foto = 'img/gastronomia/ajiaco.jpg'          WHERE nombre = 'Ajiaco Santafereño';
UPDATE gastronomia SET foto = 'img/gastronomia/arepa-choclo.jpg'    WHERE nombre = 'Arepa de Choclo';
UPDATE gastronomia SET foto = 'img/gastronomia/sancocho.jpg'        WHERE nombre = 'Sancocho de Gallina';
UPDATE gastronomia SET foto = 'img/gastronomia/mote-queso.jpg'      WHERE nombre = 'Mote de Queso';
UPDATE gastronomia SET foto = 'img/gastronomia/bunuelos-natilla.jpg' WHERE nombre = 'Buñuelos y Natilla';

-- Para verificar:
-- SELECT nombre, foto FROM gastronomia ORDER BY id;
