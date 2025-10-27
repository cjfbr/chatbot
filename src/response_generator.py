import pandas as pd

def generate_response(parsed, result):
    """Generate natural-language answers from parsed intent and query results."""

    # --- Handle empty results ---
    if result is None or (isinstance(result, (pd.DataFrame, dict)) and len(result) == 0):
        return "Sorry, I couldn’t find information for that query."

    q_type = parsed.get("type")
    state = parsed.get("state") or (
        parsed.get("states")[0] if parsed.get("states") else None
    )

    # --- Handle NaN or missing values ---
    def clean_value(v):
        if pd.isna(v) or v in ["nan", None, ""]:
            return "No data available"
        return str(v).strip()

    # --- Handle CURRENT wage queries ---
    if q_type == "current":
        wage = clean_value(result.get("basic_minimum_rate_text"))
        note = result.get("note", "")
        return f"The current minimum wage in {state} is {wage}{f' {note}' if note else ''}"

    # --- Handle MAX wage queries ---
    if q_type == "max":
        wage = clean_value(result.get("basic_minimum_rate_text"))
        return f"The state with the highest minimum wage is {result.get('state')} at {wage}."

    # --- Handle MIN wage queries ---
    if q_type == "min":
        if isinstance(result, pd.DataFrame):
            wage = result["value"].iloc[0]
            states = ", ".join(result["state"].tolist())
            return f"The states with the lowest minimum wage ({wage:.2f}) are: {states}."
        else:
            wage = clean_value(str(result.get("basic_minimum_rate_text")))
            return f"The state with the lowest minimum wage is {result.get('state')} at ${wage}."


    # --- Handle COMPARE queries ---
    if q_type == "compare":
        if isinstance(result, pd.DataFrame) and len(result) >= 2:
            rows = result.to_dict(orient="records")
            text = "### Comparison\n\n"
            for r in rows:
                text += f"- **{r['state']}**: ${r['value']:.2f}\n\n"
            diff = rows[0]["value"] - rows[1]["value"]
            if diff == 0:
                return text + "→ Both states have the same minimum wage."
            elif diff > 0:
                return text + f"→ **{rows[0]['state']}** has a higher minimum wage by **${abs(diff):.2f}**."
            else:
                return text + f"→ **{rows[1]['state']}** has a higher minimum wage by **${abs(diff):.2f}**."

    # --- Handle TIPPED wage queries ---
    if q_type == "tipped":
        wage = clean_value(
            result.get("basic combined cash & tip minimum wage rate")
            or result.get("tipped_wage")
        )
        return f"In {state}, the minimum wage for tipped workers is ${wage}."

    # --- Handle AGE-based wage queries ---
    if q_type == "age":
        wage = clean_value(
            result.get("minimum_wage") or result.get("age_based_rate") or result.get("provision")
        )
        return f"In {state}, {wage}."

    # --- Handle HISTORY queries ---
    if q_type == "history":
        if isinstance(result, dict) and "year" in result:
            return f"The minimum wage in {state} in {result['year']} was ${result['wage']}."
        elif isinstance(result, pd.DataFrame):
            result_clean = result.dropna(how="all").fillna("-")
            table = result_clean.to_markdown(index=False)
            return f"**Full historical data for {state}:**\n\n{table}"

    # --- Fallback ---
    return "Sorry, I couldn’t find information for that query."


    

    

