// ── Conexión con el backend real (FastAPI + PostgreSQL) ─────────────────────
// Antes estos datos estaban escritos a mano aquí mismo; ahora se piden al
// backend en http://127.0.0.1:8000. Si por alguna razón el backend no
// responde (no está corriendo, sin conexión, etc.) se usan los datos de
// respaldo de más abajo para que la página nunca se quede vacía.
const API_BASE_URL_DATOS = (location.hostname === "127.0.0.1" || location.hostname === "localhost")
  ? "http://127.0.0.1:8000"
  : "https://rinconescol-api.onrender.com";

function obtenerJSONSincrono(ruta) {
  const xhr = new XMLHttpRequest();
  try {
    xhr.open("GET", API_BASE_URL_DATOS + ruta, false); // false = síncrona
    xhr.send(null);
    if (xhr.status >= 200 && xhr.status < 300) {
      const body = JSON.parse(xhr.responseText);
      if (body && body.success) {
        return body.data;
      }
    }
  } catch (e) {
    console.warn("No se pudo obtener " + ruta + " del backend:", e);
  }
  return null;
}

// ── Datos de respaldo (se usan solo si el backend no responde) ─────────────
const DESTINOS_RESPALDO = [
  {
    id: "gachala",
    nombre: "Gachalá",
    region: "Cundinamarca",
    sello: "Guavio",
    resumen: "Reconocido por sus hermosos paisajes, el embalse del Guavio y su tradición esmeraldera, ideal para el turismo de naturaleza y descanso.",
    descripcion: "Gachalá es un encantador municipio de Cundinamarca rodeado de montañas y naturaleza. Destaca por el imponente embalse del Guavio, sus paisajes tranquilos y su tradición en la minería de esmeraldas. Es un destino ideal para disfrutar del ecoturismo, la pesca, los deportes acuáticos y la belleza natural de la región.",
    clima: "Templado húmedo, 18°C promedio.",
    imagen: "img/gachala.jpg",
    ubicacion: "Provincia del Guavio, a unas 3 horas de Bogotá, en el departamento de Cundinamarca.",
    alcalde: "Alcaldía Municipal de Gachalá gachala-cundinamarca.gov.co.",
    actividades: ["Recorrido por el Embalse del Guavio", "Senderismo ecológico", "Avistamiento de aves", "Paseos en lancha y fotografía de paisajes"],
    platosTipicos:  ["Trucha al ajillo", "Ajiaco cundinamarqués", "Gallina campesina", "Arepas de maíz pelado"],
    dondeComer: [
      { nombre: "Restaurante El Mirador", tipo: "Comida típica colombiana", descripcion: "Ofrece platos tradicionales con una hermosa vista al Embalse del Guavio."},
      { nombre: "Parador Gachalá", tipo: "Cocina casera", descripcion: "Ideal para disfrutar de almuerzos típicos preparados con ingredientes frescos de la región."},
      { nombre: "Café Guavio", tipo: "Cafetería y comida rápida", descripcion: "Perfecto para tomar un café colombiano acompañado de postres y comidas ligeras."}
    ]
  },
  {
    id: "salento",
    nombre: "Salento",
    region: "Quindío",
    sello: "Eje Cafetero",
    resumen: "La puerta de entrada al Valle de Cocora y a las palmas de cera más altas del mundo.",
    descripcion: "Salento es sinónimo de paisaje cafetero: montañas verdes, balcones de colores vivos y el aroma constante a café recién pasado. Desde aquí se organizan las caminatas al Valle de Cocora, hogar de la palma de cera, el árbol nacional de Colombia.",
    clima: "Templado, 18°C promedio",
    imagen: "img/salento.jpg",
    ubicacion: "A unos 40 minutos de Armenia, en el corazón del Eje Cafetero, departamento del Quindío.",
    alcalde: "Alcaldía Municipal de Salento (consulta el nombre vigente en salento-quindio.gov.co)",
    actividades: ["Caminata al Valle de Cocora", "Tour por fincas cafeteras", "Mirador de Salento", "Cabalgatas por las montañas"],
    platosTipicos: ["Trucha frita con patacón", "Arepa de choclo con queso", "Sancocho de gallina criolla", "Mazamorra con panela"],
    dondeComer: [
      { nombre: "Camino Real", tipo: "Trucha y cocina regional", descripcion: "Un clásico del pueblo para probar la trucha en distintas preparaciones." },
      { nombre: "Bosque de las Nubes", tipo: "Vistas y cocina local", descripcion: "Restaurante con vista al valle, ideal después de la caminata a Cocora." },
      { nombre: "Café Jesús Martín", tipo: "Café de origen", descripcion: "Café cultivado y tostado en el Quindío, buen lugar para llevar café de recuerdo." }
    ]
  },
  {
    id: "guatape",
    nombre: "Guatapé",
    region: "Antioquia",
    sello: "Zócalos",
    resumen: "Fachadas cubiertas de zócalos coloridos y el imponente Peñol vigilando el embalse.",
    descripcion: "Cada casa en Guatapé cuenta una historia a través de sus zócalos, relieves pintados que representan oficios y familias del pueblo. A pocos minutos está La Piedra del Peñol, con más de 700 escalones y una vista completa del embalse.",
    clima: "Templado, 20°C promedio",
    imagen: "img/guatape.jpg",
    ubicacion: "A dos horas de Medellín, junto al embalse Peñol-Guatapé, en el oriente antioqueño.",
    alcalde: "Alcaldía Municipal de Guatapé (consulta el nombre vigente en guatape-antioquia.gov.co)",
    actividades: ["Subida a la Piedra del Peñol (740 escalones)", "Paseo en bote por el embalse", "Ruta fotográfica de los zócalos", "Deportes acuáticos en la represa"],
    platosTipicos: ["Bandeja paisa", "Mojarra frita del embalse", "Arepa de mote", "Buñuelos con chocolate"],
    dondeComer: [
      { nombre: "Fogón Paisa", tipo: "Cocina antioqueña", descripcion: "Bandeja paisa y platos típicos de la región en porciones generosas." },
      { nombre: "La Piscina del Malecón", tipo: "Pescado y mariscos", descripcion: "Vista directa al embalse, ideal para probar mojarra frita." },
      { nombre: "Los Balcones", tipo: "Café y postres", descripcion: "Terraza con vista a las calles de zócalos, perfecta para una pausa." }
    ]
  },
  {
    id: "jardin",
    nombre: "Jardín",
    region: "Antioquia",
    sello: "Suroeste",
    resumen: "Un pueblo cafetero rodeado de montañas donde el tiempo pasa distinto, sentado en el parque principal.",
    descripcion: "Jardín conserva la vida de plaza: gente conversando en las mecedoras de los cafés que rodean el parque, un teleférico que sube a las fincas y un patrimonio religioso notable en su iglesia. Es también punto de partida para avistamiento del gallito de roca.",
    clima: "Templado, 19°C promedio",
    imagen: "img/jardin.jpg",
    ubicacion: "En el suroeste antioqueño, a unas 3 horas de Medellín por carretera de montaña.",
    alcalde: "Alcaldía Municipal de Jardín (consulta el nombre vigente en jardin-antioquia.gov.co)",
    actividades: ["Teleférico a las fincas cafeteras", "Avistamiento de aves y del gallito de roca", "Café en el parque principal", "Visita a la Basílica Menor"],
    platosTipicos: ["Frijoles con garra", "Arepa de mote con chorizo", "Café de finca recién pasado", "Envueltos de maíz"],
    dondeComer: [
      { nombre: "Café Macanas", tipo: "Café de finca", descripcion: "Café propio cultivado en las montañas de Jardín." },
      { nombre: "Restaurante Balcones del Parque", tipo: "Cocina paisa", descripcion: "Vista directa al parque principal y su iglesia." },
      { nombre: "La Fonda de Jardín", tipo: "Cocina campesina", descripcion: "Platos caseros de la región del suroeste antioqueño." }
    ]
  },
  {
    id: "villa-de-leyva",
    nombre: "Villa de Leyva",
    region: "Boyacá",
    sello: "Colonial",
    resumen: "Una de las plazas empedradas más grandes de Suramérica, rodeada de casas blancas centenarias.",
    descripcion: "Villa de Leyva combina historia colonial con paisaje desértico. Su plaza mayor, sin una sola línea de pavimento moderno, es el corazón del pueblo. Alrededor hay fósiles marinos, viñedos y el desierto de la Candelaria.",
    clima: "Seco templado, 18°C promedio",
    imagen: "img/villadeleyva.jpg",
    ubicacion: "A 3 horas de Bogotá, en la provincia de Ricaurte, departamento de Boyacá.",
    alcalde: "Alcaldía Municipal de Villa de Leyva (consulta el nombre vigente en villadeleyva-boyaca.gov.co)",
    actividades: ["Recorrido por la plaza mayor", "Desierto de la Candelaria", "Museo El Fósil", "Ruta de viñedos boyacenses"],
    platosTipicos: ["Cuchuco de trigo con espinazo", "Longaniza boyacense", "Almojábanas", "Mazato de maíz"],
    dondeComer: [
      { nombre: "Casa Blanca", tipo: "Cocina boyacense", descripcion: "Ubicado frente a la plaza mayor, cocina tradicional de la región." },
      { nombre: "Savia Restaurante", tipo: "Cocina de mercado", descripcion: "Platos con ingredientes locales en un ambiente campestre." },
      { nombre: "Viñedo Ain Karim", tipo: "Vinos y cocina local", descripcion: "Tour y almuerzo entre los viñedos a las afueras del pueblo." }
    ]
  },
  {
    id: "mompox",
    nombre: "Santa Cruz de Mompox",
    region: "Bolívar",
    sello: "Río Magdalena",
    resumen: "Orfebrería, balcones sobre el río y un aire colonial que parece sacado de una novela.",
    descripcion: "A orillas del río Magdalena, Mompox fue durante siglos un puerto comercial clave. Hoy conserva iglesias coloniales, casas con balcones de madera y una tradición orfebre reconocida en toda Colombia.",
    clima: "Cálido húmedo, 28°C promedio",
    imagen: "img/mompox.jpg",
    ubicacion: "A orillas del río Magdalena, en el sur del departamento de Bolívar.",
    alcalde: "Alcaldía Municipal de Santa Cruz de Mompox (consulta el nombre vigente en mompos-bolivar.gov.co)",
    actividades: ["Paseo en champán por el río Magdalena", "Talleres de orfebrería momposina", "Recorrido por las iglesias coloniales", "Caminata nocturna por la Albarrada"],
    platosTipicos: ["Mote de queso", "Butifarra momposina", "Dulce de níspero", "Pescado frito del Magdalena"],
    dondeComer: [
      { nombre: "El Fuerte San Anselmo", tipo: "Cocina caribeña", descripcion: "Frente al río, con platos de pescado típicos de la región." },
      { nombre: "Comedor Costeño", tipo: "Cocina tradicional", descripcion: "Butifarra y mote de queso preparados como en casa." },
      { nombre: "La Casa Amarilla", tipo: "Café y postres", descripcion: "Buen lugar para probar el dulce de níspero y descansar del calor." }
    ]
  }
];

