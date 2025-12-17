# streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
from typing import List

API_URL = "http://localhost:8000/recommend"

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="SHL Assessment Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- HELPERS ----------------
def strip_html(s: str) -> str:
    """Strip HTML tags and return plain text (safe display)."""
    if s is None:
        return ""
    # If the incoming value is not a string, cast to str
    if not isinstance(s, str):
        s = str(s)
    return BeautifulSoup(s, "lxml").get_text(separator=" ", strip=True)

def normalize_recs(raw_recs: List[dict]) -> List[dict]:
    """Return sanitized, normalized records for display and charting."""
    norm = []
    for r in raw_recs:
        rec = {
            "Assessment Name": strip_html(r.get("Assessment Name", "Untitled")),
            "URL": r.get("URL", "#"),
            "Duration": r.get("Duration", None) if r.get("Duration") is not None else None,
            "Remote Testing Support": strip_html(r.get("Remote Testing Support", "No")),
            "Adaptive/IRT": strip_html(r.get("Adaptive/IRT", "No")),
            "Test Type": strip_html(r.get("Test Type", "Other")),
            "Skills": strip_html(r.get("Skills", "")),
            "Description": strip_html(r.get("Description", "")),
            "Relevance Score": float(r.get("Relevance Score", 0.0)) if r.get("Relevance Score") is not None else 0.0,
        }
        norm.append(rec)
    return norm

