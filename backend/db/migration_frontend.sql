-- ============================================================================
-- MIGRACIÓN: adapta la base de datos "turismo_cultural_colombia" a los datos
-- que el frontend (RinconesCol_Ultimo) necesita para destinos.html, destino.html,
-- gastronomia.html y home.html, sin tocar ni una línea del frontend.
--
-- Ejecutar UNA sola vez contra la base ya existente, por ejemplo:
--   psql -h 127.0.0.1 -U postgres -d turismo_cultural_colombia -f migration_frontend.sql
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1) Ampliar la tabla "pueblos" con los campos que usa destinos.html/destino.html
-- ----------------------------------------------------------------------------
ALTER TABLE pueblos
    ADD COLUMN IF NOT EXISTS slug        VARCHAR(80) UNIQUE,
    ADD COLUMN IF NOT EXISTS region      VARCHAR(120),
    ADD COLUMN IF NOT EXISTS sello       VARCHAR(80),
    ADD COLUMN IF NOT EXISTS resumen     TEXT,
    ADD COLUMN IF NOT EXISTS clima       VARCHAR(120),
    ADD COLUMN IF NOT EXISTS ubicacion   TEXT,
    ADD COLUMN IF NOT EXISTS alcalde     TEXT;

-- ----------------------------------------------------------------------------
-- 2) Tablas hijas de "pueblos": actividades, platos típicos y restaurantes
--    (lo que destino.html muestra en "🧭 Actividades", "🍽️ Platos típicos"
--    y "🍴 Dónde comer")
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pueblo_actividades (
    id         SERIAL PRIMARY KEY,
    pueblo_id  INTEGER NOT NULL REFERENCES pueblos(id) ON DELETE CASCADE,
    actividad  TEXT NOT NULL,
    orden      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pueblo_platos_tipicos (
    id         SERIAL PRIMARY KEY,
    pueblo_id  INTEGER NOT NULL REFERENCES pueblos(id) ON DELETE CASCADE,
    plato      TEXT NOT NULL,
    orden      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pueblo_restaurantes (
    id           SERIAL PRIMARY KEY,
    pueblo_id    INTEGER NOT NULL REFERENCES pueblos(id) ON DELETE CASCADE,
    nombre       VARCHAR(150) NOT NULL,
    tipo         VARCHAR(150),
    descripcion  TEXT,
    orden        INTEGER NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- 3) Ampliar "gastronomia" con la región que muestra gastronomia.html/home.html
-- ----------------------------------------------------------------------------
ALTER TABLE gastronomia
    ADD COLUMN IF NOT EXISTS region VARCHAR(150);

-- ----------------------------------------------------------------------------
-- 4) Semilla de datos: los 6 pueblos que ya existían como contenido estático
--    en js/data.js, ahora migrados a la base de datos real.
-- ----------------------------------------------------------------------------
INSERT INTO pueblos (nombre, departamento, municipio, slug, region, sello, resumen, descripcion, historia, clima, imagen, ubicacion, alcalde, latitud, longitud)
VALUES
('Gachalá', 'Cundinamarca', 'Gachalá', 'gachala', 'Cundinamarca', 'Guavio',
 'Reconocido por sus hermosos paisajes, el embalse del Guavio y su tradición esmeraldera, ideal para el turismo de naturaleza y descanso.',
 'Gachalá es un encantador municipio de Cundinamarca rodeado de montañas y naturaleza. Destaca por el imponente embalse del Guavio, sus paisajes tranquilos y su tradición en la minería de esmeraldas. Es un destino ideal para disfrutar del ecoturismo, la pesca, los deportes acuáticos y la belleza natural de la región.',
 NULL, 'Templado húmedo, 18°C promedio.', 'img/gachala.jpg',
 'Provincia del Guavio, a unas 3 horas de Bogotá, en el departamento de Cundinamarca.',
 'Alcaldía Municipal de Gachalá gachala-cundinamarca.gov.co.', NULL, NULL),

('Salento', 'Quindío', 'Salento', 'salento', 'Quindío', 'Eje Cafetero',
 'La puerta de entrada al Valle de Cocora y a las palmas de cera más altas del mundo.',
 'Salento es sinónimo de paisaje cafetero: montañas verdes, balcones de colores vivos y el aroma constante a café recién pasado. Desde aquí se organizan las caminatas al Valle de Cocora, hogar de la palma de cera, el árbol nacional de Colombia.',
 NULL, 'Templado, 18°C promedio', 'img/salento.jpg',
 'A unos 40 minutos de Armenia, en el corazón del Eje Cafetero, departamento del Quindío.',
 'Alcaldía Municipal de Salento (consulta el nombre vigente en salento-quindio.gov.co)', NULL, NULL),

('Guatapé', 'Antioquia', 'Guatapé', 'guatape', 'Antioquia', 'Zócalos',
 'Fachadas cubiertas de zócalos coloridos y el imponente Peñol vigilando el embalse.',
 'Cada casa en Guatapé cuenta una historia a través de sus zócalos, relieves pintados que representan oficios y familias del pueblo. A pocos minutos está La Piedra del Peñol, con más de 700 escalones y una vista completa del embalse.',
 NULL, 'Templado, 20°C promedio', 'img/guatape.jpg',
 'A dos horas de Medellín, junto al embalse Peñol-Guatapé, en el oriente antioqueño.',
 'Alcaldía Municipal de Guatapé (consulta el nombre vigente en guatape-antioquia.gov.co)', NULL, NULL),

('Jardín', 'Antioquia', 'Jardín', 'jardin', 'Antioquia', 'Suroeste',
 'Un pueblo cafetero rodeado de montañas donde el tiempo pasa distinto, sentado en el parque principal.',
 'Jardín conserva la vida de plaza: gente conversando en las mecedoras de los cafés que rodean el parque, un teleférico que sube a las fincas y un patrimonio religioso notable en su iglesia. Es también punto de partida para avistamiento del gallito de roca.',
 NULL, 'Templado, 19°C promedio', 'img/jardin.jpg',
 'En el suroeste antioqueño, a unas 3 horas de Medellín por carretera de montaña.',
 'Alcaldía Municipal de Jardín (consulta el nombre vigente en jardin-antioquia.gov.co)', NULL, NULL),

('Villa de Leyva', 'Boyacá', 'Villa de Leyva', 'villa-de-leyva', 'Boyacá', 'Colonial',
 'Una de las plazas empedradas más grandes de Suramérica, rodeada de casas blancas centenarias.',
 'Villa de Leyva combina historia colonial con paisaje desértico. Su plaza mayor, sin una sola línea de pavimento moderno, es el corazón del pueblo. Alrededor hay fósiles marinos, viñedos y el desierto de la Candelaria.',
 NULL, 'Seco templado, 18°C promedio', 'img/villadeleyva.jpg',
 'A 3 horas de Bogotá, en la provincia de Ricaurte, departamento de Boyacá.',
 'Alcaldía Municipal de Villa de Leyva (consulta el nombre vigente en villadeleyva-boyaca.gov.co)', NULL, NULL),

('Santa Cruz de Mompox', 'Bolívar', 'Mompox', 'mompox', 'Bolívar', 'Río Magdalena',
 'Orfebrería, balcones sobre el río y un aire colonial que parece sacado de una novela.',
 'A orillas del río Magdalena, Mompox fue durante siglos un puerto comercial clave. Hoy conserva iglesias coloniales, casas con balcones de madera y una tradición orfebre reconocida en toda Colombia.',
 NULL, 'Cálido húmedo, 28°C promedio', 'img/mompox.jpg',
 'A orillas del río Magdalena, en el sur del departamento de Bolívar.',
 'Alcaldía Municipal de Santa Cruz de Mompox (consulta el nombre vigente en mompos-bolivar.gov.co)', NULL, NULL)
ON CONFLICT (slug) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 5) Actividades por pueblo
-- ----------------------------------------------------------------------------
INSERT INTO pueblo_actividades (pueblo_id, actividad, orden)
SELECT p.id, a.actividad, a.orden
FROM pueblos p
JOIN (VALUES
    ('gachala', 'Recorrido por el Embalse del Guavio', 1),
    ('gachala', 'Senderismo ecológico', 2),
    ('gachala', 'Avistamiento de aves', 3),
    ('gachala', 'Paseos en lancha y fotografía de paisajes', 4),
    ('salento', 'Caminata al Valle de Cocora', 1),
    ('salento', 'Tour por fincas cafeteras', 2),
    ('salento', 'Mirador de Salento', 3),
    ('salento', 'Cabalgatas por las montañas', 4),
    ('guatape', 'Subida a la Piedra del Peñol (740 escalones)', 1),
    ('guatape', 'Paseo en bote por el embalse', 2),
    ('guatape', 'Ruta fotográfica de los zócalos', 3),
    ('guatape', 'Deportes acuáticos en la represa', 4),
    ('jardin', 'Teleférico a las fincas cafeteras', 1),
    ('jardin', 'Avistamiento de aves y del gallito de roca', 2),
    ('jardin', 'Café en el parque principal', 3),
    ('jardin', 'Visita a la Basílica Menor', 4),
    ('villa-de-leyva', 'Recorrido por la plaza mayor', 1),
    ('villa-de-leyva', 'Desierto de la Candelaria', 2),
    ('villa-de-leyva', 'Museo El Fósil', 3),
    ('villa-de-leyva', 'Ruta de viñedos boyacenses', 4),
    ('mompox', 'Paseo en champán por el río Magdalena', 1),
    ('mompox', 'Talleres de orfebrería momposina', 2),
    ('mompox', 'Recorrido por las iglesias coloniales', 3),
    ('mompox', 'Caminata nocturna por la Albarrada', 4)
) AS a(slug, actividad, orden) ON a.slug = p.slug
WHERE NOT EXISTS (SELECT 1 FROM pueblo_actividades pa WHERE pa.pueblo_id = p.id);

