-- ============================================================================
-- MIGRACIÓN: sección "Atracciones" por pueblo + itinerario sugerido de 1 día.
--
-- 1) Agrega un campo "orden" a la tabla "atracciones" ya existente, para
--    poder mostrarlas siempre en el mismo orden.
-- 2) Crea la tabla "pueblo_itinerario": el itinerario sugerido de 1 día por
--    pueblo, organizado por franja horaria (mañana / tarde / noche).
--    Cada fila puede (opcionalmente) enlazar a una atracción concreta de la
--    tabla "atracciones" vía "atraccion_id"; si el paso del itinerario no
--    corresponde a ninguna atracción puntual (ej. "desayuno en el parque"),
--    ese campo queda en NULL.
-- 3) Siembra atracciones reales e itinerarios reales para los 6 pueblos que
--    ya existen en la base de datos (gachala, salento, guatape, jardin,
--    villa-de-leyva, mompox), investigados con fuentes turísticas actuales.
--
-- Ejecutar UNA sola vez, después de migration_frontend.sql:
--   psql -h 127.0.0.1 -U postgres -d turismo_cultural_colombia -f migration_atracciones_itinerario.sql
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1) Campo "orden" en "atracciones"
-- ----------------------------------------------------------------------------
ALTER TABLE atracciones
    ADD COLUMN IF NOT EXISTS orden INTEGER NOT NULL DEFAULT 0;

