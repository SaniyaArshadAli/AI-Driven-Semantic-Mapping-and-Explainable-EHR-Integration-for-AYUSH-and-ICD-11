import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import time
import json

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# ==============================
# CONFIGURATION
# ==============================
DEMO_MODE = False  # 👉 Set True to disable live Gemini calls
PAGE_SIZE = 8

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "C:\\Users\\saniy\\OneDrive\\Desktop\\BioPython_CourseProject\\ehr.db")

# ==============================
# GEMINI CONFIG
# ==============================
if not DEMO_MODE:
    genai.configure(api_key="AIzaSyCf2-Ap8SktjyT1WLEX8MFgfmMCDW2zc38")
    gemini = genai.GenerativeModel("gemini-2.5-flash")

# ==============================
# DATABASE HELPERS
# ==============================
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def load_all():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM semantic_mapping", conn)
    conn.close()
    return df

def update_mapping(mid, status, reviewer, icd_override=None):
    conn = get_db()
    cur = conn.cursor()

    if icd_override:
        cur.execute("""
            UPDATE semantic_mapping
            SET status=?, reviewed_by=?, reviewed_at=?, icd11_term=?
            WHERE id=?
        """, (status, reviewer, datetime.utcnow(), icd_override, mid))
    else:
        cur.execute("""
            UPDATE semantic_mapping
            SET status=?, reviewed_by=?, reviewed_at=?
            WHERE id=?
        """, (status, reviewer, datetime.utcnow(), mid))

    conn.commit()
    conn.close()

# ==============================
# SAFE GEMINI CALL (CACHED)
# ==============================
@st.cache_data(show_spinner=False)
def ask_gemini(prompt: str):
    if DEMO_MODE:
        return "🧪 **Demo Mode Enabled**\n\nThis is a cached AI explanation shown without calling Gemini."

    try:
        response = gemini.generate_content(prompt)
        time.sleep(1.5)  # rate limiting
        return response.text.strip()
    except ResourceExhausted:
        return "⚠️ Gemini API quota exceeded. Please wait and retry later."
    except Exception as e:
        return f"❌ AI error: {str(e)}"

# ==============================
# LOGIN
# ==============================
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

if not st.session_state.user:
    st.title("🔐 Clinical Reviewer Login")
    name = st.text_input("Reviewer Name")
    role = st.selectbox("Role", ["Clinician", "Admin"])

    if st.button("Login"):
        if name:
            st.session_state.user = name
            st.session_state.role = role
            st.rerun()
        else:
            st.warning("Please enter your name")

    st.stop()

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="AYUSH ↔ ICD-11 Explainable EHR",
    layout="wide"
)

st.title("🏥 AYUSH ↔ ICD-11 Explainable EHR Console")
st.caption(f"Logged in as **{st.session_state.user}** ({st.session_state.role})")

# ==============================
# LOAD DATA
# ==============================
df = load_all()

# ==============================
# DASHBOARD METRICS
# ==============================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", len(df))
c2.metric("Approved", (df.status == "APPROVED").sum())
c3.metric("Pending", (df.status == "PENDING").sum())
c4.metric("Rejected", (df.status == "REJECTED").sum())

st.divider()

# ==============================
# FILTERS
# ==============================
st.sidebar.header("🔍 Filters")

status_filter = st.sidebar.multiselect(
    "Status",
    ["PENDING", "APPROVED", "REJECTED"],
    default=["PENDING"]
)

conf_range = st.sidebar.slider(
    "Confidence",
    0.0, 1.0, (0.0, 1.0)
)

search = st.sidebar.text_input("Search")

filtered = df[
    df.status.isin(status_filter) &
    (df.confidence >= conf_range[0]) &
    (df.confidence <= conf_range[1])
]

if search:
    filtered = filtered[
        filtered.ayush_term.str.contains(search, case=False) |
        filtered.icd11_term.str.contains(search, case=False) |
        filtered.reason.str.contains(search, case=False)
    ]