-- ----------------------------------------------------------------------------
-- 6) Platos típicos por pueblo
-- ----------------------------------------------------------------------------
INSERT INTO pueblo_platos_tipicos (pueblo_id, plato, orden)
SELECT p.id, a.plato, a.orden
FROM pueblos p
JOIN (VALUES
    ('gachala', 'Trucha al ajillo', 1),
    ('gachala', 'Ajiaco cundinamarqués', 2),
    ('gachala', 'Gallina campesina', 3),
    ('gachala', 'Arepas de maíz pelado', 4),
    ('salento', 'Trucha frita con patacón', 1),
    ('salento', 'Arepa de choclo con queso', 2),
    ('salento', 'Sancocho de gallina criolla', 3),
    ('salento', 'Mazamorra con panela', 4),
    ('guatape', 'Bandeja paisa', 1),
    ('guatape', 'Mojarra frita del embalse', 2),
    ('guatape', 'Arepa de mote', 3),
    ('guatape', 'Buñuelos con chocolate', 4),
    ('jardin', 'Frijoles con garra', 1),
    ('jardin', 'Arepa de mote con chorizo', 2),
    ('jardin', 'Café de finca recién pasado', 3),
    ('jardin', 'Envueltos de maíz', 4),
    ('villa-de-leyva', 'Cuchuco de trigo con espinazo', 1),
    ('villa-de-leyva', 'Longaniza boyacense', 2),
    ('villa-de-leyva', 'Almojábanas', 3),
    ('villa-de-leyva', 'Mazato de maíz', 4),
    ('mompox', 'Mote de queso', 1),
    ('mompox', 'Butifarra momposina', 2),
    ('mompox', 'Dulce de níspero', 3),
    ('mompox', 'Pescado frito del Magdalena', 4)
) AS a(slug, plato, orden) ON a.slug = p.slug
WHERE NOT EXISTS (SELECT 1 FROM pueblo_platos_tipicos pt WHERE pt.pueblo_id = p.id);

