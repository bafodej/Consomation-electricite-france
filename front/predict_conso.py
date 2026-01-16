from sklearn.ensemble import RandomForestRegressor
import pandas as pd

df = pd.read_csv('conso_recent_2026.csv')
X = df[['heure']].values  # Features
y = df['consommation'].values

model = RandomForestRegressor()
model.fit(X, y)
next_conso = model.predict([[8]])[0]
print(f" Prédiction 8h: {next_conso:,.0f} MW")
