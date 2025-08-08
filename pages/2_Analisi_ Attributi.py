import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Analisi delle Qualità di Leadership Selezionate")

# --- Función para cargar y preparar los datos ---
@st.cache_data
def load_qualities_data(path):
    """
    Carga el JSON de la encuesta de cualidades y lo "expande" para
    que cada cualidad seleccionada tenga su propia fila.
    """
    try:
        df = pd.read_json(path)
        # La función 'explode' es la clave aquí: transforma la lista de cualidades
        # en filas individuales, duplicando los datos demográficos.
        return df.explode('qualities')
    except Exception as e:
        st.error(f"ERRORE nel caricamento del file JSON '{path}': {e}")
        return None

# --- Cargar los datos ---
df_qualities = load_qualities_data("qualities_survey.json")

if df_qualities is not None:
    # --- Barra lateral con los filtros ---
    st.sidebar.header("Filtri")
    
    # Opciones para cada filtro
    workplace_options = list(df_qualities['mainWorkplace'].dropna().unique())
    country_options = list(df_qualities['country'].dropna().unique())
    gender_options = list(df_qualities['gender'].dropna().unique())
    
    # Creación de los widgets de filtro
    selected_workplace = st.sidebar.multiselect("Luogo di Lavoro", workplace_options, default=workplace_options)
    selected_country = st.sidebar.multiselect("Paese", country_options, default=country_options)
    selected_gender = st.sidebar.multiselect("Sesso", gender_options, default=gender_options)

    # --- Filtrar el DataFrame principal ---
    df_filtered = df_qualities[
        df_qualities['mainWorkplace'].isin(selected_workplace) &
        df_qualities['country'].isin(selected_country) &
        df_qualities['gender'].isin(selected_gender)
    ]

    if not df_filtered.empty:
        # --- KPIs y Gráfico Principal ---
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Metriche Principali")
            # Usamos len(df_filtered['id'].unique()) para contar personas, no respuestas
            total_participants = len(df_filtered['id'].unique())
            st.metric("Totale Partecipanti Filtrati", total_participants)
            
            quality_counts = df_filtered['qualities'].value_counts()
            top_quality = quality_counts.index[0]
            st.metric("Qualità Più Selezionata", top_quality.capitalize())

        with col2:
            st.subheader("Top 15 Qualità Selezionate (Generale)")
            # Tomamos el top 15 de las cualidades más seleccionadas
            top_15_qualities = quality_counts.head(15).sort_values()
            
            fig_bar = px.bar(
                top_15_qualities,
                x=top_15_qualities.values,
                y=top_15_qualities.index,
                orientation='h',
                text_auto=True
            )
            fig_bar.update_layout(
                showlegend=False, 
                yaxis_title=None, 
                xaxis_title="Numero di Selezioni"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- Análisis Comparativo por Lugar de Trabajo ---
        st.subheader("Top 5 Qualità per Luogo di Lavoro")

        # Calculamos los conteos agrupando por lugar de trabajo y cualidad
        comparison_df = df_filtered.groupby(['mainWorkplace', 'qualities']).size().reset_index(name='count')
        
        # Obtenemos el top 5 para cada grupo
        top_5_per_workplace = comparison_df.groupby('mainWorkplace').apply(lambda x: x.nlargest(5, 'count')).reset_index(drop=True)

        fig_grouped = px.bar(
            top_5_per_workplace,
            x='qualities',
            y='count',
            color='mainWorkplace',
            barmode='group',
            text_auto=True,
            title="Confronto delle 5 qualità più scelte tra Ufficio e Cantiere"
        )
        fig_grouped.update_layout(xaxis_title="Qualità", yaxis_title="Numero di Selezioni")
        st.plotly_chart(fig_grouped, use_container_width=True)

    else:
        st.warning("Nessun dato corrisponde ai filtri selezionati.")