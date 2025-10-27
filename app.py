import streamlit as st
from src.data_loader import load_data
from src.question_parser import parse_question
from src.query_engine import (
    query_current, query_history, query_tipped, query_age,
    query_max, query_min, query_compare, query_max_tipped, query_min_tipped
)
from src.response_generator import generate_response

# --------------------------
#  Page configuration
# --------------------------
st.set_page_config(page_title="US Minimum Wage Chatbot", layout="centered")

st.title("💬 US Minimum Wage Chatbot")
st.markdown("""
Ask about minimum wages, historical rates, tipped worker rates, or labor certificate rules for minors.
Examples:
- "Which state has the highest minimum wage?"
- "Which state offers better pay, Colorado or Utah?"
- "How has the wage changed in Washington over the years?"
- "Do minors need a work certificate in Florida?"
""")

# --------------------------
#  Load and cache data
# --------------------------
@st.cache_data
def get_data():
    return load_data()

data = get_data()

# --------------------------
#  Input form (Enter or Button)
# --------------------------
with st.form(key="chat_form"):
    user_input = st.text_input(
        "Ask your question:",
        placeholder="Type a question and press Enter or click 'Ask'"
    )
    submitted = st.form_submit_button("Ask")

# --------------------------
#  Main logic
# --------------------------
if submitted:
    if not user_input.strip():
        st.warning("Please type a question.")
    else:
        with st.spinner("🤔 Thinking..."):
            parsed = parse_question(user_input)
            q_type = parsed.get("type")

            # Run appropriate query
            result = None
            try:
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

            except Exception as e:
                st.error(f"❌ Error while processing your question: {e}")
                result = None

        # --------------------------
        #  Generate and display response
        # --------------------------
        if result is not None:
            st.markdown("### 🤖 Answer:")
            st.markdown(generate_response(parsed, result))
        else:
            st.warning("Sorry, I couldn't find an answer for that question.")

        # --------------------------
        #  Confidence warning
        # --------------------------
        if parsed.get("confidence", 1) < 0.3:
            st.info("⚠️ I'm not very confident about your question intent. Try rephrasing it.")

    with st.expander("🔍 Debug info (Intent Detection)"):
        st.markdown(f"**Intent Type:** `{query['type']}`")
        if query["states"]:
            st.markdown("**Detected States:** " + ", ".join(f"`{s}`" for s in query["states"]))
        else:
            st.markdown("**Detected States:** _None_")
        st.markdown(f"**Year:** `{query['year'] if query['year'] else 'None'}`")
        st.markdown(f"**Confidence:** `{query['confidence']}`")
