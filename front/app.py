import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Consommation Électricité France")
st.markdown("Data Engineering")

API_BASE = "http://localhost:8001"

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
    if conso:
        df = pd.DataFrame(conso)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        
        fig = px.line(df, x='datetime', y='mw_conso', 
                     title="Consommation horaire",
                     height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Données")
        st.dataframe(df.tail(20), use_container_width=True)
    else:
        st.warning("Données indisponibles")

st.markdown("---")
st.caption("ETL + FastAPI + Streamlit - RNCP C1 validé")

if st.toggle("Auto-refresh (60s)"):
    st.info("Refresh auto activé...")
    time.sleep(55)  # Cache ttl=60s
    st.rerun()
else:
    st.button("Refresh manuel", on_click=st.rerun)

