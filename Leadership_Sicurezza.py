import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Configuración de la página del Dashboard ---
st.set_page_config(layout="wide")
st.title("Dashboard sulla Leadership in Sicurezza")

# --- Función para cargar y preparar los datos ---
@st.cache_data # El caché acelera la carga al no tener que reprocesar el archivo
def load_and_prepare_data(path):
    """
    Carga el archivo CSV y calcula la columna 'age_group' para el filtrado.
    """
    try:
        df = pd.read_csv(path)
        
        # --- Cálculo de la edad y creación del grupo de edad ---
        def calcular_edad(fecha_nacimiento):
            try:
                fecha_nac = pd.to_datetime(fecha_nacimiento, errors='coerce')
                # --- INICIO DE LA CORRECCIÓN ---
                # Si la fecha es inválida, devolvemos un valor nulo en lugar de texto.
                if pd.isna(fecha_nac):
                    return None 
                
                hoy = datetime.now()
                edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                return edad
            except Exception:
                # Si ocurre cualquier otro error, también devolvemos un valor nulo.
                return None
                # --- FIN DE LA CORRECCIÓN ---

        df['age'] = df['birth_date'].apply(calcular_edad)
        
        # pd.cut ignorará automáticamente los valores nulos en la columna 'age'
        bins = [0, 30, 40, 50, 60, 100]
        labels = ['Meno di 30', '30-40', '41-50', '51-60', 'Più di 60']
        df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels, right=False)
        
        return df
    except FileNotFoundError:
        st.error(f"ERRORE: File non trovato al percorso: {path}")
        st.info("Assicurati che il file 'reporte_para_dashboard.csv' si trovi nella stessa cartella di questo script.")
        return None

# --- Cargar los datos ---
df = load_and_prepare_data("reporte_para_dashboard.csv")

if df is not None:
    # --- Detectar las columnas de competencias automáticamente ---
    columnas_demograficas = ['group', 'language', 'birth_date', 'sex', 'country', 'work_place', 'age', 'age_group']
    competencias = [col for col in df.columns if col not in columnas_demograficas]
    
    # --- Barra lateral con TODOS los filtros ---
    st.sidebar.header("Filtri")
    
    # Opciones para cada filtro, eliminando valores nulos o vacíos
    group_options = sorted(list(df['group'].dropna().unique()))
    language_options = list(df['language'].dropna().unique())
    age_group_options = list(df['age_group'].dropna().astype(str).unique()) # Convertimos a string para el filtro
    sex_options = list(df['sex'].dropna().unique())
    country_options = list(df['country'].dropna().unique())
    workplace_options = list(df['work_place'].dropna().unique())
    
    # Creación de los widgets de filtro
    selected_group = st.sidebar.multiselect("Gruppo", group_options, default=group_options)
    selected_language = st.sidebar.multiselect("Lingua", language_options, default=language_options)
    selected_age_group = st.sidebar.multiselect("Fascia d'età (Anni)", age_group_options, default=age_group_options)
    selected_sex = st.sidebar.multiselect("Sesso", sex_options, default=sex_options)
    selected_country = st.sidebar.multiselect("Paese", country_options, default=country_options)
    selected_workplace = st.sidebar.multiselect("Luogo di Lavoro", workplace_options, default=workplace_options)
    
    # --- Filtrar el DataFrame principal según la selección del usuario ---
    # Convertimos la columna 'age_group' del DataFrame a string para que la comparación funcione
    df['age_group'] = df['age_group'].astype(str)

    df_filtered = df[
        df['group'].isin(selected_group) &
        df['language'].isin(selected_language) &
        df['age_group'].isin(selected_age_group) &
        df['sex'].isin(selected_sex) &
        df['country'].isin(selected_country) &
        df['work_place'].isin(selected_workplace)
    ]

    # --- Mostrar los gráficos solo si hay datos después de filtrar ---
    if not df_filtered.empty:
        col1, col2 = st.columns([3, 1]) 

        with col1:
            st.subheader("Punteggio Medio per Competenza")
            avg_scores = df_filtered[competencias].mean().sort_values()
            
            fig_bar = px.bar(
                avg_scores, 
                x=avg_scores.values, 
                y=avg_scores.index, 
                orientation='h', 
                text_auto='.2s'
            )
            fig_bar.update_layout(showlegend=False, yaxis_title=None, xaxis_title="Punteggio Medio (0-100)")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("Partecipanti")
            st.metric("Totale Risposte Filtrate", len(df_filtered))
            
            st.subheader("Ripartizione per Ruolo")
            workplace_dist = df_filtered['work_place'].value_counts()
            fig_pie = px.pie(workplace_dist, values=workplace_dist.values, names=workplace_dist.index)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- Análisis Comparativo ---
        st.subheader("Analisi Comparativa per Luogo di Lavoro")
        df_comparison = df_filtered.groupby('work_place')[competencias].mean().reset_index()
        
        df_melted = df_comparison.melt(
            id_vars='work_place', 
            var_name='Competenza', 
            value_name='Punteggio Medio'
        )
        
        fig_grouped_bar = px.bar(
            df_melted,
            x="Competenza",
            y="Punteggio Medio",
            color="work_place",
            barmode="group",
            text_auto='.2s'
        )
        fig_grouped_bar.update_layout(xaxis_title=None)
        st.plotly_chart(fig_grouped_bar, use_container_width=True)
        
    else:
        st.warning("Nessun dato corrisponde ai filtri selezionati.")