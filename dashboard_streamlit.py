# Dashboard de Inteligencia de Negocio: Predicción de Cultivo Óptimo basado en Condiciones
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split 
import warnings
import altair as alt 
warnings.filterwarnings('ignore') 

# --- CONFIGURACIÓN Y CONSTANTES ---

EXCEL_FILENAME = "crop_recommendation_unida_corregida.xlsx"

# Límites de seguridad para los widgets de Streamlit y limpieza de datos (Solución a errores)
MAX_WIDGET_N = 200.0
MAX_WIDGET_P = 200.0
MAX_WIDGET_K = 250.0
MAX_WIDGET_TEMP = 50.0      # Límite realista para T° (soluciona error 99.499)
MAX_WIDGET_RAIN = 300.0     # Límite del widget para Precipitación (soluciona error 999.834)
MAX_WIDGET_PH = 14.0
MAX_WIDGET_HUM = 100.0

# --- CACHE DE DATOS Y MODELO ---

@st.cache_data
def load_and_preprocess_data_for_crop_prediction():
    """Carga, limpia y prepara el dataset enfocándose en PREDECIR EL CULTIVO."""
    try:
        df = pd.read_excel(EXCEL_FILENAME)
        
        # 1. Normalizar nombres de columnas
        df.columns = [col.lower().replace('.', '').replace('/', '_').replace('-', '_').strip() for col in df.columns]
        
        # 2. Definir Features
        feature_cols = ['n', 'p', 'k', 'temperature', 'rainfall', 'humidity', 'ph']
        
        # 3. Limpieza y Relleno de Datos (Conversión a numérico y llenado de nulos con la media)
        for col in feature_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col].fillna(df[col].mean(), inplace=True)
        
        # 4. TRATAMIENTO DE OUTLIERS (SOLUCIÓN DEFINITIVA A STREAMLIT ERRORS)
        # Aseguramos que los valores máximos históricos no superen los límites de los widgets.
        if 'temperature' in df.columns:
            df.loc[df['temperature'] > MAX_WIDGET_TEMP, 'temperature'] = MAX_WIDGET_TEMP
        
        if 'rainfall' in df.columns:
            df.loc[df['rainfall'] > MAX_WIDGET_RAIN, 'rainfall'] = MAX_WIDGET_RAIN
                
        # 5. Definir Target y Codificación
        df['crop'].fillna('desconocido', inplace=True)
        le_crop = LabelEncoder()
        df['crop_encoded'] = le_crop.fit_transform(df['crop'])
        
        df.dropna(subset=feature_cols + ['crop_encoded'], inplace=True)

        return df, le_crop
    
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo {EXCEL_FILENAME}. Colócalo en la misma carpeta.")
        st.stop()
    except Exception as e:
        st.error(f"Error al cargar o preprocesar los datos: {e}")
        st.stop()

@st.cache_data
def train_crop_model(df):
    """Entrena el modelo usando condiciones de suelo y clima para predecir el CULTIVO ÓPTIMO."""
    
    X_features = ['n', 'p', 'k', 'temperature', 'rainfall', 'humidity', 'ph']
    X = df[X_features]
    y = df['crop_encoded']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = RandomForestClassifier(n_estimators=150, random_state=42, max_depth=15, class_weight='balanced')
    model.fit(X_train, y_train)
    return model, X_features

# --- FUNCIÓN DE VISUALIZACIÓN ---

