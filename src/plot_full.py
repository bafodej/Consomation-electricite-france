import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

df = pd.read_csv("conso_rte_france.csv")
df["date_heure"] = pd.to_datetime(df["date_heure"])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

# Conso
ax1.plot(df["date_heure"], df["consommation"], label="Conso réelle", linewidth=2)
ax1.plot(df["date_heure"], df["prevision_j"], label="Prévision J", alpha=0.8)
ax1.set_title("Conso Élec France + Prévisions")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Prod mix (top 5)
prod_cols = ["nucleaire", "eolien", "solaire", "hydraulique", "gaz"]
df[prod_cols].plot(ax=ax2, kind="area", stacked=True, alpha=0.8)
ax2.set_title("Mix Production")
ax2.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

plt.tight_layout()
plt.savefig("full_analyse_rte.png", dpi=300, bbox_inches="tight")
plt.show()