# ---------------- STYLES ----------------
st.markdown(
    """
<style>
/* Page background */
.stApp {
    background: linear-gradient(135deg, #0b1220 0%, #1e163a 60%, #2b1642 100%) !important;
    color: #e6eef8;
    font-family: Inter, Arial, Helvetica, sans-serif;
}

/* Header */
.header {
    text-align: center;
    padding: 2.2rem 1rem 1.2rem 1rem;
}
.header h1 { margin: 0; font-size: 2.2rem; letter-spacing: -0.5px; color: #f8fafc; }
.header p { margin: 6px 0 0 0; color: #b9c2d9; }

/* Sidebar tweaks */
.css-1d391kg { /* streamlit sidebar container hook - conservative, may vary by release */ }
.sidebar .stTextInput>div>div>input { background: #0f1720; color: #e6eef8; }

/* Card */
.card {
    background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
    border: 1px solid rgba(255,255,255,0.04);
}

/* Inner dark panel for text (pre/code style) */
.card .inner {
    background: rgba(3,7,12,0.45);
    padding: 1rem;
    border-radius: 8px;
    color: #dbe9ff;
    font-family: "Courier New", monospace;
    white-space: pre-wrap;
}

/* badges */
.badge {
    display:inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    margin-right: 0.5rem;
    margin-bottom: 0.45rem;
    color: white;
}
.badge-type { background:#7c5cff; }
.badge-time { background:#1f2937; color:#c7d2fe; }
.badge-mode { background:#052e16; color:#86efac; }

/* score and view button row */
.row-actions {
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-top:0.75rem;
}
.score {
    font-weight:700;
    color:#f59e0b;
    font-size:1.05rem;
}
.view-btn{
    background:transparent;
    border:1px solid rgba(255,255,255,0.08);
    padding:0.45rem 0.9rem;
    border-radius:8px;
    color:#cfe7ff;
    text-decoration:none;
}
.view-btn:hover{ border-color: rgba(255,255,255,0.14); }

/* Skeleton placeholders */
.skeleton {
    height:68px;
    border-radius:10px;
    margin-bottom:12px;
    background: linear-gradient(90deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.03) 40%, rgba(255,255,255,0.02) 100%);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.01);
}

/* Insights section title */
.section-title {
    background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border-radius:10px;
    padding:10px 14px;
    margin-top:8px;
    margin-bottom:12px;
}

/* Footer text color */
.footer { color:#9fb0d3; font-size:0.9rem; margin-top:18px; text-align:center; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- HEADER ----------------
st.markdown(
    """
<div class="header">
    <h1>🎯 SHL Assessment Finder</h1>
    <p>AI-powered assessment recommendations for hiring managers</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("### 🔍 Filters")
    query = st.text_input("Job role / requirement", value="Data Analyst", help="e.g. Software Engineer, Data Analyst")
    top_k = st.slider("Number of results", min_value=1, max_value=20, value=10)
    max_duration = st.slider("Max duration (minutes)", min_value=15, max_value=90, value=60, step=5)
    min_score = st.slider("Minimum relevance score (%)", min_value=0, max_value=100, value=0)
    remote_only = st.checkbox("Remote testing only", value=False)
    st.markdown("---")
    search = st.button("Find Assessments", help="Call backend and fetch recommended assessments")

# ---------------- SKELETON ----------------
def show_skeleton(count: int = 3):
    for _ in range(count):
        st.markdown('<div class="skeleton"></div>', unsafe_allow_html=True)

# ---------------- SEARCH LOGIC ----------------
if search:
    with st.spinner("🔎 Analyzing requirements and fetching recommendations..."):
        # show improved dark skeleton
        show_skeleton(3)
        try:
            payload = {
                "query": query,
                "top_k": top_k,
                "max_duration": max_duration,
                "remote_only": remote_only,
            }
            resp = requests.post(API_URL, json=payload, timeout=25)
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend. Make sure FastAPI is running at http://localhost:8000")
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error while calling backend: {e}")
            st.stop()

    if resp.status_code != 200:
        st.error(f"Backend returned error {resp.status_code}: {resp.text}")
        st.stop()

    # normalize and sanitize
    data = resp.json()
    raw_recs = data.get("recommendations", [])
    recs = normalize_recs(raw_recs)

    # client-side filters (duration, min score, remote)
    filtered = []
    for r in recs:
        # duration filter
        dur = r.get("Duration")
        if dur is not None and isinstance(dur, (int, float)):
            if dur > max_duration:
                continue
        # min score filter
        if r.get("Relevance Score", 0.0) < float(min_score):
            continue
        # remote only filter
        if remote_only and r.get("Remote Testing Support", "").lower() != "yes":
            continue
        filtered.append(r)

    total_found = data.get("total_found", len(recs))
    st.success(f"Found {len(filtered)} matched assessments (total catalog matches: {total_found})")

    # ---------------- CARDS ----------------
    for r in filtered:
        # build the card as HTML but with sanitized values (no raw HTML inserted)
        name = r["Assessment Name"]
        tt = r["Test Type"]
        dur = r["Duration"] if r["Duration"] is not None else "N/A"
        mode = "Remote" if r["Remote Testing Support"].lower() == "yes" else "On-site"
        skills = r["Skills"] or "—"
        desc = r["Description"] or ""
        score = r["Relevance Score"]
        url = r["URL"] or "#"

        card_html = f"""
        <div class="card">
            <h3 style="margin:0 0 8px 0; color:#dbe9ff;">{name}</h3>
            <div style="margin-bottom:8px;">
                <span class="badge badge-type">{tt}</span>
                <span class="badge badge-time">⏱ {dur} min</span>
                <span class="badge badge-mode">{mode}</span>
            </div>
            <div style="margin-top:6px;">
                <p style="margin:6px 0;"><strong>Skills:</strong> {skills}</p>
                <p style="margin:6px 0; color:var(--muted,#9fb0d3);">{desc}</p>
            </div>
            <div class="row-actions">
                <div class="score">Score: {score:.1f}%</div>
                <div><a class="view-btn" href="{url}" target="_blank" rel="noopener noreferrer">View Assessment</a></div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    # ---------------- CHARTS ----------------
    if len(filtered) > 0:
        df = pd.DataFrame(filtered)

        st.markdown('<div class="section-title"><b>📊 Insights</b></div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])

        with col1:
            # Pie chart for test-type distribution
            fig1 = px.pie(
                df,
                names="Test Type",
                title="Assessment Types Distribution",
                template="plotly_dark",
                hole=0.45,
            )
            # updated plotting call (no use_container_width)
            st.plotly_chart(fig1, width="stretch", use_container_width=False)

        with col2:
            # Duration histogram
            # ensure Duration is numeric
            dur_series = pd.to_numeric(df["Duration"], errors="coerce").dropna()
            if dur_series.empty:
                st.info("No duration data for insights.")
            else:
                hist = px.histogram(
                    dur_series,
                    nbins=6,
                    title="Duration Histogram (minutes)",
                    labels={"value": "Duration (min)"},
                    template="plotly_dark",
                )
                st.plotly_chart(hist, width="stretch", use_container_width=False)

    else:
        st.info("No results after applying filters. Try widening filters or lowering the minimum relevance score.")

# ---------------- FOOTER ----------------
st.markdown(
    """
<div class="footer">
    SHL Assessment Finder • By Shubam Kumar • © 2025<br>
     <a href="https://github.com/shubamkumar" target="_blank" rel="noopener noreferrer" style="margin-right:12px; text-decoration:none; color:inherit;">
        <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="20" style="vertical-align:middle; margin-right:6px;">GitHub
    </a>
    <a href="https://www.linkedin.com/in/shubam-kumar" target="_blank" rel="noopener noreferrer" style="margin-right:12px; text-decoration:none; color:inherit;">
        <img src="https://cdn.worldvectorlogo.com/logos/linkedin-icon-2.svg" width="20" style="vertical-align:middle; margin-right:6px;">LinkedIn
    </a>
    <a href="mailto:shubam.kumar@example.com" style="text-decoration:none; color:inherit;">
        <img src="https://cdn-icons-png.flaticon.com/512/732/732200.png" width="20" style="vertical-align:middle; margin-right:6px;">Email
    </a>
</div>
""",
    unsafe_allow_html=True,
)
