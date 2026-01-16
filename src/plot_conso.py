import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('conso_recent_2026.csv')
df['date_heure'] = pd.to_datetime(df['date_heure'])

plt.figure(figsize=(12,6))
plt.plot(df['date_heure'], df['consommation'], label='Conso réelle (MW)')
plt.plot(df['date_heure'], df['prevision_j'], label='Prévision J', alpha=0.7)
plt.title('Consommation Électricité France (RTE) - Jan 2025')
plt.ylabel('MW')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('conso_france_2025.png', dpi=300)
plt.show()
