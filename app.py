import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from query_functions import get_engine
import os

st.set_page_config(
    page_title="SHL Assessment Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1a1f71 0%, #4a2c7e 50%, #7b2d8e 100%);
        padding: 2rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: white;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0;
    }
    
    .search-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
    }
    
    .assessment-card {
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
        transition: all 0.2s ease;
    }
    
    .assessment-card:hover {
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
        border-color: #6366f1;
    }
    
    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1f71;
        margin-bottom: 0.5rem;
    }
    
    .card-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }
    
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .badge-purple {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
    }
    
    .badge-blue {
        background: #e0e7ff;
        color: #3730a3;
    }
    
    .badge-green {
        background: #d1fae5;
        color: #065f46;
    }
    
    .badge-orange {
        background: #fed7aa;
        color: #9a3412;
    }
    
    .score-indicator {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    .score-high {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
    }
    
    .score-medium {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
    }
    
    .score-low {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        padding: 1.25rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1f71;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.25rem;
    }
    
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    
    .sidebar .stSelectbox label, .sidebar .stSlider label {
        font-weight: 500;
        color: #374151;
    }
    
    div[data-testid="stExpander"] {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
    }
    
    .requirements-box {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #f59e0b;
        margin-bottom: 1rem;
    }
    
    a {
        color: #6366f1;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>SHL Assessment Finder</h1>
    <p>AI-powered assessment recommendations for smarter hiring decisions</p>
</div>
""", unsafe_allow_html=True)

@st.cache_resource
def load_engine():
    return get_engine()

engine = load_engine()

with st.sidebar:
    st.markdown("### Search Options")
    
    search_mode = st.radio(
        "Search Method",
        ["Natural Language Query", "Job Description URL"],
        help="Choose how you want to search for assessments"
    )
    
    st.markdown("---")
    st.markdown("### Filters")
    
    test_types = engine.get_test_types()
    selected_types = st.multiselect(
        "Assessment Types",
        options=test_types,
        default=[],
        help="Filter by specific assessment categories"
    )
    
    max_duration = st.slider(
        "Maximum Duration (minutes)",
        min_value=15,
        max_value=90,
        value=60,
        step=5,
        help="Filter assessments by maximum time"
    )
    
    remote_only = st.checkbox(
        "Remote Testing Only",
        value=False,
        help="Show only assessments that support remote testing"
    )
    
    num_results = st.slider(
        "Number of Results",
        min_value=1,
        max_value=20,
        value=10,
        help="How many recommendations to show"
    )
    
    st.markdown("---")
    
    stats = engine.get_catalog_stats()
    st.markdown("### Catalog Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Tests", stats['total_assessments'])
        st.metric("Remote Ready", stats['remote_supported'])
    with col2:
        st.metric("Avg Duration", f"{stats['avg_duration']}m")
        st.metric("Adaptive", stats['adaptive_tests'])

col1, col2 = st.columns([3, 1])

with col1:
    if search_mode == "Natural Language Query":
        query = st.text_area(
            "Describe what you're looking for",
            placeholder="e.g., 'I need assessments for a senior Python developer who will work with SQL databases and needs strong problem-solving skills'",
            height=100,
            key="query_input"
        )
        url = None
    else:
        url = st.text_input(
            "Enter Job Description URL",
            placeholder="https://example.com/job/senior-developer",
            key="url_input"
        )
        query = None

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_button = st.button("🔍 Find Assessments", use_container_width=True)

if search_button:
    if (search_mode == "Natural Language Query" and query) or (search_mode == "Job Description URL" and url):
        with st.spinner("Analyzing and finding the best assessments..."):
            results = engine.get_recommendations(
                query=query,
                url=url,
                max_duration=max_duration,
                test_types=selected_types if selected_types else None,
                remote_only=remote_only,
                top_k=num_results
            )
        
        if results.get('job_requirements'):
            req = results['job_requirements']
            st.markdown("### 📋 Extracted Job Requirements")
            
            with st.expander("View Extracted Information", expanded=True):
                cols = st.columns(3)
                
                with cols[0]:
                    st.markdown("**Skills Identified:**")
                    if req.get('skills'):
                        for skill in req['skills'][:8]:
                            st.markdown(f"• {skill}")
                
                with cols[1]:
                    st.markdown("**Experience Level:**")
                    st.markdown(f"🎯 {req.get('experience_level', 'Not specified').title()}")
                    
                    st.markdown("**Duration Preference:**")
                    st.markdown(f"⏱️ {req.get('duration_preference', 'Medium').title()}")
                
                with cols[2]:
                    st.markdown("**Suggested Test Types:**")
                    for tt in req.get('test_types', [])[:4]:
                        st.markdown(f"• {tt}")
        
        st.markdown(f"### 🎯 Recommended Assessments ({results['total_found']} found)")
        
        if results['recommendations']:
            for i, rec in enumerate(results['recommendations']):
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        score = rec.get('Relevance Score', 0)
                        score_class = "score-high" if score >= 70 else "score-medium" if score >= 40 else "score-low"
                        
                        st.markdown(f"""
                        <div class="assessment-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div style="flex: 1;">
                                    <div class="card-title">
                                        <a href="{rec.get('URL', '#')}" target="_blank">{rec['Assessment Name']}</a>
                                    </div>
                                    <div class="card-meta">
                                        <span class="badge badge-purple">{rec['Test Type']}</span>
                                        <span class="badge badge-blue">⏱️ {rec['Duration']} min</span>
                                        <span class="badge badge-green">{'✓ Remote' if rec['Remote Testing Support'] == 'Yes' else '✗ On-site'}</span>
                                        {'<span class="badge badge-orange">Adaptive</span>' if rec['Adaptive/IRT'] == 'Yes' else ''}
                                    </div>
                                    <div style="color: #64748b; font-size: 0.9rem;">
                                        <strong>Skills:</strong> {rec['Skills']}
                                    </div>
                                    {f'<div style="color: #64748b; font-size: 0.85rem; margin-top: 0.5rem;">{rec["Description"][:150]}...</div>' if rec.get('Description') and len(str(rec.get('Description', ''))) > 10 else ''}
                                </div>
                                <div class="score-indicator {score_class}">
                                    {score:.0f}%
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📊 Results Analysis")
            
            results_df = pd.DataFrame(results['recommendations'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                type_counts = results_df['Test Type'].value_counts()
                fig_types = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="Assessment Types Distribution",
                    color_discrete_sequence=px.colors.sequential.Purples_r
                )
                fig_types.update_layout(
                    font_family="Inter",
                    title_font_size=14,
                    showlegend=True,
                    height=300
                )
                st.plotly_chart(fig_types, use_container_width=True)
            
            with col2:
                fig_duration = px.bar(
                    results_df.head(10),
                    x='Assessment Name',
                    y='Duration',
                    title="Duration Comparison (Top 10)",
                    color='Relevance Score',
                    color_continuous_scale='Purples'
                )
                fig_duration.update_layout(
                    font_family="Inter",
                    title_font_size=14,
                    xaxis_tickangle=-45,
                    height=300,
                    xaxis_title="",
                    yaxis_title="Duration (min)"
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        else:
            st.warning("No assessments found matching your criteria. Try adjusting your filters.")
    else:
        st.info("Please enter a search query or job description URL to find assessments.")

gemini_status = "🟢 AI-Enhanced" if os.environ.get('GEMINI_API_KEY') else "🟡 Basic Mode"
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #64748b; font-size: 0.85rem; padding: 1rem;">
    SHL Assessment Finder • {gemini_status} • Powered by Semantic Search
</div>
""", unsafe_allow_html=True)
