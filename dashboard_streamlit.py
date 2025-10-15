# Prediccion de Zona de Vida y Departamento Optimos basado en NPK y Temperatura Futura.
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
import altair as alt # <-- Importamos altair para el gráfico
warnings.filterwarnings('ignore') 

# --- Configuración Inicial y Cache de Datos/Modelo ---

EXCEL_FILENAME = "crop_recommendation_unida_corregida.xlsx"

@st.cache_data
def load_and_preprocess_data():
    """Carga, limpia y prepara TODAS las variables para el entrenamiento."""
    try:
        df = pd.read_excel(EXCEL_FILENAME)
        df.columns = [col.lower().replace('.', '').replace('/', '_').replace('-', '_').strip() for col in df.columns]
        
        # Combinar departamento y zona_vida en una sola variable objetivo para predicción
        df['target_location'] = df['departamento_colombia'] + " | " + df['zona_vida']
        
        # Limpieza de columnas clave
        df['departamento_colombia'].fillna('desconocido', inplace=True)
        
        # Lista de columnas numéricas a limpiar y rellenar con la media
        # INCLUIMOS N, P, K y las 3 variables de temperatura para el modelo.
        numeric_cols = ['n', 'p', 'k', 'temperature', 'temperature_min', 'temperature_max',
                        'rainfall', 'humidity', 'ph']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col].fillna(df[col].mean(), inplace=True)
            
        # Codificación (Label Encoding) de Cultivo y Ubicación (Target)
        le_crop = LabelEncoder()
        df['crop_encoded'] = le_crop.fit_transform(df['crop'])
        le_target = LabelEncoder()
        df['target_encoded'] = le_target.fit_transform(df['target_location'])
        
        return df, le_crop, le_target
    
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo {EXCEL_FILENAME}. Colócalo en la misma carpeta.")
        st.stop()
    except Exception as e:
        st.error(f"Error al cargar o preprocesar los datos: {e}")
        st.stop()

@st.cache_data
def train_complex_model(df):
    """Entrena el modelo usando N, P, K, y las tres variables de temperatura para predecir la UBICACIÓN ÓPTIMA."""
    
    # 7 Features de entrada: N, P, K, temperatura (media), t_min, t_max, y crop_encoded
    X = df[['n', 'p', 'k', 'temperature', 'temperature_min', 'temperature_max', 'crop_encoded']]
    y = df['target_encoded']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = RandomForestClassifier(n_estimators=150, random_state=42, max_depth=15)
    model.fit(X_train, y_train)
    return model, X

# --- Función para crear el Diagrama de Pareto (NUEVO) ---

