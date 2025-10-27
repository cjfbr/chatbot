import streamlit as st  
import re
import spacy




@st.cache_resource
def get_nlp():
    # como o wheel já foi instalado na build, só carregar
    return spacy.load("en_core_web_sm")

nlp = get_nlp()

US_STATES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware",
    "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
    "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey", "new mexico",
    "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming"
]

INTENT_KEYWORDS = {
    "tipped": ["tip", "tipped", "gratuity", "server", "waiter", "waitress", "bartender"],
    "history": ["since", "year", "change", "history", "evolve","past", "historical"],
    "age": ["minor", "certificate", "age", "child", "children", "kid", "kids", "teen", "teenager", "youth"],   
    "current": ["wage", "minimum", "pay", "current"],
    "max": ["highest", "max", "biggest", "largest", "top"],
    "min": ["lowest", "min", "smallest", "least", "bottom"],
    "compare": ["compare", "vs", "versus"],
}


def intent_confidence(q_type: str, lemmas: list[str]) -> float:
    keywords = INTENT_KEYWORDS.get(q_type, [])
    matches = sum(1 for w in lemmas if w in keywords)
    base_conf = matches / max(len(keywords), 1)

    # --- Dynamic confidence boosting rules ---
    if q_type == "age":
        if any(w in lemmas for w in ["wage", "minimum", "pay"]) and any(
            w in lemmas for w in ["child", "children", "kid", "kids", "minor", "teen", "teenager"]
        ):
            base_conf += 0.3

    elif q_type == "current":
        if "wage" in lemmas and not any(
            w in lemmas for w in ["child", "children", "kid", "minor", "teen"]
        ):
            base_conf += 0.2

    elif q_type == "compare":
        # Boost if multiple states are detected
        if len([w for w in lemmas if w in [s.lower() for s in US_STATES]]) >= 2:
            base_conf += 0.5  # big confidence boost for multi-state context

    return round(min(base_conf, 1.0), 2)



def parse_question(question: str):
    doc = nlp(question.lower())
    lemmas = [token.lemma_ for token in doc]
    text = question.lower()

    # --- Named Entity Recognition ---
    states = []
    year = None
    for ent in doc.ents:
        if ent.label_ == "GPE" and ent.text.lower() in US_STATES:
            states.append(ent.text.title())
        elif ent.label_ == "DATE" and re.match(r"^(19|20)\d{2}$", ent.text.strip()):
            year = int(ent.text.strip())

    # --- Intent detection (priority-based logic) ---

        # --- Detect intent (priority-based logic) ---

    # 1️⃣ Tipped (highest priority)
    if any(w in lemmas for w in INTENT_KEYWORDS["tipped"]):
        if any(w in lemmas for w in INTENT_KEYWORDS["max"]):
            q_type = "max_tipped"
        elif any(w in lemmas for w in INTENT_KEYWORDS["min"]):
            q_type = "min_tipped"
        else:
            q_type = "tipped"

    # 2️⃣ Comparison (multi-state or explicit compare)
    elif any(w in lemmas for w in INTENT_KEYWORDS["compare"]) or "vs" in text or "versus" in text or len(states) >= 2:
        q_type = "compare"

    # 3️⃣ Age-based
    elif any(w in lemmas for w in INTENT_KEYWORDS["age"]):
        q_type = "age"

    # 4️⃣ Historical (mention of year or history terms)
    elif any(w in lemmas for w in INTENT_KEYWORDS["history"]) or year:
        q_type = "history"

    # 5️⃣ Max/min (important: checked before 'current')
    elif any(word in text for word in ["highest", "most", "greatest", "largest", "top", "max"]):
        q_type = "max"
    elif any(word in text for word in ["lowest", "least", "smallest", "bottom", "low", "min"]):
        q_type = "min"

    # 6️⃣ Current wage (fallback)
    elif any(w in lemmas for w in INTENT_KEYWORDS["current"]) or (
        "how" in [t.text for t in doc if t.tag_ in ["WP", "WRB"]] and "much" in lemmas
    ):
        q_type = "current"

    else:
        q_type = "unknown"


    # Confidence scoring
    confidence = intent_confidence(q_type, lemmas)

    return {
        "type": q_type,
        "states": states,
        "year": year,
        "confidence": confidence,
    }

