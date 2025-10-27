import streamlit as st
from src.data_loader import load_data
from src.question_parser import parse_question
from src.query_engine import (
    query_current, query_history, query_tipped, query_age,
    query_max, query_min, query_compare, query_max_tipped, query_min_tipped
)
from src.response_generator import generate_response

st.set_page_config(page_title="US Minimum Wage Chatbot", layout="centered")

st.title("💬 US Minimum Wage Chatbot")
st.markdown("Ask about minimum wages, historical rates, tipped worker rates, or labor certificate rules for minors."
            )

# Load data
data = load_data()

# User input
user_input = st.text_input("Ask your question (e.g. 'Which state has the highest minimum wage?', 'Which state offers better pay, Colorado or Utah?','How has the wage changed in Washington over the years?','What do children need to work in Florida')")

if st.button("Ask"):
    if not user_input.strip():
        st.warning("Please type a question.")
    else:
        # ✅ Parse question first
        parsed = parse_question(user_input)
        q_type = parsed["type"]

        # Run the correct query based on detected type
        if q_type == "max":
            result = query_max(data)
        elif q_type == "min":
            result = query_min(data)
        elif q_type == "max_tipped":
            result = query_max_tipped(data)
        elif q_type == "min_tipped":
            result = query_min_tipped(data)
        elif q_type == "compare":
            result = query_compare(data, parsed["states"])
        elif q_type == "current":
            result = query_current(data, parsed["states"][0] if parsed["states"] else None)
        elif q_type == "history":
            result = query_history(data, parsed["states"][0] if parsed["states"] else None, parsed["year"])
        elif q_type == "tipped":
            result = query_tipped(data, parsed["states"][0] if parsed["states"] else None)
        elif q_type == "age":
            result = query_age(data, parsed["states"][0] if parsed["states"] else None)
        else:
            result = None

        # ✅ Now use parsed in response generation
        st.markdown("### 🤖 Answer:")
        st.markdown(generate_response(parsed, result))


# Show confidence if below threshold
    if parsed["confidence"] < 0.3:
        st.info("⚠️ I'm not very confident about your question intent. Try rephrasing it.")


