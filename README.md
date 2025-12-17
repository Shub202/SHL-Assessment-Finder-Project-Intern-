## 🎯 SHL Assessment Finder
## AI-Powered Assessment Recommendation System

## An end-to-end AI system that scrapes, understands, and recommends SHL assessments using semantic search, embeddings, and LLM-assisted query understanding, delivered through a FastAPI backend and a Streamlit frontend.

# 🚀 Live Demo
# 🔗 https://nonalgebraical-tesha-multiplicational.ngrok-free.dev/

📌 Features
🔎 Natural-language job requirement search

🧠 Semantic search using Sentence Transformers

🤖 LLM-assisted query understanding (Gemini / RAG ready)

🧪 SHL catalog scraping & parsing pipeline

⚡ FastAPI backend with JSON API

🎨 Polished Streamlit UI with cards, charts & filters

📊 Insights: test-type distribution & duration analysis

🧠 Architecture Overview

SHL Website
   ↓ (Scraping & Parsing)
Assessment Catalog (CSV / DataFrame)
   ↓
Sentence Transformer Embeddings
   ↓
Similarity Search + LLM Query Understanding
   ↓
FastAPI Recommendation API
   ↓
Streamlit Frontend


🖥️ Web App Screenshots

🔹 Main Dashboard

🔹 Assessment Recommendations

🔹 Insights & Charts

📌 Place images inside an assets/ folder in your repo.

https://github.com/Shub202/SHL-Assessment-Finder-Project-Intern-/blob/main/Output1.png

🎥 Project Video


⚙️ Tech Stack
Layer	Technology

Frontend	Streamlit

Backend	FastAPI

Embeddings	sentence-transformers (MiniLM)

LLM	Gemini / RAG (optional)

Scraping	BeautifulSoup, Trafilatura

Visualization	Plotly

Deployment	Streamlit Cloud

📡 API Endpoints

🔹 Health Check
GET /health

🔹 Get Recommendations
POST /recommend

Request Body

{
  "query": "Data Analyst with SQL skills",
  
  "top_k": 5,
  
  "max_duration": 60,
  
  "remote_only": true
}

Response

{
  "total_found": 5,
  
  "recommendations": [
  
    {
      "Assessment Name": "Data Analyst Screening",
      "Duration": 45,
      "Test Type": "Cognitive",
      "Skills": "SQL",
      "Relevance Score": 46.9,
      "URL": "https://shl.com/assessment/3"
    }
  ]
}


🧪 Evaluation Methodology

Embedding Similarity Scores for ranking relevance

Top-K Precision Review

Manual Validation against SHL categories

Duration & Skill Match Constraints

Future improvements:

Ground-truth labels

NDCG / MAP metrics

Human-in-the-loop evaluation

🛠️ Local Setup

1️⃣ Clone Repository
cd SHL-Assessment-Finder

2️⃣ Create Virtual Environment
## python -m venv .venv
## .venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Run FastAPI Backend

(.venv) PS E:\Assessment-Engine> uvicorn main:app --reload

>>
>>
INFO:     Will watch for changes in these directories:

## INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

INFO:     Started reloader process [25368] using StatReload

INFO:     Started server process [18224]

INFO:     Waiting for application startup.

INFO:     Application startup complete.

INFO:     127.0.0.1:51878 - "GET / HTTP/1.1" 200 OK

INFO:     127.0.0.1:57656 - "POST /recommend HTTP/1.1" 200 OK

INFO:     127.0.0.1:60770 - "POST /recommend HTTP/1.1" 200 OK

INFO:     127.0.0.1:64459 - "POST /recommend HTTP/1.1" 200 OK


5️⃣ Run Streamlit Frontend

(.venv) PS E:\Assessment-Engine> cd E:\Assessment-Engine

>> .venv\Scripts\activate

## >> streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1

>> 

  You can now view your Streamlit app in your browser.

  ## URL: http://127.0.0.1:8501


## Repo link : https://github.com/Shub202/SHL-Assessment-Finder-Project-Intern-.git

Main file: streamlit_app.py

📂 Repository Structure

├── streamlit_app.py

├── main.py

├── query_functions.py


├── requirements.txt


├── assets/

│   ├── dashboard.png

│   ├── results.png

│   └── insights.png


├── README.md


👤 Author

Shubham Kumar

# 🔗 GitHub: https://github.com/Shub202


✅ Submission Checklist

✔️ Web app URL

✔️ API endpoint

✔️ GitHub code

✔️ Evaluation included

✔️ README + screenshots + video

✔️ Production-ready UI

