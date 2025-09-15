import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image
import os
import pandas as pd
import plotly.graph_objects as go # type: ignore

st.set_page_config(page_title="ChronoLogistics - Dashboard Operativo", layout="wide")

# ----------------------- Precog: Lógica y Funciones -----------------------
class Precog:
    def predecir_riesgo(self, velocidad_media, intensidad_lluvia, ocupacion_transito):
        v = np.clip(velocidad_media / 150.0, 0, 1)
        r = np.clip(intensidad_lluvia / 200.0, 0, 1)
        t = np.clip(ocupacion_transito / 100.0, 0, 1)
        score = 0.5 * v + 0.35 * r + 0.15 * t
        extreme = 0
        if velocidad_media > 100:
            extreme += 0.12 * ((velocidad_media - 100) / 50)
        if intensidad_lluvia > 120:
            extreme += 0.12 * ((intensidad_lluvia - 120) / 80)
        final = np.clip((score + extreme) * 100, 0, 100)
        return float(final)

PREC = Precog()

def riesgo_label(score):
    if score < 30:
        return f"{score:.0f}% - BAJO", "green"
    elif score < 60:
        return f"{score:.0f}% - MEDIO", "orange"
    else:
        return f"{score:.0f}% - ALTO", "red"

# ----------------------- K-Lang Protocolos -----------------------
PROTOCOLS = {
    'VÍSPERA': {'trigger': 'Condiciones pre-alerta', 'actions': ['Activar patrullas', 'Preparar refugios', 'Notificar stakeholders']},
    'CÓDIGO ROJO': {'trigger': 'Evento extremo', 'actions': ['Evacuación inmediata', 'Corte suministro', 'Activar TITÁN']},
    'RENACIMIENTO': {'trigger': 'Post-evento', 'actions': ['Evaluación daños', 'Plan reconstrucción', 'Revisar protocolos']}
}

def determinar_protocolo(viento_kmh, nivel_inundacion_cm):
    if viento_kmh >= 95 or nivel_inundacion_cm >= 80:
        return 'CÓDIGO ROJO', 'Viento >= 95 km/h o Inundación >= 80 cm'
    if viento_kmh >= 40 or nivel_inundacion_cm >= 30:
        return 'VÍSPERA', 'Condiciones de pre-alerta'
    return 'RENACIMIENTO', 'Condición normal / post-evento'

# ----------------------- Mapa de calor sobre Madrid -----------------------
def generar_mapa_clusters_sobre_madrid(velocidad, lluvia, transito):
    np.random.seed(42)
    num_puntos = int(400 + velocidad*2 + lluvia*1.5 + transito*2)
    spread = max(2, 15 - velocidad/20)
    center_shift = velocidad/10
    clusters = [[30+center_shift,30+center_shift],[70-center_shift,40+center_shift],[50+center_shift,70-center_shift],[80-center_shift,80+center_shift]]
    x_list = []
    for cx, cy in clusters:
        pts = np.random.normal(loc=[cx, cy], scale=spread, size=(int(num_puntos/len(clusters)), 2))
        x_list.append(pts)
    x = np.concatenate(x_list)
    heat, _, _ = np.histogram2d(x[:,0], x[:,1], bins=80, range=[[0,100],[0,100]])
    heat = np.rot90(heat)
    heat = np.flipud(heat)

    cmap = mcolors.LinearSegmentedColormap.from_list("riesgo", ["black","green","yellow","red","darkred"])

    fondo_path = 'assets/madrid_map.png'
    if os.path.exists(fondo_path):
        fondo_img = np.array(Image.open(fondo_path))
    else:
        st.warning("No se encuentra el mapa de Madrid en assets/. Usando fondo blanco.")
        fondo_img = np.ones((800,800,3))

    fig, ax = plt.subplots(figsize=(6,6))
    ax.imshow(fondo_img, extent=[0,100,0,100], origin='upper')
    ax.imshow(heat, extent=[0,100,0,100], origin='lower', cmap=cmap, alpha=0.6, vmin=0, vmax=np.max(heat))

    # Triángulo del Peligro: conectar los 3 clústeres más críticos
    criticos = np.array(clusters[:3])
    cx = np.append(criticos[:,0], criticos[0,0])
    cy = np.append(criticos[:,1], criticos[0,1])
    ax.plot(cx, cy, color='cyan', linewidth=2, linestyle='--')
    ax.scatter(criticos[:,0], criticos[:,1], color='cyan', s=50)

    ax.set_title('Mapa de Calor Dinámico sobre Madrid')
    ax.set_xlabel('Longitud (simulada)')
    ax.set_ylabel('Latitud (simulada)')
    plt.colorbar(ax.images[-1], ax=ax, fraction=0.046, pad=0.04)
    st.pyplot(fig)
    plt.close(fig)