-- ----------------------------------------------------------------------------
-- 7) Restaurantes ("Dónde comer") por pueblo
-- ----------------------------------------------------------------------------
INSERT INTO pueblo_restaurantes (pueblo_id, nombre, tipo, descripcion, orden)
SELECT p.id, r.nombre, r.tipo, r.descripcion, r.orden
FROM pueblos p
JOIN (VALUES
    ('gachala', 'Restaurante El Mirador', 'Comida típica colombiana', 'Ofrece platos tradicionales con una hermosa vista al Embalse del Guavio.', 1),
    ('gachala', 'Parador Gachalá', 'Cocina casera', 'Ideal para disfrutar de almuerzos típicos preparados con ingredientes frescos de la región.', 2),
    ('gachala', 'Café Guavio', 'Cafetería y comida rápida', 'Perfecto para tomar un café colombiano acompañado de postres y comidas ligeras.', 3),
    ('salento', 'Camino Real', 'Trucha y cocina regional', 'Un clásico del pueblo para probar la trucha en distintas preparaciones.', 1),
    ('salento', 'Bosque de las Nubes', 'Vistas y cocina local', 'Restaurante con vista al valle, ideal después de la caminata a Cocora.', 2),
    ('salento', 'Café Jesús Martín', 'Café de origen', 'Café cultivado y tostado en el Quindío, buen lugar para llevar café de recuerdo.', 3),
    ('guatape', 'Fogón Paisa', 'Cocina antioqueña', 'Bandeja paisa y platos típicos de la región en porciones generosas.', 1),
    ('guatape', 'La Piscina del Malecón', 'Pescado y mariscos', 'Vista directa al embalse, ideal para probar mojarra frita.', 2),
    ('guatape', 'Los Balcones', 'Café y postres', 'Terraza con vista a las calles de zócalos, perfecta para una pausa.', 3),
    ('jardin', 'Café Macanas', 'Café de finca', 'Café propio cultivado en las montañas de Jardín.', 1),
    ('jardin', 'Restaurante Balcones del Parque', 'Cocina paisa', 'Vista directa al parque principal y su iglesia.', 2),
    ('jardin', 'La Fonda de Jardín', 'Cocina campesina', 'Platos caseros de la región del suroeste antioqueño.', 3),
    ('villa-de-leyva', 'Casa Blanca', 'Cocina boyacense', 'Ubicado frente a la plaza mayor, cocina tradicional de la región.', 1),
    ('villa-de-leyva', 'Savia Restaurante', 'Cocina de mercado', 'Platos con ingredientes locales en un ambiente campestre.', 2),
    ('villa-de-leyva', 'Viñedo Ain Karim', 'Vinos y cocina local', 'Tour y almuerzo entre los viñedos a las afueras del pueblo.', 3),
    ('mompox', 'El Fuerte San Anselmo', 'Cocina caribeña', 'Frente al río, con platos de pescado típicos de la región.', 1),
    ('mompox', 'Comedor Costeño', 'Cocina tradicional', 'Butifarra y mote de queso preparados como en casa.', 2),
    ('mompox', 'La Casa Amarilla', 'Café y postres', 'Buen lugar para probar el dulce de níspero y descansar del calor.', 3)
) AS r(slug, nombre, tipo, descripcion, orden) ON r.slug = p.slug
WHERE NOT EXISTS (SELECT 1 FROM pueblo_restaurantes pr WHERE pr.pueblo_id = p.id);

