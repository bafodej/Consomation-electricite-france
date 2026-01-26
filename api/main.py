import os
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

load_dotenv()

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger import get_logger, setup_logging

# Configuration du logging
setup_logging(log_dir="logs")
logger = get_logger(__name__)

app = FastAPI(
    title="RTE Consommation API",
    description="API pour consulter les données de consommation électrique française",
    version="1.0.0",
)

# Configuration base de données
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite").lower()

if DATABASE_TYPE == "postgresql":
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "rte_consommation")
    user = os.getenv("POSTGRES_USER", "rte_user")
    password = os.getenv("POSTGRES_PASSWORD", "rte_secure_password")
    conn_string = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(conn_string)
    logger.info(f"API démarrée avec PostgreSQL: {host}:{port}/{db}")
else:
    db_path = os.path.abspath("database/rte_consommation.db")
    engine = create_engine(f"sqlite:///{db_path}")
    logger.info(f"API démarrée avec SQLite: {db_path}")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware pour logger toutes les requêtes"""
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}"

    logger.info(
        f"Requête entrante: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "client_host": request.client.host if request.client else "unknown",
        },
    )

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Requête terminée: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return response

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Erreur lors du traitement: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "duration_ms": round(duration_ms, 2),
            },
            exc_info=True,
        )
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gestionnaire global d'exceptions"""
    logger.error(
        f"Exception non gérée: {str(exc)}",
        extra={"endpoint": request.url.path, "method": request.method},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "message": "Une erreur s'est produite lors du traitement de votre requête",
        },
    )


@app.get("/")
def root():
    """Endpoint racine - vérification de l'état de l'API"""
    try:
        count = pd.read_sql("SELECT COUNT(*) cnt FROM consommation", engine).iloc[0]["cnt"]
        logger.info(f"Vérification santé API: {count} enregistrements en base")
        return {"status": "OK", "lignes": int(count)}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de santé: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données")


@app.get("/conso")
def conso(limit: Optional[int] = 24):
    """Récupérer les données de consommation récentes"""
    try:
        if limit <= 0:
            logger.warning(f"Limite invalide demandée: {limit}")
            raise HTTPException(status_code=400, detail="La limite doit être supérieure à 0")

        if limit > 1000:
            logger.warning(f"Limite trop élevée demandée: {limit}, limitée à 1000")
            limit = 1000

        df = pd.read_sql(f"SELECT * FROM consommation ORDER BY datetime DESC LIMIT {limit}", engine)
        logger.info(f"Récupération de {len(df)} enregistrements de consommation")
        return df.to_dict("records")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des données")


@app.get("/stats")
def stats():
    """Statistiques globales de consommation"""
    try:
        stats_df = pd.read_sql(
            "SELECT AVG(mw_conso) m, MAX(mw_conso) p, MIN(mw_conso) c FROM consommation", engine
        ).iloc[0]

        result = {
            "moyenne": round(stats_df.m),
            "pic": round(stats_df.p),
            "creux": round(stats_df.c),
        }

        logger.info(f"Statistiques calculées: {result}")
        return result

    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur lors du calcul des statistiques")


if __name__ == "__main__":
    import uvicorn

    logger.info("Démarrage du serveur uvicorn sur port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