def create_pareto_chart(df_results_chart):
    """
    Crea un Diagrama de Pareto usando Altair a partir de los resultados Top-N.
    """
    # 1. Calcular el Porcentaje Acumulado
    # Aseguramos que la columna de probabilidad esté como float
    df_results_chart['Probabilidad (%)'] = df_results_chart['Probabilidad (%)'].astype(float)
    df_results_chart['Probabilidad_Normalizada'] = df_results_chart['Probabilidad (%)'] / 100
    df_results_chart['Acumulado'] = df_results_chart['Probabilidad_Normalizada'].cumsum()
    
    # 2. Gráfico de Barras (Probabilidad Individual)
    bar_chart = alt.Chart(df_results_chart).mark_bar().encode(
        # La concatenación hace que la etiqueta sea más descriptiva en el eje X
        x=alt.X('Ubicacion:N', sort='-y', title='Ubicación (Dpto | Zona)'), 
        y=alt.Y('Probabilidad_Normalizada', axis=alt.Axis(format='%', title='Probabilidad Individual')),
        tooltip=['Ubicacion', alt.Tooltip('Probabilidad_Normalizada', format='.1%')],
        color=alt.value('#1f77b4') # Color de las barras (azul)
    ).properties(
        title="Diagrama de Pareto de Ubicaciones Alternativas (Probabilidad)"
    )

    # 3. Gráfico de Línea (Probabilidad Acumulada)
    line_chart = alt.Chart(df_results_chart).mark_line(point=True, color='red').encode(
        x=alt.X('Ubicacion:N', sort='-y'), # Mismo orden de barras
        y=alt.Y('Acumulado', axis=alt.Axis(format='%', title='Probabilidad Acumulada')),
        tooltip=['Ubicacion', alt.Tooltip('Acumulado', format='.1%')]
    )
    
    # 4. Combinar ambos gráficos y personalizar
    chart = alt.layer(bar_chart, line_chart).resolve_scale(
        y='independent' # Permite que cada eje Y tenga su propia escala
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

# --- Función Principal de la Aplicación ---

def app():
    st.set_page_config(page_title="Simulador Multi-Variable Futuro", layout="wide")
    st.title("🌱 Simulador Multi-Variable de Futura Ubicación (NPK + Temperatura)")
    st.markdown("Predice la **Zona de Vida** y el **Departamento** óptimos si cambian los requerimientos de nutrientes y temperatura de un cultivo.")

    # Cargar datos y entrenar el modelo
    df, le_crop, le_target = load_and_preprocess_data()
    model, X = train_complex_model(df)
    
    # Obtener opciones para los widgets
    crop_options = sorted(le_crop.classes_)
    
    st.sidebar.header("⚙️ Configuración del Escenario FUTURO")
    
    # --- 1. Entrada del Cultivo ---
    current_crop_name = st.sidebar.selectbox(
        "Elige el CULTIVO:",
        options=crop_options
    )
    current_crop_encoded = le_crop.transform([current_crop_name])[0]

    # Obtenemos las variables promedio de ese cultivo como punto de partida
    base_data_crop = df[df['crop'] == current_crop_name]
    
    if base_data_crop.empty:
        st.error(f"No hay datos suficientes para {current_crop_name}. Por favor, elige otro cultivo.")
        st.stop()
        
    # Variables Base (Promedio de todos los departamentos para ese cultivo)
    N_base = base_data_crop['n'].mean()
    P_base = base_data_crop['p'].mean()
    K_base = base_data_crop['k'].mean()
    T_avg_base = base_data_crop['temperature'].mean()
    T_min_base = base_data_crop['temperature_min'].mean()
    T_max_base = base_data_crop['temperature_max'].mean()
    
    # --- 2. Sliders para N, P, K (Entrada Futura) ---
    st.sidebar.subheader("Requerimientos de Nutrientes (N, P, K)")
    N_future = st.sidebar.slider("Nitrógeno (N)", 
                                 min_value=0.0, max_value=200.0, 
                                 value=N_base, step=1.0)
    P_future = st.sidebar.slider("Fósforo (P)", 
                                 min_value=0.0, max_value=200.0, 
                                 value=P_base, step=1.0)
    K_future = st.sidebar.slider("Potasio (K)", 
                                 min_value=0.0, max_value=250.0, 
                                 value=K_base, step=1.0)

    # --- 3. Sliders para Temperaturas (Entrada Futura) ---
    st.sidebar.subheader("Requerimientos de Temperatura (°C)")
    T_min_future = st.sidebar.slider("T° Mínima (Futura)", 
                                     min_value=T_min_base - 5, max_value=T_max_base + 10, 
                                     value=T_min_base + 2, step=0.1)
    T_max_future = st.sidebar.slider("T° Máxima (Futura)", 
                                     min_value=T_min_base - 5, max_value=T_max_base + 10, 
                                     value=T_max_base + 2, step=0.1)
    # Temperatura Media (simplemente el promedio de min/max para este modelo)
    T_avg_future = (T_min_future + T_max_future) / 2
    
    
    # --- 4. Realizar Predicción Compleja ---
    
    future_conditions = pd.DataFrame([[
        N_future, P_future, K_future, T_avg_future, T_min_future, T_max_future, current_crop_encoded
    ]], columns=X.columns)
    
    # Predicción de la etiqueta de ubicación
    predicted_label_new = model.predict(future_conditions)[0]
    predicted_target_location = le_target.inverse_transform([predicted_label_new])[0]
    
    # Separar Departamento y Zona de Vida
    predicted_dept, predicted_zona = predicted_target_location.split(' | ')
    
    # Probabilidad de las 5 mejores predicciones
    probas = model.predict_proba(future_conditions)[0]
    top_5_indices = np.argsort(probas)[::-1][:5]
    top_5_probas = probas[top_5_indices]
    top_5_targets = le_target.inverse_transform(top_5_indices)
    
    
    # --- 5. Mostrar Resultados ---
    
    st.header(f"➡️ Predicción de la Mejor Ubicación Futura para {current_crop_name.upper()}")
    st.subheader(f"Basado en NPK ({N_future:.0f}, {P_future:.0f}, {K_future:.0f}) y T° ({T_min_future:.1f}°C - {T_max_future:.1f}°C)")

    col1, col2 = st.columns(2)
    
    col1.metric("🏅 Departamento Óptimo Futuro", predicted_dept.upper(), 
                delta=f"Probabilidad de Éxito: {top_5_probas[0]*100:.1f}%")
    
    col2.metric("🌳 Zona de Vida Óptima", predicted_zona.upper())
    
    
    st.markdown("---")

    # --- 6. Mostrar Top 5 Ubicaciones Alternativas y Diagrama de Pareto ---
    
    st.subheader("📊 Top 5 Ubicaciones Alternativas")
    
    top_results = []
    
    # Usamos 'enumerate' para obtener el índice (posicion) y el valor (target, proba)
    for index, (target, proba) in enumerate(zip(top_5_targets, top_5_probas)):
        # Separar Departamento y Zona de Vida
        dept, zona = target.split(' | ')
        
        # DataFrame para la tabla
        top_results.append({
            "Posición": index + 1,
            "Departamento": dept.upper(),
            "Zona de Vida": zona.upper(),
            "Probabilidad (%)": f"{proba*100:.1f}",
            "Ubicacion": f"{dept.upper()} | {zona.upper()}" # Columna extra para el gráfico
        })
        
    df_results = pd.DataFrame(top_results)
    
    # Mostramos el Diagrama de Pareto (usamos todo el Top 5)
    st.markdown("##### Visualización de la Distribución de Probabilidad (Diagrama de Pareto)")
    create_pareto_chart(df_results.copy()) # Usamos una copia para el gráfico
    
    # Mostramos la tabla (quitando el resultado principal)
    st.markdown("##### Detalle de las Ubicaciones")
    # Convertimos la columna de Probabilidad a float para ordenarla, pero la mostramos formateada
    df_display = df_results.copy()
    df_display['Probabilidad (%)'] = df_display['Probabilidad (%)'].astype(float)
    
    st.dataframe(df_display[['Posición', 'Departamento', 'Zona de Vida', 'Probabilidad (%)']].set_index('Posición').style.format({'Probabilidad (%)': "{:.1f}%"}))

    st.markdown(
        """
        **Explicación:** El modelo busca la combinación histórica de N, P, K, T-min y T-max que mejor coincida 
        con tus escenarios futuros simulados, prediciendo la ubicación (Departamento y Zona de Vida) donde ese 
        conjunto de condiciones es más común.
        """
    )


if __name__ == '__main__':
    app()
