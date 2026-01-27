import pandas as pd
import requests


def get_consommation(start, end):
    """Conso RTE France PUBLIQUE"""
    # ENDPOINT  Eco2Mix
    url = (
        "https://digital.iservices.rte-france.com/open_api/eco2mix/v1/powerConsumption"
    )
    params = {"start_date": f"{start}T00:00:00Z", "end_date": f"{end}T23:59:59Z"}

    resp = requests.get(url, params=params)
    print(f"Status: {resp.status_code}")

    if resp.status_code != 200:
        print("Erreur:", resp.text[:200])
        return None

    data = resp.json()
    df = pd.DataFrame(data)
    return df


if __name__ == "__main__":
    df = get_consommation("2026-01-01", "2026-01-14")
    if df is not None:
        print(df.head())
        df.to_csv("conso_rte.csv", index=False)
        print(" conso_rte.csv créé !")
