"""
Entraînement du modèle de prédiction avec MLflow tracking
RNCP C11: Assurer le suivi et monitoring des modèles
RNCP C13: Intégrer les évolutions et le suivi des modèles (MLOps)
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
    """Charger les données de consommation RTE"""
    data_path = Path(__file__).parent.parent / "data" / "conso_recent_2026.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"Fichier de données introuvable: {data_path}")

    df = pd.read_csv(data_path)
    df['date_heure'] = pd.to_datetime(df['date_heure'])
    df['heure'] = df['date_heure'].dt.hour
    df['jour_semaine'] = df['date_heure'].dt.dayofweek
    df['mois'] = df['date_heure'].dt.month

    return df


def prepare_features(df):
    """Préparer les features pour l'entraînement"""
    features = ['heure', 'jour_semaine', 'mois']
    target = 'consommation'

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
        mlflow.set_tag("data_source", "RTE_eco2mix")
        mlflow.set_tag("training_date", datetime.now().isoformat())

        print("\nEntraînement terminé avec succès!")
        print(f"MLflow run ID: {mlflow.active_run().info.run_id}")


if __name__ == "__main__":
    main()
