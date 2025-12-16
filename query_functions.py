import os
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class SHLRecommendationEngine:
    def __init__(self, catalog_path: str = "SHL_catalog.csv"):
        self.catalog = pd.read_csv(catalog_path)
        self.catalog.fillna('', inplace=True)
        self.model = None
        self.embeddings = None
        self.gemini_client = None
        self._initialize_model()
        self._initialize_gemini()
        
    def _initialize_model(self):
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self._compute_embeddings()
            except Exception as e:
                print(f"Warning: Could not load sentence transformer: {e}")
                self.model = None
    
    def _initialize_gemini(self):
        if GEMINI_AVAILABLE:
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key:
                try:
                    self.gemini_client = genai.Client(api_key=api_key)
                except Exception as e:
                    print(f"Warning: Could not initialize Gemini: {e}")
                    self.gemini_client = None
    
    def _compute_embeddings(self):
        if self.model is None:
            return
        texts = []
        for _, row in self.catalog.iterrows():
            text = f"{row['Assessment Name']} {row['Test Type']} {row['Skills']} {row.get('Description', '')}"
            texts.append(text)
        self.embeddings = self.model.encode(texts, convert_to_numpy=True)
    
    def _get_combined_text(self, row: pd.Series) -> str:
        return f"{row['Assessment Name']} {row['Test Type']} {row['Skills']} {row.get('Description', '')}"
    
    def extract_text_from_url(self, url: str) -> str:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
                tag.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            return text[:5000]
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def extract_job_requirements(self, text: str) -> Dict[str, Any]:
        if self.gemini_client:
            try:
                prompt = f"""Analyze this job description and extract the key requirements.
Return a JSON object with these fields:
- skills: list of required technical and soft skills
- experience_level: junior/mid/senior
- test_types: list of relevant assessment types (Coding, Cognitive, Personality, Communication, Aptitude)
- duration_preference: short (<30 min), medium (30-45 min), or long (>45 min)
- key_responsibilities: list of main job responsibilities

Job Description:
{text[:3000]}

Return only valid JSON, no markdown formatting."""
                
                response = self.gemini_client.models.generate_content(
                    model='models/gemini-2.0-flash',
                    contents=prompt
                )
                
                import json
                result_text = response.text.strip()
                if result_text.startswith('```'):
                    result_text = re.sub(r'^```json?\n?', '', result_text)
                    result_text = re.sub(r'\n?```$', '', result_text)
                return json.loads(result_text)
            except Exception as e:
                print(f"Gemini extraction failed: {e}")
        
        skills = []
        skill_patterns = [
            r'\b(python|java|javascript|sql|react|node\.?js|angular|typescript)\b',
            r'\b(problem solving|communication|teamwork|leadership|analytical)\b',
            r'\b(data analysis|machine learning|cloud|aws|azure|gcp)\b'
        ]
        
        text_lower = text.lower()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.extend(matches)
        
        return {
            'skills': list(set(skills)),
            'experience_level': 'mid',
            'test_types': ['Coding', 'Cognitive'],
            'duration_preference': 'medium',
            'key_responsibilities': []
        }
    
    def semantic_search(self, query: str, top_k: int = 10) -> pd.DataFrame:
        if self.model is None or self.embeddings is None:
            return self._keyword_search(query, top_k)
        
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
        
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = self.catalog.iloc[top_indices].copy()
        results['Relevance Score'] = [round(similarities[i] * 100, 1) for i in top_indices]
        
        return results
    
    def _keyword_search(self, query: str, top_k: int = 10) -> pd.DataFrame:
        query_terms = query.lower().split()
        scores = []
        
        for _, row in self.catalog.iterrows():
            combined = self._get_combined_text(row).lower()
            score = sum(1 for term in query_terms if term in combined)
            scores.append(score)
        
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = self.catalog.iloc[top_indices].copy()
        max_score = max(scores) if max(scores) > 0 else 1
        results['Relevance Score'] = [round((scores[i] / max_score) * 100, 1) for i in top_indices]
        
        return results
    
    def filter_by_duration(self, df: pd.DataFrame, max_duration: int) -> pd.DataFrame:
        return df[df['Duration'].astype(int) <= max_duration]
    
    def filter_by_test_type(self, df: pd.DataFrame, test_types: List[str]) -> pd.DataFrame:
        if not test_types:
            return df
        return df[df['Test Type'].isin(test_types)]
    
    def filter_by_remote(self, df: pd.DataFrame, remote_only: bool = True) -> pd.DataFrame:
        if remote_only:
            return df[df['Remote Testing Support'] == 'Yes']
        return df
    
    def get_recommendations(
        self,
        query: str = None,
        url: str = None,
        max_duration: int = None,
        test_types: List[str] = None,
        remote_only: bool = False,
        top_k: int = 10
    ) -> Dict[str, Any]:
        search_query = query
        job_requirements = None
        
        if url:
            extracted_text = self.extract_text_from_url(url)
            if not extracted_text.startswith("Error"):
                job_requirements = self.extract_job_requirements(extracted_text)
                if job_requirements.get('skills'):
                    search_query = ' '.join(job_requirements['skills'])
                    if job_requirements.get('test_types') and not test_types:
                        test_types = job_requirements['test_types']
        
        if not search_query:
            results = self.catalog.head(top_k).copy()
            results['Relevance Score'] = [100.0] * len(results)
        else:
            results = self.semantic_search(search_query, top_k=min(top_k * 2, 50))
        
        if max_duration:
            results = self.filter_by_duration(results, max_duration)
        if test_types:
            results = self.filter_by_test_type(results, test_types)
        if remote_only:
            results = self.filter_by_remote(results, remote_only)
        
        results = results.head(top_k)
        
        return {
            'recommendations': results.to_dict('records'),
            'job_requirements': job_requirements,
            'search_query': search_query,
            'total_found': len(results)
        }
    
    def get_test_types(self) -> List[str]:
        return sorted(self.catalog['Test Type'].unique().tolist())
    
    def get_catalog_stats(self) -> Dict[str, Any]:
        return {
            'total_assessments': len(self.catalog),
            'test_types': self.catalog['Test Type'].value_counts().to_dict(),
            'avg_duration': round(self.catalog['Duration'].astype(int).mean(), 1),
            'remote_supported': (self.catalog['Remote Testing Support'] == 'Yes').sum(),
            'adaptive_tests': (self.catalog['Adaptive/IRT'] == 'Yes').sum()
        }


engine = None

def get_engine() -> SHLRecommendationEngine:
    global engine
    if engine is None:
        engine = SHLRecommendationEngine()
    return engine