const GASTRONOMIA_RESPALDO = [
  { id: "trucha-guavio", nombre: "Trucha del Guavio", region: "Gachalá, Cundinamarca", descripcion: "Trucha fresca del Embalse del Guavio, preparada al ajillo o a la plancha y acompañada de arroz, patacón, ensalada y papa. Es uno de los platos más representativos de la gastronomía local.", imagen: "img/gastronomia/trucha-guavio.jpg" },
  { id: "ajiaco", nombre: "Ajiaco Santafereño", region: "Cundinamarca / Boyacá", descripcion: "Sopa espesa de tres papas, pollo desmechado y guasca, servida con crema de leche, alcaparras y aguacate. El plato que abriga el clima frío de la sabana.", imagen: "img/gastronomia/ajiaco.jpg" },
  { id: "arepa-choclo", nombre: "Arepa de Choclo", region: "Eje Cafetero", descripcion: "Arepa dulce hecha con maíz tierno, acompañada de queso campesino. El desayuno favorito en los pueblos del Quindío y Risaralda.", imagen: "img/gastronomia/arepa-choclo.jpg" },
  { id: "sancocho", nombre: "Sancocho de Gallina", region: "Todo el país", descripcion: "Un caldo contundente de gallina criolla, yuca, plátano y mazorca, cocinado a fuego lento. Cada región tiene su propia versión, pero siempre reúne a la familia.", imagen: "img/gastronomia/sancocho.jpg" },
  { id: "mote-queso", nombre: "Mote de Queso", region: "Costa Caribe", descripcion: "Sopa cremosa de ñame con queso costeño derretido, típica de los pueblos de Sucre y Bolívar como Mompox.", imagen: "img/gastronomia/mote-queso.jpg" },
  { id: "buñuelos", nombre: "Buñuelos y Natilla", region: "Todo el país", descripcion: "La dupla infaltable de la época decembrina: bolitas de queso fritas y un postre de maíz dulce con canela.", imagen: "img/gastronomia/bunuelos-natilla.jpg" }
];

// ── Se piden los datos reales al backend; si falla, se usa el respaldo ────
const _pueblosApi = obtenerJSONSincrono("/pueblos/");
const _gastronomiaApi = obtenerJSONSincrono("/gastronomia/");

const DESTINOS = (_pueblosApi && _pueblosApi.length) ? _pueblosApi : DESTINOS_RESPALDO;
const GASTRONOMIA = (_gastronomiaApi && _gastronomiaApi.length) ? _gastronomiaApi : GASTRONOMIA_RESPALDO;