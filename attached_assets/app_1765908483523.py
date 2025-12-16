import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="SHL Assessment Recommendation System",
    page_icon="brain",
    layout="wide"
)

st.markdown(
    """
    <style>
        .main-header {
            text-align: center;
            color: #4B8BBE;
            margin-bottom: 10px;
        }
        .sub-header {
            text-align: center;
            color: #888;
            margin-bottom: 20px;
        }
        table.custom-table {
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
        }
        table.custom-table thead {
            background-color: #2e2e2e;
            color: white;
        }
        table.custom-table th, table.custom-table td {
            border: 1px solid #444;
            padding: 10px;
            text-align: left;
            vertical-align: top;
        }
        table.custom-table tr:nth-child(even) {
            background-color: #1e1e1e;
        }
        table.custom-table tr:nth-child(odd) {
            background-color: #2a2a2a;
        }
        a {
            color: #1a73e8;
            text-decoration: none;
        }
        .stButton > button {
            background-color: #4B8BBE;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            font-weight: bold;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 class='main-header'>SHL Assessment Recommendation System</h1>", unsafe_allow_html=True)
st.markdown("<h4 class='sub-header'>Find the best assessments based on your query using AI!</h4>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.warning("GEMINI_API_KEY not found. The system will use basic semantic search without LLM enhancement. Add your API key for better results.")
    use_llm = False
else:
    use_llm = True
    st.success("Connected to Gemini AI for enhanced recommendations")

tab1, tab2 = st.tabs(["Search Query", "Job Description URL"])

with tab1:
    query = st.text_area(
        "Enter your search query:",
        placeholder="e.g., I need a Python coding test under 40 minutes with remote testing support",
        height=100
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        num_results = st.selectbox("Max Results", [5, 10, 15, 20], index=1)
    
    search_button = st.button("Search", key="search_query")

with tab2:
    url_input = st.text_input(
        "Enter job description URL:",
        placeholder="https://example.com/job-posting"
    )
    
    url_button = st.button("Fetch & Analyze", key="search_url")

def display_results(df):
    if df is None or df.empty:
        st.warning("No assessments matched your query. Try rephrasing it!")
        return
    
    if 'Score' in df.columns:
        df = df.drop(columns=['Score'])
    
    if "Duration" in df.columns:
        df = df.rename(columns={"Duration": "Duration (mins)"})
    
    display_cols = ["Assessment Name", "Skills", "Test Type", "Description", 
                    "Remote Testing Support", "Adaptive/IRT", "Duration (mins)", "URL"]
    df = df[[col for col in display_cols if col in df.columns]]
    
    df['URL'] = df['URL'].apply(
        lambda x: f"<a href='{x}' target='_blank'>View</a>" if pd.notna(x) else ""
    )
    
    st.success(f"Found {len(df)} assessment recommendations:")
    
    table_html = """
    <table class="custom-table">
        <thead>
            <tr>
    """
    
    for col in df.columns:
        table_html += f"<th>{col}</th>"
    table_html += "</tr></thead><tbody>"
    
    for _, row in df.iterrows():
        table_html += "<tr>"
        for cell in row:
            table_html += f"<td>{cell}</td>"
        table_html += "</tr>"
    
    table_html += "</tbody></table>"
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if "Test Type" in df.columns:
        test_types = df["Test Type"].value_counts()
        st.subheader("Test Type Distribution")
        st.bar_chart(test_types)

if search_button and query.strip():
    with st.spinner("Finding the best assessments for you..."):
        try:
            from query_functions import query_handling_using_LLM_updated, get_simple_recommendations
            
            if use_llm:
                df = query_handling_using_LLM_updated(query)
            else:
                df = get_simple_recommendations(query, k=num_results)
            
            display_results(df)
            
        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())

elif search_button:
    st.warning("Please enter a valid query.")

if url_button and url_input.strip():
    with st.spinner("Fetching job description from URL..."):
        try:
            from query_functions import extract_text_from_url, query_handling_using_LLM_updated, get_simple_recommendations
            
            extracted_text = extract_text_from_url(url_input)
            
            if extracted_text.startswith("Error"):
                st.error(f"Failed to fetch URL: {extracted_text}")
            else:
                st.info("Extracted job description:")
                with st.expander("View extracted text"):
                    st.text(extracted_text[:2000] + "..." if len(extracted_text) > 2000 else extracted_text)
                
                with st.spinner("Analyzing and finding matching assessments..."):
                    if use_llm:
                        df = query_handling_using_LLM_updated(extracted_text)
                    else:
                        df = get_simple_recommendations(extracted_text, k=10)
                    
                    display_results(df)
                    
        except Exception as e:
            st.error(f"Error: {e}")

elif url_button:
    st.warning("Please enter a valid URL.")

st.markdown("---")

with st.expander("About this Application"):
    st.markdown("""
    ### SHL Assessment Recommendation System
    
    This application helps hiring managers find the right SHL assessments for their roles.
    
    **Features:**
    - Natural language query processing
    - Job description URL analysis
    - AI-powered semantic search
    - LLM-enhanced filtering for relevant results
    
    **How to use:**
    1. Enter a query describing your assessment needs (e.g., "Python developer test under 30 minutes")
    2. Or paste a job description URL to automatically extract requirements
    3. Click Search to get personalized recommendations
    
    **Tips for better results:**
    - Include specific skills (Python, Java, SQL, etc.)
    - Mention duration requirements (under 40 minutes)
    - Specify if you need remote testing support
    - Include job title or role description
    """)

with st.expander("API Usage"):
    st.markdown("""
    ### REST API Endpoints
    
    The FastAPI backend provides the following endpoints:
    
    **POST /recommend**
    ```json
    {
        "query": "your search query or job description"
    }
    ```
    
    **GET /health**
    Returns API health status.
    
    Run the API server with: `python main.py`
    """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #888;'>SHL Assessment Recommendation Engine | Built with Streamlit</p>", unsafe_allow_html=True)
