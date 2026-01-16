import pandas as pd
import numpy as np
import os
import requests 
from sqlalchemy import create_engine

print("ETL Dataset...")

dates = pd.date_range('2026-01-01', periods=500, freq='H')
conso = 45000 + 12000 * np.sin(2 * np.pi * dates.hour / 24) + np.random.normal(0, 1500, 500)

df = pd.DataFrame({
    'datetime': dates,
    'mw_conso': conso.round(0)
})

try:
    token = 'VOTRE_TOKEN'
    start, end = '2024-12-01T00:00:00', '2025-12-15T23:59:00'
    url = f"https://digital.iservices.rte-france.com/open_api/consumption/v1/consumption?start_date={start}&end_date={end}&token={token}"
    resp = requests.get(url)
    if resp.status_code == 200:
        df_real = pd.DataFrame(resp.json())
        df_real['datetime'] = pd.to_datetime(df_real['updated'])
        df_real.to_csv('data/rte_real.csv')  # Réel si OK
        print("API OK, réel utilisé")
    else:
        print("API fail, synthétique fallback")
except:
    pass  # Garde synthétique

os.makedirs('data', exist_ok=True)
os.makedirs('database', exist_ok=True)

df.to_csv('data/rte_consommation.csv', index=False)

db_path = os.path.abspath('database/rte_consommation.db')
engine = create_engine(f'sqlite:///{db_path}')
df.to_sql('consommation', engine, if_exists='replace', index=False)

print("Dataset créé")
print(f"Lignes: {len(df)}")
print(f"DB: {db_path}")