def create_pareto_chart(df_results):
    """Crea un Diagrama de Pareto con Altair."""
    
    # Calcular el Porcentaje Acumulado
    df_results['Probabilidad_Normalizada'] = df_results['Probabilidad (%)'] / 100
    df_results['Acumulado'] = df_results['Probabilidad_Normalizada'].cumsum()
    
    # 1. Gráfico de Barras (Probabilidad Individual)
    bar_chart = alt.Chart(df_results).mark_bar().encode(
        x=alt.X('Cultivo:N', sort='-y', title='Cultivo Candidato'), 
        y=alt.Y('Probabilidad_Normalizada', axis=alt.Axis(format='%', title='Probabilidad Individual')),
        tooltip=['Cultivo', alt.Tooltip('Probabilidad_Normalizada', format='.1%')],
        color=alt.value('#1f77b4') 
    ).properties(
        title="Diagrama de Pareto de Cultivos Óptimos por Probabilidad"
    )

    # 2. Gráfico de Línea (Probabilidad Acumulada)
    line_chart = alt.Chart(df_results).mark_line(point=True, color='red').encode(
        x=alt.X('Cultivo:N', sort='-y'), 
        y=alt.Y('Acumulado', axis=alt.Axis(format='%', title='Probabilidad Acumulada')),
        tooltip=['Cultivo', alt.Tooltip('Acumulado', format='.1%')]
    )
    
    # 3. Combinar y mostrar
    chart = alt.layer(bar_chart, line_chart).resolve_scale(
        y='independent' 
    ).configure_axis(
        labelFontSize=10, titleFontSize=12
    ).configure_title(
        fontSize=14
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


# --- FUNCIÓN PRINCIPAL DE LA APLICACIÓN ---

def app():
    st.set_page_config(page_title="Dashboard de Cultivos Óptimos", layout="wide")
    st.title("🌾 Dashboard Inteligente: Selección de Cultivo Óptimo")
    st.markdown("Ingresa los **rangos** de tus condiciones de suelo y clima. El sistema predice los cultivos más adecuados para ese ambiente.")

    # Cargar datos y entrenar el modelo
    df, le_crop = load_and_preprocess_data_for_crop_prediction()
    model, features = train_crop_model(df)
    
    # Obtener los rangos min/max de los datos históricos (ya limpios)
    min_max_values = df[features].agg(['min', 'max']).T.to_dict('index')

    # ----------------------------------------------------------------------
    # 1. ENTRADA DE PARÁMETROS (Sidebar)
    # ----------------------------------------------------------------------
    st.sidebar.header("🎛️ Ingresa los Rangos de Condiciones")
    
    st.sidebar.subheader("🔬 Condiciones del Suelo")
    
    col_n, col_p = st.sidebar.columns(2)
    with col_n:
        n_min = st.number_input("Nitrógeno (N) Mín.", min_value=0.0, max_value=MAX_WIDGET_N, value=min_max_values['n']['min'], step=1.0)
        n_max = st.number_input("Nitrógeno (N) Máx.", min_value=n_min, max_value=MAX_WIDGET_N, value=min_max_values['n']['max'], step=1.0)
    with col_p:
        p_min = st.number_input("Fósforo (P) Mín.", min_value=0.0, max_value=MAX_WIDGET_P, value=min_max_values['p']['min'], step=1.0)
        p_max = st.number_input("Fósforo (P) Máx.", min_value=p_min, max_value=MAX_WIDGET_P, value=min_max_values['p']['max'], step=1.0)
    
    col_k, col_ph = st.sidebar.columns(2)
    with col_k:
        k_min = st.number_input("Potasio (K) Mín.", min_value=0.0, max_value=MAX_WIDGET_K, value=min_max_values['k']['min'], step=1.0)
        k_max = st.number_input("Potasio (K) Máx.", min_value=k_min, max_value=MAX_WIDGET_K, value=min_max_values['k']['max'], step=1.0)
    with col_ph:
        ph_min = st.number_input("pH Mín.", min_value=0.0, max_value=MAX_WIDGET_PH, value=min_max_values['ph']['min'], step=0.1)
        ph_max = st.number_input("pH Máx.", min_value=ph_min, max_value=MAX_WIDGET_PH, value=min_max_values['ph']['max'], step=0.1)

    st.sidebar.subheader("☁️ Condiciones Climáticas")

    col_t, col_h = st.sidebar.columns(2)
    with col_t:
        temp_min = st.number_input("Temp. Mín. (°C)", min_value=0.0, max_value=MAX_WIDGET_TEMP, value=min_max_values['temperature']['min'], step=0.5)
        temp_max = st.number_input("Temp. Máx. (°C)", min_value=temp_min, max_value=MAX_WIDGET_TEMP, value=min_max_values['temperature']['max'], step=0.5)
    with col_h:
        hum_min = st.number_input("Humedad Mín. (%)", min_value=0.0, max_value=MAX_WIDGET_HUM, value=min_max_values['humidity']['min'], step=1.0)
        hum_max = st.number_input("Humedad Máx. (%)", min_value=hum_min, max_value=MAX_WIDGET_HUM, value=min_max_values['humidity']['max'], step=1.0)
        
    prec_min = st.sidebar.number_input("Precipitación Mín. (mm)", min_value=0.0, max_value=MAX_WIDGET_RAIN, value=min_max_values['rainfall']['min'], step=1.0)
    prec_max = st.sidebar.number_input("Precipitación Máx. (mm)", min_value=prec_min, max_value=MAX_WIDGET_RAIN, value=min_max_values['rainfall']['max'], step=1.0)

    # ----------------------------------------------------------------------
    # 2. PROCESAMIENTO Y PREDICCIÓN
    # ----------------------------------------------------------------------
    
    st.header("🎯 Resultados del Análisis Integrado")
    
    # Calculamos los promedios para alimentar al modelo
    input_n = (n_min + n_max) / 2
    input_p = (p_min + p_max) / 2
    input_k = (k_min + k_max) / 2
    input_ph = (ph_min + ph_max) / 2
    input_temp = (temp_min + temp_max) / 2
    input_hum = (hum_min + hum_max) / 2
    input_prec = (prec_min + prec_max) / 2

    input_conditions = pd.DataFrame([[
        input_n, input_p, input_k, input_temp, input_prec, input_hum, input_ph
    ]], columns=features)
    
    # Predicción de probabilidad
    probas = model.predict_proba(input_conditions)[0]
    
    # Obtener el Top 10 de cultivos
    N_TOP = 10
    top_indices = np.argsort(probas)[::-1][:N_TOP]
    top_probas = probas[top_indices]
    top_crops_encoded = le_crop.inverse_transform(top_indices)
    
    # ----------------------------------------------------------------------
    # 3. VISUALIZACIÓN Y ANÁLISIS
    # ----------------------------------------------------------------------

    # A. Métrica Principal
    predicted_crop = top_crops_encoded[0].upper()
    predicted_proba = top_probas[0] * 100
    
    st.metric(
        label="🏆 Cultivo Principal Óptimo", 
        value=predicted_crop, 
        delta=f"Probabilidad de Éxito: {predicted_proba:.1f}%",
        delta_color="normal"
    )
    
    st.markdown("---")

    # B. Gráfico de Pareto de Alternativas
    st.subheader("📈 Cultivos Alternativos y Análisis de Pareto (Top 10)")
    
    top_results = pd.DataFrame({
        "Cultivo": top_crops_encoded,
        "Probabilidad (%)": top_probas * 100
    }).sort_values(by="Probabilidad (%)", ascending=False).reset_index(drop=True)
    
    create_pareto_chart(top_results.copy())
    
    # C. Detalle de la Tabla
    st.markdown("##### Detalle de las Probabilidades")
    top_results_display = top_results.drop(columns=['Probabilidad_Normalizada', 'Acumulado'], errors='ignore')
    st.dataframe(top_results_display.style.format({'Probabilidad (%)': "{:.1f}%"}), use_container_width=True)

    # D. Explicación
    st.markdown(
        """
        ---
        **Nota:** recuerden muchachos que los rangos de datos atípicos (como T° > 50°C o Precipitación > 300mm) en el dataset original 
        fueron limitados a valores más realistas para garantizar la estabilidad del simulador. 
        El **Diagrama de Pareto** le permite aplicar el **Principio 80/20** para enfocarse en los cultivos 
        con mayor probabilidad de éxito dada la combinación de condiciones ingresadas.
        """
    )


if __name__ == '__main__':
    app()
# para poner a correr el streamlit en la terminal:  python -m streamlit run dashboard_cultivos_optimizado.py