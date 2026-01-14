import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine

print("ETL Dataset...")

dates = pd.date_range('2026-01-01', periods=500, freq='H')
conso = 45000 + 12000 * np.sin(2 * np.pi * dates.hour / 24) + np.random.normal(0, 1500, 500)

df = pd.DataFrame({
    'datetime': dates,
    'mw_conso': conso.round(0)
})

os.makedirs('data', exist_ok=True)
os.makedirs('database', exist_ok=True)

df.to_csv('data/rte_consommation.csv', index=False)

db_path = os.path.abspath('database/rte_consommation.db')
engine = create_engine(f'sqlite:///{db_path}')
df.to_sql('consommation', engine, if_exists='replace', index=False)

print("✅ Dataset créé")
print(f"Lignes: {len(df)}")
print(f"DB: {db_path}")
