import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Consommation Électricité France")
st.markdown("Data Engineering")

API_BASE = "http://localhost:8000"

@st.cache_data(ttl=60)
def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f" FastAPI erreur: {e}")
        st.info("Vérifie: uvicorn api.main:app --port 8001")
        return None

col1, col2 = st.columns([1,3])

with col1:
    st.header("API Status")
    stats = fetch_data("/stats")
    conso = fetch_data("/conso?limit=168")
    
    if stats:
        st.metric("Moyenne", f"{stats['moyenne']} MW")
        st.metric("Pic", f"{stats['pic']} MW")
        st.metric("Creux", f"{stats['creux']} MW")

with col2:
    predictions = fetch_data("/predict?limit=168")

    if predictions:
        df = pd.DataFrame(predictions)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['datetime'], y=df['mw_conso'],
            name='Consommation réelle', line=dict(color='#1f77b4')
        ))
        fig.add_trace(go.Scatter(
            x=df['datetime'], y=df['mw_predit'],
            name='Prédiction ML', line=dict(color='#ff7f0e', dash='dash')
        ))
        fig.update_layout(
            title="Consommation réelle vs Prédiction ML (7 derniers jours)",
            height=400,
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Données")
        st.dataframe(df[['datetime', 'mw_conso', 'mw_predit']].tail(20), use_container_width=True)
    elif conso:
        df = pd.DataFrame(conso)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['mw_conso'],
                                 name='Consommation réelle', line=dict(color='#1f77b4')))
        fig.update_layout(title="Consommation horaire", height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.tail(20), use_container_width=True)
    else:
        st.warning("Données indisponibles")

st.markdown("---")
st.caption("ETL + FastAPI + Streamlit -  C1 ")

if st.toggle("Auto-refresh (60s)"):
    st.info("Refresh auto activé...")
    time.sleep(55)  # Cache ttl=60s
    st.rerun()
else:
    st.button("Refresh manuel", on_click=st.rerun)

