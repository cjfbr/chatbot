import pandas as pd
from pathlib import Path

def load_data():
    base = Path("data")

    data = {
        "age": pd.read_csv(base / "age_certificates with footnotes.csv"),
        "history": pd.read_csv(base / "state_minimum_wage_history_2000.csv"),
        "tipped": pd.read_csv(base / "tipped_min_wage_completo.csv"),
        "states": pd.read_csv(base / "us_states_min_wage.csv"),
    }

    # Normalização de nomes de colunas
    data["history"].columns = [str(c).strip().lower() for c in data["history"].columns]
    data["tipped"].columns = [str(c).strip().lower() for c in data["tipped"].columns]
    data["states"].columns = [str(c).strip().lower() for c in data["states"].columns]
    data["age"].columns = [str(c).strip().lower() for c in data["age"].columns]

    return data