# ----------------------- UI -----------------------
header_placeholder = st.empty()
header_placeholder.markdown('<h2 style="text-align:center">ChronoLogistics — Dashboard Operativo</h2>', unsafe_allow_html=True)

tabs = st.tabs([
    "Precog: Monitor de Riesgo Táctico",
    "Chronos: Visión Estratégica 2040",
    "K-Lang: Manual de Batalla Interactivo",
    "Hydra: Registro de Alertas"
])

# Pestaña 1: Precog
with tabs[0]:
    st.header('Precog: Monitor de Riesgo Táctico')
    col1,col2 = st.columns([2,1])
    with col2:
        velocidad_media = st.slider('Velocidad media (km/h)',0,160,60)
        intensidad_lluvia = st.slider('Intensidad lluvia (mm/h)',0,300,20)
        ocupacion_transito = st.slider('Ocupación tráfico (%)',0,100,45)
        score = PREC.predecir_riesgo(velocidad_media,intensidad_lluvia,ocupacion_transito)
        label,color = riesgo_label(score)
        st.metric('Nivel de Riesgo en Cascada', label)

        # Barra de contribuciones
        data = pd.DataFrame({'Factor':['Velocidad','Lluvia','Tráfico'],'Contribución':[velocidad_media,intensidad_lluvia,ocupacion_transito]})
        st.subheader('Contribución de factores al riesgo')
        st.bar_chart(data.set_index('Factor'))

        # Gauge de riesgo
        fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text':'Nivel de Riesgo (%)'},
                                           gauge={'axis':{'range':[None,100]},'bar':{'color':'red'},
                                                  'steps':[{'range':[0,30],'color':'green'},{'range':[30,60],'color':'yellow'},{'range':[60,100],'color':'red'}]}))
        st.plotly_chart(fig_gauge)

        # Historial y descarga de riesgo
        if 'risk_history' not in st.session_state:
            st.session_state['risk_history'] = []

        if st.button('Guardar medición'):
            st.session_state['risk_history'].append({'time': pd.Timestamp.now(), 'riesgo': score})

        if st.session_state['risk_history']:
            hist_df = pd.DataFrame(st.session_state['risk_history'])
            hist_df['time'] = hist_df['time'].dt.strftime('%H:%M:%S')
            st.subheader('Historial de riesgo')
            st.line_chart(hist_df.set_index('time')['riesgo'])
            st.download_button('Descargar historial CSV', hist_df.to_csv(index=False), file_name='historial_riesgo.csv')

    with col1:
        generar_mapa_clusters_sobre_madrid(velocidad_media,intensidad_lluvia,ocupacion_transito)

# Pestaña 2: Chronos
with tabs[1]:
    st.header('Chronos: Visión Estratégica 2040')
    strategy = st.selectbox('Selector de Estrategia',['Fortaleza Verde','Búnker Tecnológico'])
    col1,col2 = st.columns([1,1])
    strategy_images = {'Fortaleza Verde':'assets/fortaleza_verde.jpg','Búnker Tecnológico':'assets/bunker_tecnologico.jpg'}
    descriptions = {'Fortaleza Verde':'Fortalecer resiliencia urbana mediante infraestructura verde, drenaje y políticas sostenibles.',
                    'Búnker Tecnológico':'Invertir en tecnología defensiva, automatización y redundancia digital para proteger activos críticos.'}
    with col1:
        img_path = strategy_images.get(strategy)
        if os.path.exists(img_path): st.image(img_path, caption=strategy, use_container_width=True)
        else: st.warning('Imagen no encontrada en assets/.')
    with col2:
        st.subheader('Argumento estratégico')
        st.write(descriptions[strategy])

