import json
import numpy as np
import pandas as pd
import re
from bs4 import BeautifulSoup
import requests
from sentence_transformers import SentenceTransformer, util
import torch
from google import genai
from google.genai import types
import os

catalog_df = None
corpus = None
model = None
corpus_embeddings = None
gemini_client = None

def initialize_models():
    global catalog_df, corpus, model, corpus_embeddings, gemini_client
    
    if model is None:
        print("Loading SentenceTransformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
    
    if gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            gemini_client = genai.Client(api_key=api_key)
        else:
            print("Warning: GEMINI_API_KEY not found")
    
    if catalog_df is None:
        print("Loading SHL catalog...")
        catalog_df = pd.read_csv("SHL_catalog.csv")
        
        def combine_row(row):
            parts = [
                str(row["Assessment Name"]),
                str(row["Duration"]),
                str(row["Remote Testing Support"]),
                str(row["Adaptive/IRT"]),
                str(row["Test Type"]),
                str(row["Skills"]),
                str(row["Description"]),
            ]
            return ' '.join(parts)
        
        catalog_df['combined'] = catalog_df.apply(combine_row, axis=1)
        corpus = catalog_df['combined'].tolist()
        
        print("Generating corpus embeddings...")
        corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
        print("Initialization complete!")
    
    return catalog_df, corpus, model, corpus_embeddings, gemini_client

def extract_url_from_text(text):
    match = re.search(r'(https?://[^\s,]+)', text)
    if match:
        return match.group(1)
    return None

def extract_text_from_url(url):
    try:
        response = requests.get(url, headers={'User-Agent': "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return ' '.join(soup.get_text().split())
    except Exception as e:
        return f"Error: {e}"

def extract_features_with_llm(user_query):
    global gemini_client
    
    if gemini_client is None:
        return user_query
    
    prompt = f"""
You are an intelligent assistant helping to recommend SHL assessments.

The input below may be:
1. A natural language query describing assessment needs (e.g., "Need a Python test under 60 minutes").
2. A job description (JD) pasted directly.
3. A job description URL (already converted into text outside this function).
4. A combination of user query + JD.

Your task is to extract and summarize key hiring features from the input. Look for and include the following **if available**:

- Job Title  
- Duration of Test  
- Remote Testing Support (Yes/No)  
- Adaptive/IRT Format (Yes/No)  
- Test Type  
- Skills Required  
- Any other relevant hiring context

Format your response as a **single line** like this:

`<Job Title> <Duration> <Remote Support> <Adaptive> <Test Type> <Skills> <Other Info>`

Skip any fields not mentioned — do not include placeholders or "N/A".

---
Input:
{user_query}

Only return the final, clean sentence — no explanations.
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt
        )
        return response.text.strip() if response.text else user_query
    except Exception as e:
        print(f"Error extracting features: {e}")
        return user_query

def find_assessments(user_query, k=10):
    global model, corpus_embeddings, catalog_df
    
    initialize_models()
    
    query_embedding = model.encode(user_query, convert_to_tensor=True)
    cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
    top_k = min(k, len(corpus))
    top_results = torch.topk(cosine_scores, k=top_k)
    
    results = []
    for score, idx in zip(top_results[0], top_results[1]):
        idx = idx.item()
        result = {
            "Assessment Name": catalog_df.iloc[idx]['Assessment Name'],
            "Skills": catalog_df.iloc[idx]['Skills'],
            "Test Type": catalog_df.iloc[idx]['Test Type'],
            "Description": catalog_df.iloc[idx]['Description'],
            "Remote Testing Support": catalog_df.iloc[idx]['Remote Testing Support'],
            "Adaptive/IRT": catalog_df.iloc[idx]['Adaptive/IRT'],
            "Duration": catalog_df.iloc[idx]['Duration'],
            "URL": catalog_df.iloc[idx]['URL'],
            "Score": round(score.item(), 4)
        }
        results.append(result)
    return results

def convert_numpy(obj):
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    else:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def filter_relevant_assessments_with_llm(user_query, top_results):
    global gemini_client
    
    if gemini_client is None:
        return top_results
    
    prompt = f"""
You are helping to refine assessment recommendations based on user needs.

A user has entered the following query:
"{user_query}"

You are given 10 or less assessments retrieved using semantic similarity. 
Your task is to go through each assessment and determine if it truly matches the user's intent, based on the following:
- Duration match (e.g., if the user wants "< 40 mins", exclude longer ones)
- Skills match (e.g., user wants "Python" but test is on "Excel", reject it)
- Remote support, Adaptive format, Test type, or any clearly stated requirement
- Ignore irrelevant matches, even if score is high

Return only the assessments that are **highly relevant** to the query. 
Use your understanding of language and hiring to filter smartly. But you have to return something atleast 1 assessment.
You have to return minimum 1 assessment and maximum 10(only relevant ones). You cannot return empty json.

Respond in clean JSON format:
[
  {{
    "Assessment Name": "...",
    "Skills": "...",
    "Test Type": "...",
    "Description": "...",
    "Remote Testing Support": "...",
    "Adaptive/IRT": "...",
    "Duration": "... mins",
    "URL": "...",
    "Score": ...
  }},
  ...
]

---
Assessments:
{top_results}
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt
        )
        return response.text.strip() if response.text else top_results
    except Exception as e:
        print(f"Error filtering assessments: {e}")
        return top_results

def query_handling_using_LLM_updated(query):
    initialize_models()
    
    url = extract_url_from_text(query)
    
    if url:
        extracted_text = extract_text_from_url(url)
        if not extracted_text.startswith("Error"):
            query += " " + extracted_text
    
    user_query = extract_features_with_llm(query)
    
    top_results = find_assessments(user_query, k=10)
    
    top_json = json.dumps(top_results, indent=2, default=convert_numpy)
    
    filtered_output = filter_relevant_assessments_with_llm(user_query, top_json)
    
    if not filtered_output or not filtered_output.strip():
        print("Empty response from LLM.")
        return pd.DataFrame()
    
    try:
        if isinstance(filtered_output, str):
            match = re.search(r"\[.*\]", filtered_output, re.DOTALL)
            if match:
                json_str = match.group()
                filtered_results = json.loads(json_str)
            else:
                print("No valid JSON array found in the response")
                return pd.DataFrame(top_results)
        else:
            filtered_results = json.loads(filtered_output)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return pd.DataFrame(top_results)
    
    if not filtered_results:
        return pd.DataFrame(top_results)
    else:
        try:
            df = pd.DataFrame(filtered_results)
            return df
        except Exception as e:
            print(f"Error creating DataFrame: {e}")
            return pd.DataFrame()

def get_simple_recommendations(query, k=10):
    initialize_models()
    results = find_assessments(query, k=k)
    return pd.DataFrame(results)
