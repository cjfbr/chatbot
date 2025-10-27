import re
import spacy
import subprocess



def load_spacy_model(model_name="en_core_web_sm"):
    try:
        # tenta carregar o modelo
        nlp = spacy.load(model_name)
        
    except OSError:
        
        subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
        nlp = spacy.load(model_name)
        
    return nlp



nlp = load_spacy_model()

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
    "tipped": ["tip", "tipped", "gratuity"],
    "history": ["since", "year", "change", "history", "evolve"],
    "age": ["minor", "certificate", "age", "child", "children", "kid", "kids", "teen", "teenager", "youth"],   
    "current": ["wage", "minimum", "pay", "current"],
    "max": ["highest", "max", "biggest", "largest", "top"],
    "min": ["lowest", "min", "smallest", "least", "bottom"],
    "compare": ["compare", "vs", "versus"],
}


def intent_confidence(q_type: str, lemmas: list[str]) -> float:
    """
    Compute how strongly the question matches the chosen intent,
    with dynamic boosting for age-related contexts.
    """
    keywords = INTENT_KEYWORDS.get(q_type, [])
    matches = sum(1 for w in lemmas if w in keywords)
    base_conf = matches / max(len(keywords), 1)

    # --- Dynamic confidence boosting rules ---
    if q_type == "age":
        # If the question mentions both 'wage' and an age-related word, boost confidence
        if any(w in lemmas for w in ["wage", "minimum", "pay"]) and any(
            w in lemmas for w in ["child", "children", "kid", "kids", "minor", "teen", "teenager"]
        ):
            base_conf += 0.3  # +30% confidence boost for clear "child wage" context

    elif q_type == "current":
        # If the question mentions 'wage' but no state or age term, it's strongly current
        if "wage" in lemmas and not any(
            w in lemmas for w in ["child", "children", "kid", "minor", "teen"]
        ):
            base_conf += 0.2

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

    # --- Detect intent ---
 
    if "tipped" in lemmas and any(w in lemmas for w in INTENT_KEYWORDS["max"]):
        q_type = "max_tipped"
    elif "tipped" in lemmas and any(w in lemmas for w in INTENT_KEYWORDS["min"]):
        q_type = "min_tipped"

    # ✅ Direct text fallback — catch "highest", "most", "greatest", "lowest", etc.
    elif any(word in text for word in ["highest", "most", "greatest", "largest", "top", "high"]):
        q_type = "max"
    elif any(word in text for word in ["lowest", "least", "smallest", "bottom", "low"]):
        q_type = "min"

    elif any(w in lemmas for w in INTENT_KEYWORDS["compare"]) or "vs" in text or "versus" in text or len(states) >= 2:
        q_type = "compare"

    elif any(w in lemmas for w in INTENT_KEYWORDS["age"]):
        # Priority rule: "wage" + "child/minor" → still age
        if any(w in lemmas for w in ["wage", "minimum", "pay"]):
            q_type = "age"
        else:
            q_type = "age"

    elif any(w in lemmas for w in INTENT_KEYWORDS["tipped"]):
        q_type = "tipped"

    elif any(w in lemmas for w in INTENT_KEYWORDS["history"]) or year:
        q_type = "history"

    # “how much” or wage-related → current
    elif any(w in lemmas for w in INTENT_KEYWORDS["current"]) or (
        "how" in [t.text for t in doc if t.tag_ in ["WP", "WRB"]] and "much" in lemmas
    ):
        q_type = "current"

    else:
        q_type = "unknown"


    # “how much” → current wage
    wh_words = [token.text for token in doc if token.tag_ in ["WP", "WRB"]]
    if "how" in wh_words and "much" in lemmas:
        q_type = "current"

    confidence = intent_confidence(q_type, lemmas)

    return {
        "type": q_type,
        "states": states,
        "year": year,
        "confidence": confidence,
    }