-- ----------------------------------------------------------------------------
-- 8) Gastronomía (lista global que usa gastronomia.html / home.html)
-- ----------------------------------------------------------------------------
INSERT INTO gastronomia (nombre, descripcion, foto, region, pueblo_id)
SELECT g.nombre, g.descripcion, g.foto, g.region, p.id
FROM (VALUES
    ('Trucha del Guavio', 'Trucha fresca del Embalse del Guavio, preparada al ajillo o a la plancha y acompañada de arroz, patacón, ensalada y papa. Es uno de los platos más representativos de la gastronomía local.', 'https://picsum.photos/seed/truchaguavio/700/500', 'Gachalá, Cundinamarca', 'gachala'),
    ('Ajiaco Santafereño', 'Sopa espesa de tres papas, pollo desmechado y guasca, servida con crema de leche, alcaparras y aguacate. El plato que abriga el clima frío de la sabana.', 'https://picsum.photos/seed/ajiaco/700/500', 'Cundinamarca / Boyacá', NULL),
    ('Arepa de Choclo', 'Arepa dulce hecha con maíz tierno, acompañada de queso campesino. El desayuno favorito en los pueblos del Quindío y Risaralda.', 'https://picsum.photos/seed/arepachoclo/700/500', 'Eje Cafetero', 'salento'),
    ('Sancocho de Gallina', 'Un caldo contundente de gallina criolla, yuca, plátano y mazorca, cocinado a fuego lento. Cada región tiene su propia versión, pero siempre reúne a la familia.', 'https://picsum.photos/seed/sancocho/700/500', 'Todo el país', NULL),
    ('Mote de Queso', 'Sopa cremosa de ñame con queso costeño derretido, típica de los pueblos de Sucre y Bolívar como Mompox.', 'https://picsum.photos/seed/motequeso/700/500', 'Costa Caribe', 'mompox'),
    ('Buñuelos y Natilla', 'La dupla infaltable de la época decembrina: bolitas de queso fritas y un postre de maíz dulce con canela.', 'https://picsum.photos/seed/bunuelos/700/500', 'Todo el país', NULL)
) AS g(nombre, descripcion, foto, region, slug)
LEFT JOIN pueblos p ON p.slug = g.slug
WHERE NOT EXISTS (SELECT 1 FROM gastronomia existente WHERE existente.nombre = g.nombre);

COMMIT;