-- ----------------------------------------------------------------------------
-- 2) Tabla "pueblo_itinerario"
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pueblo_itinerario (
    id             SERIAL PRIMARY KEY,
    pueblo_id      INTEGER NOT NULL REFERENCES pueblos(id) ON DELETE CASCADE,
    franja         VARCHAR(10) NOT NULL CHECK (franja IN ('manana', 'tarde', 'noche')),
    orden          INTEGER NOT NULL DEFAULT 0,
    hora_sugerida  VARCHAR(30),
    actividad      TEXT NOT NULL,
    descripcion    TEXT,
    atraccion_id   INTEGER REFERENCES atracciones(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pueblo_itinerario_pueblo ON pueblo_itinerario(pueblo_id);

-- ----------------------------------------------------------------------------
-- 3) Atracciones reales por pueblo
-- ----------------------------------------------------------------------------
INSERT INTO atracciones (nombre, tipo, descripcion, foto, pueblo_id, orden)
SELECT a.nombre, a.tipo, a.descripcion, a.foto, p.id, a.orden
FROM pueblos p
JOIN (VALUES
    -- Gachalá
    ('gachala', 'Embalse del Guavio', 'Naturaleza', 'Uno de los embalses más grandes de Colombia. Se pueden hacer paseos en lancha, pesca y deportes náuticos rodeados de montañas verdes.', 'https://picsum.photos/seed/guavio-embalse/700/500', 1),
    ('gachala', 'Cascada La Chorrera de Gachalá', 'Naturaleza', 'Caída de agua a la que se llega por un sendero ecológico entre bosque nativo, ideal para caminatas cortas y fotografía.', 'https://picsum.photos/seed/gachala-cascada/700/500', 2),
    ('gachala', 'Cueva de los Guácharos', 'Aventura', 'Caverna con formaciones rocosas y fauna única, perfecta para quienes quieren explorar el mundo subterráneo con guía local.', 'https://picsum.photos/seed/gachala-cueva/700/500', 3),
    ('gachala', 'Parque principal y Parroquia de la Inmaculada Concepción', 'Cultural', 'El corazón social del pueblo: plaza tradicional y templo desde donde se aprecia el paisaje de montaña que rodea a Gachalá.', 'https://picsum.photos/seed/gachala-parque/700/500', 4),
    ('gachala', 'Senderismo y torrentismo en la reserva natural', 'Aventura', 'Rutas de trekking entre ríos y bosques, con opción de descenso por cascadas (torrentismo) para los más aventureros.', 'https://picsum.photos/seed/gachala-senderismo/700/500', 5),

    -- Salento
    ('salento', 'Valle de Cocora', 'Naturaleza', 'Hogar de las palmas de cera del Quindío, las más altas del mundo y árbol nacional de Colombia. Caminata clásica de 4 a 5 horas.', 'https://picsum.photos/seed/cocora-valle/700/500', 1),
    ('salento', 'Mirador de Salento (Alto de la Cruz)', 'Naturaleza', 'Subida de 250 escalones desde el centro del pueblo hasta un mirador con vista panorámica del valle cafetero.', 'https://picsum.photos/seed/salento-mirador/700/500', 2),
    ('salento', 'Tour por finca cafetera', 'Gastronómico', 'Recorrido por los cultivos de café, el proceso de tueste y degustación en una finca cercana al pueblo.', 'https://picsum.photos/seed/salento-finca/700/500', 3),
    ('salento', 'Calle Real', 'Cultural', 'La calle principal, llena de balcones coloridos, artesanías y comercio local; el mejor lugar para caminar al atardecer.', 'https://picsum.photos/seed/salento-callereal/700/500', 4),
    ('salento', 'Cabalgatas por las montañas del Quindío', 'Aventura', 'Paseos a caballo por fincas y senderos rurales alrededor de Salento, ideales para grupos y familias.', 'https://picsum.photos/seed/salento-cabalgata/700/500', 5),

    -- Guatapé
    ('guatape', 'Piedra del Peñol', 'Aventura', '740 escalones tallados en la roca que llevan a un mirador de 360° sobre el embalse Peñol-Guatapé.', 'https://picsum.photos/seed/penol-piedra/700/500', 1),
    ('guatape', 'Zócalos de Guatapé', 'Cultural', 'Recorrido fotográfico por las fachadas del pueblo, decoradas con relieves de colores que representan oficios y familias.', 'https://picsum.photos/seed/guatape-zocalos/700/500', 2),
    ('guatape', 'Paseo en bote por el embalse', 'Naturaleza', 'Navegación por el embalse Peñol-Guatapé, con vista a las islas artificiales y a la Piedra del Peñol desde el agua.', 'https://picsum.photos/seed/guatape-bote/700/500', 3),
    ('guatape', 'Malecón de Guatapé', 'Cultural', 'Zona de restaurantes, cafés y tiendas frente al embalse, punto de partida de la mayoría de paseos en bote.', 'https://picsum.photos/seed/guatape-malecon/700/500', 4),
    ('guatape', 'Deportes acuáticos en la represa', 'Aventura', 'Jet ski, banana boat y otras actividades acuáticas organizadas por operadores locales en el embalse.', 'https://picsum.photos/seed/guatape-deportes/700/500', 5),

    -- Jardín
    ('jardin', 'Cueva del Esplendor', 'Naturaleza', 'Cascada de unos 40 metros que cae dentro de una cueva, a unos 7-10 km del pueblo. Se llega caminando o a caballo, con guía.', 'https://picsum.photos/seed/jardin-cueva/700/500', 1),
    ('jardin', 'La Garrucha', 'Aventura', 'Teleférico artesanal creado por los campesinos para cruzar la quebrada Volcanes; hoy también es un paseo turístico.', 'https://picsum.photos/seed/jardin-garrucha/700/500', 2),
    ('jardin', 'Reserva Natural Jardín de Rocas (gallito de roca)', 'Naturaleza', 'Reserva privada donde se puede avistar al gallito de roca andino, mejor entre las 3:00 p. m. y las 5:30 p. m.', 'https://picsum.photos/seed/jardin-gallito/700/500', 3),
    ('jardin', 'Basílica de la Inmaculada Concepción y parque principal', 'Cultural', 'Templo neogótico de doble torre frente al parque; el plan clásico es sentarse en las mecedoras de los cafés a su alrededor.', 'https://picsum.photos/seed/jardin-basilica/700/500', 4),
    ('jardin', 'Tour por finca cafetera', 'Gastronómico', 'Visita a fincas del suroeste antioqueño para conocer el proceso del café y probarlo recién pasado.', 'https://picsum.photos/seed/jardin-finca/700/500', 5),

    -- Villa de Leyva
    ('villa-de-leyva', 'Plaza Mayor', 'Cultural', 'Una de las plazas empedradas más grandes de Suramérica, rodeada de casas coloniales blancas sin una sola línea de pavimento moderno.', 'https://picsum.photos/seed/villaleyva-plaza/700/500', 1),
    ('villa-de-leyva', 'Desierto de la Candelaria', 'Naturaleza', 'Paisaje semidesértico de formaciones rocosas rojizas a las afueras del pueblo, ideal para caminatas y fotografía.', 'https://picsum.photos/seed/villaleyva-desierto/700/500', 2),
    ('villa-de-leyva', 'Museo El Fósil', 'Cultural', 'Museo construido alrededor de un kronosaurio fosilizado encontrado en la zona, referencia de la riqueza paleontológica de Villa de Leyva.', 'https://picsum.photos/seed/villaleyva-fosil/700/500', 3),
    ('villa-de-leyva', 'Pozos Azules', 'Naturaleza', 'Pequeñas lagunas de tonos turquesa formadas por la mineralización del terreno, cerca del desierto de la Candelaria.', 'https://picsum.photos/seed/villaleyva-pozos/700/500', 4),
    ('villa-de-leyva', 'Viñedos boyacenses (Ain Karim)', 'Gastronómico', 'Recorrido y cata en uno de los viñedos de altura de la región, poco comunes en Colombia por el clima seco y templado.', 'https://picsum.photos/seed/villaleyva-vinedo/700/500', 5),

    -- Mompox
    ('mompox', 'Paseo en champán por el río Magdalena', 'Naturaleza', 'Recorrido en embarcación tradicional por el río Magdalena, con vista a los balcones coloniales desde el agua.', 'https://picsum.photos/seed/mompox-champan/700/500', 1),
    ('mompox', 'Iglesia de Santa Bárbara', 'Cultural', 'El templo más fotografiado de Mompox, con su torre octogonal y balcón único en la arquitectura colonial colombiana.', 'https://picsum.photos/seed/mompox-santabarbara/700/500', 2),
    ('mompox', 'Talleres de orfebrería momposina', 'Cultural', 'Visita a talleres familiares donde se elabora filigrana en oro y plata, oficio tradicional reconocido en toda Colombia.', 'https://picsum.photos/seed/mompox-orfebreria/700/500', 3),
    ('mompox', 'La Albarrada', 'Cultural', 'Malecón colonial junto al río, el lugar favorito para caminar al atardecer y de noche, entre casas con balcones de madera.', 'https://picsum.photos/seed/mompox-albarrada/700/500', 4),
    ('mompox', 'Centro histórico y calles coloniales', 'Cultural', 'Recorrido a pie por las calles declaradas Patrimonio de la Humanidad por la Unesco, con iglesias y casas de los siglos XVI a XIX.', 'https://picsum.photos/seed/mompox-centro/700/500', 5)
) AS a(slug, nombre, tipo, descripcion, foto, orden) ON a.slug = p.slug
WHERE NOT EXISTS (
    SELECT 1 FROM atracciones ax WHERE ax.pueblo_id = p.id AND ax.nombre = a.nombre
);

-- ----------------------------------------------------------------------------
-- 4) Itinerario sugerido de 1 día por pueblo (mañana / tarde / noche)
--    Se enlaza a "atracciones" por nombre + pueblo cuando aplica.
-- ----------------------------------------------------------------------------
INSERT INTO pueblo_itinerario (pueblo_id, franja, orden, hora_sugerida, actividad, descripcion, atraccion_id)
SELECT p.id, i.franja, i.orden, i.hora_sugerida, i.actividad, i.descripcion, ax.id
FROM pueblos p
JOIN (VALUES
    -- Gachalá
    ('gachala', 'manana', 1, '8:00 a. m.', 'Desayuno típico gachaluno', 'Empieza el día con un piquete gachaluno (pollo, arepa y consomé) o arepas de maíz pelado antes de salir al embalse.', NULL),
    ('gachala', 'manana', 2, '9:30 a. m.', 'Recorrido en lancha por el Embalse del Guavio', 'Paseo náutico con vistas a las montañas, ideal para fotografía y avistamiento de aves.', 'Embalse del Guavio'),
    ('gachala', 'tarde', 1, '1:00 p. m.', 'Caminata a la Cascada La Chorrera', 'Sendero ecológico entre bosque nativo hasta la caída de agua; buen momento para refrescarse.', 'Cascada La Chorrera de Gachalá'),
    ('gachala', 'tarde', 2, '3:30 p. m.', 'Cueva de los Guácharos', 'Exploración guiada de la caverna y sus formaciones rocosas.', 'Cueva de los Guácharos'),
    ('gachala', 'noche', 1, '6:30 p. m.', 'Cena en el parque principal', 'Comida típica de la región junto a la Parroquia de la Inmaculada Concepción, con la plaza iluminada.', 'Parque principal y Parroquia de la Inmaculada Concepción'),

    -- Salento
    ('salento', 'manana', 1, '7:00 a. m.', 'Caminata al Valle de Cocora', 'Recorrido entre las palmas de cera más altas del mundo; quienes quieran extender la ruta pueden llegar hasta la Reserva Acaime.', 'Valle de Cocora'),
    ('salento', 'tarde', 1, '1:30 p. m.', 'Tour por finca cafetera', 'Visita guiada al cultivo y proceso del café, con degustación incluida.', 'Tour por finca cafetera'),
    ('salento', 'tarde', 2, '4:00 p. m.', 'Subida al Mirador de Salento', 'Los 250 escalones del Alto de la Cruz regalan la mejor vista panorámica del valle cafetero antes del atardecer.', 'Mirador de Salento (Alto de la Cruz)'),
    ('salento', 'noche', 1, '6:30 p. m.', 'Cena de trucha en la Calle Real', 'Trucha frita con patacón en alguno de los restaurantes de la calle principal, cerrando con artesanías locales.', 'Calle Real'),

    -- Guatapé
    ('guatape', 'manana', 1, '7:30 a. m.', 'Subida a la Piedra del Peñol', 'Los 740 escalones llevan a un mirador de 360° sobre el embalse; ir temprano evita el calor y las filas.', 'Piedra del Peñol'),
    ('guatape', 'tarde', 1, '12:30 p. m.', 'Paseo en bote por el embalse', 'Navegación por el embalse Peñol-Guatapé con almuerzo con vista al agua en el malecón.', 'Paseo en bote por el embalse'),
    ('guatape', 'tarde', 2, '3:30 p. m.', 'Deportes acuáticos', 'Jet ski o banana boat para quienes quieran una tarde más activa en la represa.', 'Deportes acuáticos en la represa'),
    ('guatape', 'noche', 1, '6:00 p. m.', 'Recorrido fotográfico por los zócalos', 'Caminata por las calles del pueblo para fotografiar las fachadas de colores antes de cenar en el malecón.', 'Zócalos de Guatapé'),

    -- Jardín
    ('jardin', 'manana', 1, '6:30 a. m.', 'Avistamiento del gallito de roca', 'Mejor al amanecer o al final de la tarde; se recomienda ir con guía a la reserva natural.', 'Reserva Natural Jardín de Rocas (gallito de roca)'),
    ('jardin', 'manana', 2, '9:00 a. m.', 'Caminata a la Cueva del Esplendor', 'Ruta de 3 a 4 horas (o a caballo) hasta la cascada de 40 metros que cae dentro de una cueva.', 'Cueva del Esplendor'),
    ('jardin', 'tarde', 1, '2:00 p. m.', 'Tour por finca cafetera', 'Almuerzo campesino y recorrido por los cultivos de café del suroeste antioqueño.', 'Tour por finca cafetera'),
    ('jardin', 'tarde', 2, '4:30 p. m.', 'Cruce en La Garrucha', 'Paseo en el teleférico artesanal que cruza la quebrada Volcanes, una tradición campesina convertida en atractivo.', 'La Garrucha'),
    ('jardin', 'noche', 1, '6:30 p. m.', 'Café en el parque principal', 'Cierre del día en las mecedoras de los cafés frente a la Basílica de la Inmaculada Concepción.', 'Basílica de la Inmaculada Concepción y parque principal'),

    -- Villa de Leyva
    ('villa-de-leyva', 'manana', 1, '8:30 a. m.', 'Recorrido por la Plaza Mayor', 'Caminata por una de las plazas empedradas más grandes de Suramérica y sus calles coloniales.', 'Plaza Mayor'),
    ('villa-de-leyva', 'manana', 2, '10:00 a. m.', 'Museo El Fósil', 'Visita al kronosaurio fosilizado y a la historia paleontológica de la región.', 'Museo El Fósil'),
    ('villa-de-leyva', 'tarde', 1, '1:30 p. m.', 'Desierto de la Candelaria y Pozos Azules', 'Caminata por el paisaje semidesértico y las lagunas turquesa cercanas.', 'Desierto de la Candelaria'),
    ('villa-de-leyva', 'noche', 1, '6:30 p. m.', 'Cena y cata en un viñedo boyacense', 'Recorrido y copa de vino de altura en uno de los viñedos de la región antes de volver al pueblo.', 'Viñedos boyacenses (Ain Karim)'),

    -- Mompox
    ('mompox', 'manana', 1, '8:00 a. m.', 'Recorrido a pie por el centro histórico', 'Caminata por las calles coloniales Patrimonio de la Humanidad, deteniéndose en la Iglesia de Santa Bárbara.', 'Iglesia de Santa Bárbara'),
    ('mompox', 'tarde', 1, '2:00 p. m.', 'Taller de orfebrería momposina', 'Visita a un taller familiar para ver de cerca el trabajo en filigrana de oro y plata.', 'Talleres de orfebrería momposina'),
    ('mompox', 'noche', 1, '5:30 p. m.', 'Paseo en champán por el río Magdalena', 'Navegación al atardecer con vista a los balcones coloniales desde el agua.', 'Paseo en champán por el río Magdalena'),
    ('mompox', 'noche', 2, '7:30 p. m.', 'Caminata nocturna por la Albarrada', 'Cierre del día en el malecón colonial, el lugar favorito de los momposinos para caminar de noche.', 'La Albarrada')
) AS i(slug, franja, orden, hora_sugerida, actividad, descripcion, atraccion_nombre) ON i.slug = p.slug
LEFT JOIN atracciones ax ON ax.pueblo_id = p.id AND ax.nombre = i.atraccion_nombre
WHERE NOT EXISTS (
    SELECT 1 FROM pueblo_itinerario pi
    WHERE pi.pueblo_id = p.id AND pi.franja = i.franja AND pi.orden = i.orden
);

COMMIT;
