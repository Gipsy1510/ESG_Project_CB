"""
ESG Report Assistant — Streamlit app.

Run with:
    streamlit run src/app/streamlit_app.py
"""

import streamlit as st
from src.rag.pipeline import run_rag_question

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "ESG Report Assistant",
    page_icon  = "🌱",
    layout     = "wide",
)

COMPANIES = [
    "Any",
    "AXA", "Airbus", "BNP Paribas", "BP", "Barclays", "BlackRock",
    "Danone", "Engie", "Glencore", "HSBC", "Iberdrola", "L'Oréal",
    "Microsoft", "Nestlé", "Schneider Electric", "Shell", "Siemens",
    "TotalEnergies", "Unilever", "Volkswagen",
]

YEARS = ["Any", "2025", "2024", "2023", "2022", "2021", "2020"]

EXAMPLE_QUESTIONS = [
    "What are Shell Scope 1 and Scope 2 GHG emissions?",
    "What is TotalEnergies climate transition plan?",
    "What percentage of CapEx is aligned with the EU Taxonomy?",
    "Does Glencore disclose Scope 3 emissions?",
    "What are Microsoft's water consumption targets?",
    "How does Siemens govern climate-related issues?",
]

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌱 ESG Assistant")
    st.markdown("Ask questions about ESG reports from 19 companies (2020–2025).")
    st.divider()

    st.subheader("Filters")
    selected_company = st.selectbox("Company", COMPANIES)
    selected_year    = st.selectbox("Year", YEARS)
    top_k            = st.slider("Sources to retrieve", min_value=3, max_value=10, value=5)

    st.divider()
    st.subheader("Example questions")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state["question_input"] = q

# ── main area ─────────────────────────────────────────────────────────────────
st.title("ESG Report Assistant")
st.caption("Answers grounded in company sustainability reports. Sources cited for every answer.")

question = st.text_area(
    "Your question",
    value    = st.session_state.get("question_input", ""),
    height   = 100,
    key      = "question_input",
    placeholder = "e.g. What are Shell Scope 1 and Scope 2 emissions in 2023?",
)

ask = st.button("Ask", type="primary", use_container_width=True)

if ask and question.strip():
    company = None if selected_company == "Any" else selected_company.lower().strip()
    year    = None if selected_year == "Any" else int(selected_year)

    with st.spinner("Retrieving evidence and generating answer..."):
        try:
            result = run_rag_question(
                question = question.strip(),
                company  = company,
                year     = year,
                top_k    = top_k,
            )
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    # ── answer ────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Answer")
    st.markdown(result["answer"])

    # ── sources ───────────────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"Sources retrieved ({len(result['sources'])})")

    for s in result["sources"]:
        label = f"[{s['source_number']}] {s['company'].title()} · {s['year']} · Page {s['page']} · score {s['score']}"
        with st.expander(label):
            st.markdown(s["text_preview"])

elif ask and not question.strip():
    st.warning("Please enter a question.")