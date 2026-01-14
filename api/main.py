from fastapi import FastAPI
import pandas as pd
import os
from sqlalchemy import create_engine
from typing import Optional

app = FastAPI(title="RTE API")

db_path = os.path.abspath('database/rte_consommation.db')
engine = create_engine(f'sqlite:///{db_path}')

@app.get("/")
def root():
    count = pd.read_sql("SELECT COUNT(*) cnt FROM consommation", engine).iloc[0]['cnt']
    return {"status": "OK", "lignes": int(count)}

@app.get("/conso")
def conso(limit: Optional[int] = 24):
    df = pd.read_sql(f"SELECT * FROM consommation ORDER BY datetime DESC LIMIT {limit}", engine)
    return df.to_dict('records')

@app.get("/stats")
def stats():
    stats = pd.read_sql("SELECT AVG(mw_conso) m, MAX(mw_conso) p, MIN(mw_conso) c FROM consommation", engine).iloc[0]
    return {"moyenne": round(stats.m), "pic": round(stats.p), "creux": round(stats.c)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
