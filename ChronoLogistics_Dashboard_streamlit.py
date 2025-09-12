"""
ChronoLogistics - Dashboard Operativo (Streamlit)
Archivo único: ChronoLogistics_Dashboard_streamlit.py

Instrucciones rápidas:
1) Crear un entorno virtual (recomendado) y pip install -r requirements.txt
   Requisitos: streamlit, numpy, matplotlib, pillow
   Ejemplo: pip install streamlit numpy matplotlib pillow
2) Colocar las imágenes pre-generadas en ./assets/
   - assets/map_clusters.png      (opcional; el script genera uno de ejemplo si no existe)
   - assets/fortaleza_verde.jpg
   - assets/bunker_tecnologico.jpg
3) Ejecutar: streamlit run ChronoLogistics_Dashboard_streamlit.py

Nota: Este archivo está diseñado para ser autocontenido y ejecutable en local.
Reemplace las imágenes de ejemplo por las GANs y mapas oficiales antes de la demo.

Descripción funcional (resumen):
- Pestaña "Precog" genera (o carga) un mapa de calor con 4 clusters y marca los 3 más críticos.
  Ofrece sliders para variables tácticas y llama a precog.predecir_riesgo() para mostrar un
  "Nivel de Riesgo en Cascada" en tiempo real.
- Pestaña "Chronos" permite seleccionar estrategia a 2040 y muestra imagen + defensa.
- Pestaña "K-Lang" contiene selector de protocolos (VÍSPERA, CÓDIGO ROJO, RENACIMIENTO)
  y un simulador de sensores (viento, inundación) que determina automáticamente el
  protocolo activo y muestra la ficha técnica.

Autor: Equipo de Estrategia y Respuesta a Crisis de IA (plantilla entregable)
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os
from io import BytesIO

st.set_page_config(page_title="ChronoLogistics - Dashboard Operativo", layout="wide")

# ----------------------- Utilidades y Lógica -----------------------
class Precog:
    """Lógica interna para predecir riesgo."""
    def __init__(self):
        pass

    def predecir_riesgo(self, velocidad_media, intensidad_lluvia, ocupacion_transito):
        """Modelo simple: combinación lineal + no-lineal para producir un score 0-100.
        Esta función es un placeholder: sustituidla por vuestro modelo real.
        """
        # normalizar entradas
        v = np.clip(velocidad_media / 150.0, 0, 1)
        r = np.clip(intensidad_lluvia / 200.0, 0, 1)
        t = np.clip(ocupacion_transito / 100.0, 0, 1)

        # score base
        score = 0.5 * v + 0.35 * r + 0.15 * t
        # término no-lineal para eventos extremos
        extreme = 0
        if velocidad_media > 100:
            extreme += 0.12 * ((velocidad_media - 100) / 50)
        if intensidad_lluvia > 120:
            extreme += 0.12 * ((intensidad_lluvia - 120) / 80)

        final = np.clip((score + extreme) * 100, 0, 100)
        return float(final)


def riesgo_label(score):
    if score < 30:
        return f"{score:.0f}% - BAJO", "green"
    elif score < 60:
        return f"{score:.0f}% - MEDIO", "orange"
    else:
        return f"{score:.0f}% - ALTO", "red"


PREC = Precog()

# ----------------------- Map Generator (Ejemplo) -----------------------
def generar_mapa_clusters(save_path=None, seed=42):
    """Genera una imagen de mapa de calor con 4 clusters de ejemplo y devuelve la imagen PIL.
    Marca además los 3 clusters más críticos (los de mayor intensidad) con triángulos.
    """
    np.random.seed(seed)
    x = np.concatenate([
        np.random.normal(loc=[30, 30], scale=6, size=(400, 2)),
        np.random.normal(loc=[70, 40], scale=8, size=(300, 2)),
        np.random.normal(loc=[50, 70], scale=10, size=(200, 2)),
        np.random.normal(loc=[80, 80], scale=5, size=(150, 2)),
    ])
    heat, xedges, yedges = np.histogram2d(x[:, 0], x[:, 1], bins=80, range=[[0,100],[0,100]])
    heat = np.rot90(heat)
    heat = np.flipud(heat)

    fig, ax = plt.subplots(figsize=(6,6))
    im = ax.imshow(heat, extent=[0,100,0,100], origin='lower', cmap='hot')
    ax.set_title('Mapa de Calor - Clústeres de Riesgo (Ejemplo)')
    ax.set_xlabel('Longitud (simulada)')
    ax.set_ylabel('Latitud (simulada)')

    # detectar 4 máximos simples para simular centros de clusters
    from scipy.ndimage import maximum_filter, gaussian_filter
    blurred = gaussian_filter(heat, sigma=2)
    flat = blurred.flatten()
    idxs = np.argsort(flat)[-4:]
    ys, xs = np.unravel_index(idxs, blurred.shape)
    # convertir a coordenadas 0-100
    xs_coord = xedges[xs]
    ys_coord = yedges[ys]

    # calcular intensidades para marcar los 3 más críticos
    intensities = [blurred[y,x] for y,x in zip(ys,xs)]
    order = np.argsort(intensities)[::-1]
    top3 = [ (xs_coord[i], ys_coord[i]) for i in order[:3] ]

    # marcar triángulos
    for (xc,yc) in top3:
        ax.scatter(xc, yc, marker='^', s=200, facecolors='none', edgecolors='cyan', linewidths=2)

    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    buf = BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf)

    if save_path:
        img.save(save_path)
    return img, top3

# ----------------------- Protocolos K-Lang -----------------------
PROTOCOLS = {
    'VÍSPERA': {
        'trigger': 'Condiciones pre-alerta: viento moderado o lluvias localizadas',
        'actions': [
            'Activar patrullas de inspección',
            'Preparar centros de refugio',
            'Notificar a stakeholders clave'
        ]
    },
    'CÓDIGO ROJO': {
        'trigger': 'Evento extremo: vientos > 90 km/h o inundación > 80 cm',
        'actions': [
            'Evacuación inmediata de zonas de riesgo',
            'Corte de suministro selectivo',
            'Activación del equipo TITÁN y comunicación pública']
    },
    'RENACIMIENTO': {
        'trigger': 'Post-evento: daños estabilizados, iniciar recuperación',
        'actions': [
            'Evaluación de daños',
            'Planificación de reconstrucción prioritaria',
            'Revisar y adaptar protocolos']
        }
}


def determinar_protocolo(viento_kmh, nivel_inundacion_cm):
    """Reglas heurísticas para decidir qué protocolo estaría activo.
    Devuelve (protocolo, razon)
    """
    if viento_kmh >= 95 or nivel_inundacion_cm >= 80:
        return 'CÓDIGO ROJO', 'Viento >= 95 km/h o Inundación >= 80 cm'
    if viento_kmh >= 40 or nivel_inundacion_cm >= 30:
        return 'VÍSPERA', 'Condiciones de pre-alerta: viento >=40 km/h o inundación >=30 cm'
    return 'RENACIMIENTO', 'Condición normal / post-evento'

# ----------------------- UI -----------------------

st.markdown('<h1 style="text-align:center">ChronoLogistics — Dashboard Operativo</h1>', unsafe_allow_html=True)

tabs = st.tabs(["Precog: Monitor de Riesgo Táctico", "Chronos: Visión Estratégica 2040", "K-Lang: Manual de Batalla Interactivo"])

# ----------------------- Pestaña 1: Precog -----------------------
with tabs[0]:
    st.header('Precog: Monitor de Riesgo Táctico')
    col1, col2 = st.columns([2,1])

    # izquierda: mapa + top3
    with col1:
        st.subheader('Mapa de Calor de Riesgo')
        asset_map = 'assets/map_clusters.png'
        if os.path.exists(asset_map):
            img = Image.open(asset_map)
            # Asumimos que la imagen ya tiene marcadores si fue exportada desde análisis
            st.image(img, use_container_width=True)
            # nota: si queréis resaltar triángulos dinámicamente, calculad top3 y replotear
        else:
            img_gen, top3 = generar_mapa_clusters(save_path=None)
            st.image(img_gen, use_container_width=True)
            st.markdown('**Triángulo del Peligro**: los 3 triángulos cyan marcan los clústeres más críticos (generado).')

    # derecha: simulador
    with col2:
        st.subheader('Simulador de Riesgo Interactivo')
        velocidad_media = st.slider('Velocidad media (km/h)', min_value=0, max_value=160, value=60)
        intensidad_lluvia = st.slider('Intensidad de lluvia (mm/h)', min_value=0, max_value=300, value=20)
        ocupacion_transito = st.slider('Ocupación de tráfico (%)', min_value=0, max_value=100, value=45)

        score = PREC.predecir_riesgo(velocidad_media, intensidad_lluvia, ocupacion_transito)
        label, color = riesgo_label(score)

        st.metric(label='Nivel de Riesgo en Cascada', value=label)
        st.write('Detalles del cálculo:')
        st.write(f'- Velocidad media: {velocidad_media} km/h')
        st.write(f'- Intensidad lluvia: {intensidad_lluvia} mm/h')
        st.write(f'- Ocupación tráfico: {ocupacion_transito} %')

# ----------------------- Pestaña 2: Chronos -----------------------
with tabs[1]:
    st.header('Chronos: Visión Estratégica 2040')
    st.write('Selecciona la estrategia para visualizar el futuro deseado y su defensa estratégica.')

    strategy = st.selectbox('Selector de Estrategia', ['Fortaleza Verde', 'Búnker Tecnológico'])
    col1, col2 = st.columns([1,1])

    strategy_images = {
        'Fortaleza Verde': 'assets/fortaleza_verde.jpg',
        'Búnker Tecnológico': 'assets/bunker_tecnologico.jpg'
    }

    descriptions = {
        'Fortaleza Verde': (
            'Defensa de la estrategia: Fortalecer la resiliencia urbana mediante infraestructura verde, ' 
            'sistemas de drenaje avanzados y políticas que reduzcan la huella de carbono. Esta visión protege ' 
            'activos y mejora la calidad de vida en Madrid, reduciendo exposición a riesgos climáticos.'
        ),
        'Búnker Tecnológico': (
            'Defensa de la estrategia: Inversión pesada en tecnología defensiva, automatización y redundancia ' 
            'digital. Construir capacidades para operar en entornos adversos y proteger las cadenas logísticas críticas.'
        )
    }

    with col1:
        img_path = strategy_images.get(strategy)
        if os.path.exists(img_path):
            st.image(img_path, caption=strategy, use_container_width=True)
        else:
            st.warning('Imagen no encontrada en assets/. Usa una imagen pre-generada para la demo.')
            st.info('Nombre esperado: ' + img_path)

    with col2:
        st.subheader('Argumento estratégico')
        st.write(descriptions[strategy])
        st.markdown('**Puntos clave a presentar a la Junta (30-60s):**')
        if strategy == 'Fortaleza Verde':
            st.write('- Reducción de riesgo climático a largo plazo\n- Beneficio social y de reputación\n- Coste inicial moderado vs retorno social')
        else:
            st.write('- Máxima protección de activos críticos\n- Requiere alta inversión en tecnología\n- Ventaja competitiva en contextos extremos')

# ----------------------- Pestaña 3: K-Lang -----------------------
with tabs[2]:
    st.header('K-Lang: Manual de Batalla Interactivo')
    st.write('Selector de Protocolos y Simulador en tiempo real')

    colA, colB = st.columns([1,1])
    with colA:
        st.subheader('Selector de Protocolos')
        protocol_choice = st.selectbox('Elegir protocolo', list(PROTOCOLS.keys()))
        p = PROTOCOLS[protocol_choice]
        st.markdown(f"**Ficha Técnica — {protocol_choice}**")
        st.write(f"**Disparador:** {p['trigger']}")
        st.write('**Secuencia de acciones:**')
        for i, a in enumerate(p['actions'], start=1):
            st.write(f"{i}. {a}")

    with colB:
        st.subheader('Simulador de Protocolos (sensores)')
        viento_kmh = st.slider('Velocidad del Viento (km/h)', min_value=0, max_value=200, value=30)
        nivel_inundacion_cm = st.slider('Nivel de Inundación (cm)', min_value=0, max_value=300, value=10)

        active_protocol, reason = determinar_protocolo(viento_kmh, nivel_inundacion_cm)

        st.markdown('## Estado del Protocolo')
        if active_protocol == 'CÓDIGO ROJO':
            st.markdown(f"<div style='background-color:#ff4d4d;padding:15px;border-radius:8px;color:white'><h2>PROTOCOLO ACTIVO: {active_protocol} — TITÁN</h2><p>{reason}</p></div>", unsafe_allow_html=True)
        elif active_protocol == 'VÍSPERA':
            st.markdown(f"<div style='background-color:#ffb84d;padding:12px;border-radius:8px;color:black'><h3>PROTOCOLO ACTIVO: {active_protocol}</h3><p>{reason}</p></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background-color:#b3ffb3;padding:12px;border-radius:8px;color:black'><h3>PROTOCOLO ACTIVO: {active_protocol}</h3><p>{reason}</p></div>", unsafe_allow_html=True)

        st.write('Acciones recomendadas (automáticas):')
        prot = PROTOCOLS[active_protocol]
        for a in prot['actions']:
            st.write('- ' + a)

# ----------------------- Pie / Detalles Técnicos -----------------------
st.markdown('---')
with st.expander('Arquitectura técnica (breve):'):
    st.write('- Frontend: Streamlit (una sola app Python para rapidez en War Room)')
    st.write('- Lógica/Modelo: funciones Python (Precog y heurísticas). Reemplazables por servicios ML/NoSQL.')
    st.write('- Datos: fuentes en tiempo real -> conectar APIs/sockets/streams para sensores; actualmente simulados con sliders.')
    st.write('- Despliegue sugerido: Streamlit Community Cloud o HuggingFace Spaces (Subir repo con requirements.txt y assets/).')

with st.expander('Checklist antes de la demo (rápida):'):
    st.write('- Reemplazar imágenes en assets/ por las versiones finales generadas por la GAN y el sistema de clustering.')
    st.write('- Probar la app localmente: streamlit run ChronoLogistics_Dashboard_streamlit.py')
    st.write('- Ensayar demo de 5 minutos: seguir el guion proporcionado abajo.')

st.markdown('---')

st.subheader('Guion de Demo — 5 minutos')
st.write('1) (1 min) Precog: Mostrar mapa, cambiar sliders de velocidad/lluvia y mostrar cómo cambia el nivel de riesgo en cascada.')
st.write('2) (1 min) Chronos: cambiar entre Fortalezca Verde / Búnker Tecnológico y presentar la defensa estratégica.')
st.write('3) (2 min) K-Lang: seleccionar protocolos, usar el simulador de sensores para provocar CÓDIGO ROJO y explicar acciones.')
st.write('4) (1 min) Explicar arquitectura y próximos pasos (conectar datos en tiempo real, pruebas de carga, roles en War Room).')

st.info('Archivo listo: ChronoLogistics_Dashboard_streamlit.py. Coloca imágenes en ./assets/ y ejecuta.')
