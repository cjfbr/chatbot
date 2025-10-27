import pandas as pd

def query_current(data, state):
    df = data["states"]
    if state:
        row = df[df["state"].str.lower() == state.lower()]
        if not row.empty:
            return row.iloc[0].to_dict()
    return None


def query_history(data, state, year):
    df = data["history"]
    if not state:
        return None
    row = df[df["jurisdiction"].str.lower() == state.lower()]
    if row.empty:
        return None
    if year:
        col = str(year)
        if col in row.columns:
            return {"state": state, "year": year, "wage": row[col].values[0]}
    # If no year specified, return full history
    return row.T.reset_index().rename(columns={"index": "year", 0: "wage"})


def query_tipped(data, state):
    df = data["tipped"]
    if not state:
        return None
    row = df[df["jurisdicao"].str.lower() == state.lower()]
    if not row.empty:
        return row.iloc[0].to_dict()
    return None


def query_age(data, state):
    df = data["age"]
    if not state:
        return None

    # Normalize column names to lowercase
    df.columns = df.columns.str.lower()

    state_col = None
    for c in df.columns:
        if "state" in c or "jurisdiction" in c:
            state_col = c
            break

    if not state_col:
        return None

    row = df[df[state_col].str.lower() == state.lower()]
    if row.empty:
        return None

    # Try to find any column that mentions "minor", "age", "certificate"
    age_cols = [c for c in df.columns if any(x in c for x in ["minor", "age", "certificate"])]
    if not age_cols:
        return None

    info = next((str(row.iloc[0][c]) for c in age_cols if not pd.isna(row.iloc[0][c])), "No data available")
    return {"state": state, "provision": info or "No data available"}



def query_max_tipped(data):
    df = data["tipped"].copy()
    df.loc[:, "value"] = df["basic combined cash & tip minimum wage rate"].replace(r"[\$,]", "", regex=True)
    df.loc[:, "value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    row = df.loc[df["value"].idxmax()]
    return row.to_dict()


def query_min_tipped(data):
    df = data["tipped"].copy()
    df.loc[:, "value"] = df["basic combined cash & tip minimum wage rate"].replace(r"[\$,]", "", regex=True)
    df.loc[:, "value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    row = df.loc[df["value"].idxmin()]
    return row.to_dict()


def query_max(data):
    df = data["states"].copy()
    df.loc[:, "value"] = df["basic_minimum_rate_text"].replace(r"[\$,]", "", regex=True).astype(float)
    row = df.loc[df["value"].idxmax()]
    return row.to_dict()


def query_min(data):
    df = data["states"].copy()
    df["value"] = df["basic_minimum_rate_text"].replace(r"[\$,]", "", regex=True).astype(float)
    min_val = df["value"].min()
    rows = df[df["value"] == min_val]
    return rows


def query_compare(data, states):
    df = data["states"]
    #  Create a copy to avoid SettingWithCopyWarning
    filtered = df[df["state"].str.lower().isin([s.lower() for s in states])].copy()
    if filtered.empty:
        return None

    filtered.loc[:, "value"] = (
        filtered["basic_minimum_rate_text"].replace(r"[\$,]", "", regex=True).astype(float)
    )
    return filtered[["state", "value"]]