# Pestaña 3: K-Lang
with tabs[2]:
    st.header('K-Lang: Manual de Batalla Interactivo')
    colA,colB = st.columns([1,1])
    with colA:
        protocol_choice = st.selectbox('Elegir protocolo',list(PROTOCOLS.keys()))
        p = PROTOCOLS[protocol_choice]
        st.markdown(f"**Ficha Técnica — {protocol_choice}**")
        st.write(f"**Disparador:** {p['trigger']}")
        st.write('**Secuencia de acciones:**')
        for i,a in enumerate(p['actions'],1): st.write(f"{i}. {a}")

    with colB:
        viento_kmh = st.slider('Velocidad del Viento (km/h)',0,200,30)
        nivel_inundacion_cm = st.slider('Nivel de Inundación (cm)',0,300,10)
        active_protocol, reason = determinar_protocolo(viento_kmh,nivel_inundacion_cm)

        # Indicador principal del protocolo activo
        colores = {'CÓDIGO ROJO':'#ff4d4d','VÍSPERA':'#ffa500','RENACIMIENTO':'#4caf50'}
        color_box = colores.get(active_protocol,'#d9d9d9')
        st.markdown(
            f"<div style='padding:15px;border-radius:10px;background-color:{color_box};text-align:center;color:white'>"
            f"<h3>PROTOCOLO ACTIVO: {active_protocol}</h3><p>{reason}</p></div>",
            unsafe_allow_html=True)

        # Semáforo visual de protocolos
        st.subheader('Estado de Protocolos')
        for proto in PROTOCOLS.keys():
            color = '#ff4d4d' if proto==active_protocol else '#d9d9d9'
            st.markdown(f"<div style='width:150px;height:50px;background-color:{color};text-align:center;padding:10px;border-radius:10px;color:white'>{proto}</div>", unsafe_allow_html=True)

        # Gauge de riesgo ambiental
        fig_env = go.Figure(go.Indicator(mode="gauge+number", value=viento_kmh, title={'text':'Viento (km/h)'},
                                        gauge={'axis':{'range':[0,200]},'bar':{'color':'blue'},'steps':[{'range':[0,95],'color':'green'},{'range':[95,150],'color':'yellow'},{'range':[150,200],'color':'red'}]}))
        st.plotly_chart(fig_env)

        fig_flood = go.Figure(go.Indicator(mode="gauge+number", value=nivel_inundacion_cm, title={'text':'Nivel Inundación (cm)'},
                                          gauge={'axis':{'range':[0,300]},'bar':{'color':'blue'},'steps':[{'range':[0,80],'color':'green'},{'range':[80,200],'color':'yellow'},{'range':[200,300],'color':'red'}]}))
        st.plotly_chart(fig_flood)

        st.write('Acciones recomendadas:')
        for a in PROTOCOLS[active_protocol]['actions']: st.write('- '+a)

# Pestaña 4: Hydra
with tabs[3]:
    st.header('Hydra: Registro de Alertas')
    if 'alert_log' not in st.session_state:
        st.session_state['alert_log'] = []

    desc = st.text_input('Descripción del incidente')
    severity = st.selectbox('Severidad', ['Baja', 'Media', 'Alta'])
    if st.button('Añadir alerta') and desc:
        st.session_state.alert_log.append({'time': pd.Timestamp.now(), 'descripcion': desc, 'severidad': severity})

    if st.session_state.alert_log:
        df_alert = pd.DataFrame(st.session_state.alert_log)
        st.subheader('Historial de alertas')
        st.dataframe(df_alert)
        st.bar_chart(df_alert['severidad'].value_counts())
        st.download_button('Descargar alertas CSV', df_alert.to_csv(index=False), file_name='alertas.csv')

st.markdown('---')
#st.info('Archivo listo. Coloca las imágenes en assets/ y ejecuta con streamlit run <archivo>.py')
