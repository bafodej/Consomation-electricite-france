"""
Entraînement du modèle de prédiction avec MLflow tracking
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import mlflow
import mlflow.sklearn
from pathlib import Path
from datetime import datetime


def load_data():
    """Charger les donnees enrichies (3 sources)"""
    data_path = Path(__file__).parent.parent / "data" / "conso_enrichi_3sources.csv"

    if not data_path.exists():
        print(f"ERREUR: Fichier introuvable: {data_path}")
        print("Executer d'abord: python src/etl_fusion_donnees.py")
        raise FileNotFoundError(f"Fichier de donnees introuvable: {data_path}")

    df = pd.read_csv(data_path)
    df["datetime"] = pd.to_datetime(df["datetime"])

    return df


def prepare_features(df):
    """Preparer les features pour l'entrainement avec donnees multi-sources"""

    # Features disponibles avec les 3 sources
    features = [
        "heure",  # Feature temporelle
        "jour_semaine",  # Feature temporelle
        "mois",  # Feature temporelle
        "jour_mois",  # Feature temporelle
        "est_weekend",  # Feature temporelle
        "prix_spot_eur_mwh",  # Source 3: Web scrapping
        "est_ferie",  # Source 2: Fichier texte
        "est_vacances",  # Source 2: Fichier texte
    ]

    target = "mw_conso"  # Source 1: API

    # Verifier que toutes les colonnes existent
    missing_cols = [col for col in features if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes: {missing_cols}")

    df_clean = df.dropna(subset=[target] + features)

    X = df_clean[features]
    y = df_clean[target]

    return X, y


def train_model(X_train, y_train, params):
    """Entraîner le modèle RandomForest"""
    model = RandomForestRegressor(**params)
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test):
    """Évaluer les performances du modèle"""
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    metrics = {
        'mae': mae,
        'mse': mse,
        'rmse': rmse,
        'r2_score': r2
    }

    return metrics, y_pred


def main():
    """Pipeline principal d'entraînement avec MLflow tracking"""

    # Configuration MLflow
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("rte_consommation_prediction")

    print("Chargement des données...")
    df = load_data()
    print(f"Données chargées: {len(df)} enregistrements")

    print("Préparation des features...")
    X, y = prepare_features(df)
    print(f"Features préparées: {X.shape}")

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Hyperparamètres
    params = {
        'n_estimators': 200,
        'max_depth': 15,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42,
        'n_jobs': -1
    }

    # MLflow run
    with mlflow.start_run(run_name=f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):

        # Log des paramètres
        mlflow.log_params(params)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))
        mlflow.log_param("features", list(X.columns))

        # Entraînement
        print("Entraînement du modèle...")
        model = train_model(X_train, y_train, params)

        # Cross-validation
        cv_scores = cross_val_score(
            model, X_train, y_train,
            cv=5, scoring='neg_mean_absolute_error'
        )
        cv_mae = -cv_scores.mean()
        mlflow.log_metric("cv_mae", cv_mae)
        print(f"Cross-validation MAE: {cv_mae:.2f} MW")

        # Évaluation
        print("Évaluation du modèle...")
        metrics, y_pred = evaluate_model(model, X_test, y_test)

        # Log des métriques
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)
            print(f"{metric_name.upper()}: {metric_value:.2f}")

        # Calcul de métriques business
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        mlflow.log_metric("mape_percent", mape)
        print(f"MAPE: {mape:.2f}%")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        print("\nImportance des features:")
        print(feature_importance.to_string(index=False))

        # Log feature importance
        for idx, row in feature_importance.iterrows():
            mlflow.log_metric(f"importance_{row['feature']}", row['importance'])

        # Sauvegarde du modèle
        model_path = Path(__file__).parent / "models" / "rte_conso_model.pkl"
        model_path.parent.mkdir(exist_ok=True)
        joblib.dump(model, model_path)
        print(f"\nModèle sauvegardé: {model_path}")

        # Log du modèle dans MLflow
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="RTEConsommationPredictor"
        )

        # Tags
        mlflow.set_tag("model_type", "RandomForestRegressor")
        mlflow.set_tag("target", "consommation_electrique")
        mlflow.set_tag("data_sources", "API_RTE + Fichier_CSV + Web_Scrapping")
        mlflow.set_tag("nb_sources", "3")
        mlflow.set_tag("training_date", datetime.now().isoformat())

        print("\nEntraînement terminé avec succès!")
        print(f"MLflow run ID: {mlflow.active_run().info.run_id}")


if __name__ == "__main__":
    main()
