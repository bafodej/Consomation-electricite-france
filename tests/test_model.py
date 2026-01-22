"""
Tests automatisés pour les modèles ML
RNCP C12: Tests automatisés des modèles d'IA
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


class TestModelPerformance:
    """Tests de performance du modèle ML"""

    @pytest.fixture
    def sample_data(self):
        """Créer des données de test synthétiques"""
        np.random.seed(42)
        hours = np.arange(0, 24)
        # Simulation consommation réaliste (pic matin/soir)
        base_conso = 50000
        variation = 15000 * np.sin(hours * np.pi / 12)
        noise = np.random.normal(0, 2000, len(hours))
        consumption = base_conso + variation + noise

        df = pd.DataFrame({
            'heure': hours,
            'consommation': consumption
        })
        return df

    @pytest.fixture
    def trained_model(self, sample_data):
        """Entraîner un modèle sur les données de test"""
        X = sample_data[['heure']].values
        y = sample_data['consommation'].values

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        return model

    def test_model_predictions_range(self, trained_model):
        """Test: les prédictions doivent être dans une plage réaliste"""
        X_test = np.array([[8], [12], [18], [22]])  # Heures typiques
        predictions = trained_model.predict(X_test)

        # Consommation France: entre 30 GW et 90 GW typiquement
        MIN_CONSO_MW = 30000
        MAX_CONSO_MW = 100000

        for pred in predictions:
            assert MIN_CONSO_MW <= pred <= MAX_CONSO_MW, \
                f"Prédiction {pred:.0f} MW hors limites réalistes"

    def test_model_consistency(self, trained_model):
        """Test: prédictions identiques pour mêmes inputs"""
        X_test = np.array([[10]])
        pred1 = trained_model.predict(X_test)[0]
        pred2 = trained_model.predict(X_test)[0]

        assert pred1 == pred2, "Le modèle doit être déterministe"

    def test_model_mae_threshold(self, trained_model, sample_data):
        """Test: MAE doit être sous un seuil acceptable"""
        X = sample_data[['heure']].values
        y_true = sample_data['consommation'].values
        y_pred = trained_model.predict(X)

        mae = mean_absolute_error(y_true, y_pred)

        # MAE doit être < 5000 MW (10% de la conso moyenne)
        MAE_THRESHOLD = 5000
        assert mae < MAE_THRESHOLD, \
            f"MAE {mae:.0f} MW dépasse le seuil de {MAE_THRESHOLD} MW"

    def test_model_r2_score(self, trained_model, sample_data):
        """Test: R² doit indiquer un bon fit"""
        X = sample_data[['heure']].values
        y_true = sample_data['consommation'].values
        y_pred = trained_model.predict(X)

        r2 = r2_score(y_true, y_pred)

        # R² minimum acceptable: 0.7
        R2_THRESHOLD = 0.7
        assert r2 >= R2_THRESHOLD, \
            f"R² score {r2:.3f} insuffisant (min: {R2_THRESHOLD})"

    def test_model_no_negative_predictions(self, trained_model):
        """Test: pas de prédictions négatives"""
        X_test = np.array([[h] for h in range(0, 24)])
        predictions = trained_model.predict(X_test)

        assert all(predictions >= 0), \
            "Le modèle ne doit pas prédire de consommation négative"

    def test_peak_hours_detection(self, trained_model):
        """Test: détection des heures de pic (8h et 19h)"""
        hours_test = np.array([[8], [19]])  # Heures de pic typiques
        hours_off_peak = np.array([[3], [15]])  # Heures creuses

        peak_preds = trained_model.predict(hours_test)
        off_peak_preds = trained_model.predict(hours_off_peak)

        avg_peak = np.mean(peak_preds)
        avg_off_peak = np.mean(off_peak_preds)

        # Les pics doivent être détectés (consommation plus élevée)
        assert avg_peak > avg_off_peak, \
            "Le modèle doit identifier les heures de pic"


class TestModelSaving:
    """Tests de sauvegarde/chargement du modèle"""

    def test_model_save_load(self, tmp_path, sample_data):
        """Test: sauvegarder et charger un modèle"""
        X = sample_data[['heure']].values
        y = sample_data['consommation'].values

        # Entraîner et sauvegarder
        model_original = RandomForestRegressor(random_state=42)
        model_original.fit(X, y)

        model_path = tmp_path / "test_model.pkl"
        joblib.dump(model_original, model_path)

        # Charger et vérifier
        model_loaded = joblib.load(model_path)

        X_test = np.array([[10]])
        pred_original = model_original.predict(X_test)[0]
        pred_loaded = model_loaded.predict(X_test)[0]

        assert pred_original == pred_loaded, \
            "Le modèle chargé doit donner les mêmes prédictions"

    @pytest.fixture
    def sample_data(self):
        """Données de test pour ModelSaving"""
        np.random.seed(42)
        return pd.DataFrame({
            'heure': range(24),
            'consommation': 50000 + np.random.randn(24) * 5000
        })


class TestModelInputValidation:
    """Tests de validation des inputs"""

    @pytest.fixture
    def simple_model(self):
        """Modèle simple pour tests de validation"""
        X_train = np.array([[i] for i in range(24)])
        y_train = np.random.randn(24) * 5000 + 50000
        model = RandomForestRegressor(random_state=42)
        model.fit(X_train, y_train)
        return model

    def test_invalid_hour_handling(self, simple_model):
        """Test: gestion d'heures invalides (>24)"""
        # Le modèle doit pouvoir prédire mais on teste qu'il ne crash pas
        X_invalid = np.array([[25], [30], [100]])
        predictions = simple_model.predict(X_invalid)

        assert len(predictions) == 3, "Doit traiter toutes les entrées"
        assert all(np.isfinite(predictions)), "Pas de NaN/Inf dans prédictions"
