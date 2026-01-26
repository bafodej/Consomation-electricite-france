"""
Tests automatisés pour l'API FastAPI
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Tests des endpoints de l'API RTE"""

    def test_root_endpoint(self):
        """Test endpoint racine - doit retourner le statut"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "OK"
        assert "lignes" in data
        assert isinstance(data["lignes"], int)

    def test_conso_endpoint_default(self):
        """Test endpoint /conso avec limite par défaut (24)"""
        response = client.get("/conso")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 24

        # Vérifier la structure d'un enregistrement
        if len(data) > 0:
            record = data[0]
            assert "datetime" in record
            assert "mw_conso" in record

    def test_conso_endpoint_custom_limit(self):
        """Test endpoint /conso avec limite personnalisée"""
        limit = 10
        response = client.get(f"/conso?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= limit

    def test_stats_endpoint(self):
        """Test endpoint /stats - doit retourner moyenne, pic, creux"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()

        # Vérifier la présence des statistiques
        assert "moyenne" in data
        assert "pic" in data
        assert "creux" in data

        # Vérifier que ce sont des nombres
        assert isinstance(data["moyenne"], (int, float))
        assert isinstance(data["pic"], (int, float))
        assert isinstance(data["creux"], (int, float))

        # Vérifier la cohérence: pic >= moyenne >= creux
        assert data["pic"] >= data["moyenne"]
        assert data["moyenne"] >= data["creux"]


class TestAPIValidation:
    """Tests de validation et gestion d'erreurs"""

    def test_conso_negative_limit(self):
        """Test avec limite negative - doit retourner une erreur"""
        response = client.get("/conso?limit=-5")
        assert response.status_code in [400, 422]

    def test_conso_zero_limit(self):
        """Test avec limite zero - doit retourner une erreur"""
        response = client.get("/conso?limit=0")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestAPISecurity:
    """Tests de sécurité basiques"""

    def test_sql_injection_attempt(self):
        """Test protection contre injection SQL basique"""
        malicious_limit = "1; DROP TABLE consommation--"
        response = client.get(f"/conso?limit={malicious_limit}")
        # L'API doit rejeter ou gérer gracieusement
        assert response.status_code in [200, 400, 422]