# ==============================
# PAGINATION
# ==============================
pages = max(1, (len(filtered) - 1) // PAGE_SIZE + 1)
page = st.number_input("Page", 1, pages)
page_df = filtered.iloc[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

# ==============================
# RECORD VIEWER
# ==============================
for _, r in page_df.iterrows():

    icon = "🟢" if r.confidence >= 0.85 else "🟡" if r.confidence >= 0.6 else "🔴"

    with st.expander(f"{icon} {r.ayush_term} | Confidence {r.confidence:.2f}"):

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🌿 AYUSH")
            st.info(r.ayush_description)

        with col2:
            st.subheader("🌍 ICD-11")
            st.success(r.icd11_term)
            st.caption(r.reason)

        st.markdown("---")
        st.write("Status:", r.status)
        st.write("Reviewed By:", r.reviewed_by or "—")
        st.write("Reviewed At:", r.reviewed_at or "—")

        # ==============================
        # EXPLAINABLE AI
        # ==============================
        st.subheader("🤖 Explainable AI")

        confirm = st.checkbox(
            "I understand this will call the AI API",
            key=f"confirm_{r.id}"
        )

        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Deep",
            "🔄 Counterfactual",
            "🥇 Top-3",
            "⚠️ Bias"
        ])

        if confirm:

            with tab1:
                if st.button("Explain Mapping", key=f"d_{r.id}"):
                    prompt = f"""
Explain clinically why AYUSH '{r.ayush_term}'
maps to ICD-11 '{r.icd11_term}'.
"""
                    st.info(ask_gemini(prompt))

            with tab2:
                if st.button("Counterfactual", key=f"c_{r.id}"):
                    prompt = f"""
What changes would invalidate mapping
AYUSH '{r.ayush_term}' → ICD-11 '{r.icd11_term}'?
"""
                    st.warning(ask_gemini(prompt))

            with tab3:
                if st.button("Top-3 Alternatives", key=f"t_{r.id}"):
                    prompt = f"""
Suggest top 3 ICD-11 alternatives for AYUSH '{r.ayush_term}'
with similarity scores.
"""
                    st.success(ask_gemini(prompt))

            with tab4:
                if st.button("Bias & Uncertainty", key=f"b_{r.id}"):
                    prompt = f"""
Analyze bias and uncertainty risks in mapping
AYUSH '{r.ayush_term}' → ICD-11 '{r.icd11_term}'.
"""
                    st.error(ask_gemini(prompt))

        # ==============================
        # REVIEW ACTIONS
        # ==============================
        if r.status == "PENDING":
            st.subheader("📝 Clinical Decision")

            override = st.text_input(
                "Override ICD-11 term",
                r.icd11_term,
                key=f"o_{r.id}"
            )

            colA, colB = st.columns(2)

            with colA:
                if st.button("✅ Approve", key=f"a_{r.id}"):
                    update_mapping(r.id, "APPROVED", st.session_state.user, override)
                    st.rerun()

            with colB:
                if st.button("❌ Reject", key=f"r_{r.id}"):
                    update_mapping(r.id, "REJECTED", st.session_state.user)
                    st.rerun()

# ==============================
# EXPORT
# ==============================
st.divider()
st.subheader("📤 Export Approved Mappings")

approved = df[df.status == "APPROVED"]

fhir_json = {
    "resourceType": "ConceptMap",
    "group": [{
        "source": "AYUSH",
        "target": "ICD-11",
        "element": [
            {
                "code": r.ayush_term,
                "target": [{
                    "code": r.icd11_term,
                    "confidence": r.confidence
                }]
            } for _, r in approved.iterrows()
        ]
    }]
}

st.download_button("Download CSV", approved.to_csv(index=False), "approved_mappings.csv")
st.download_button("Download FHIR JSON", json.dumps(fhir_json, indent=2), "conceptmap.json")

st.caption("⚠️ AI assists clinicians. Final responsibility remains human.")
