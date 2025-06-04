from datetime import datetime
from src.llm import sentiment_score
from sentence_transformers import SentenceTransformer
import numpy as np

CURRENT_YEAR = datetime.now().year
embedder = SentenceTransformer("all-MiniLM-L6-v2")
ideal_vec = embedder.encode(
    ["owner-operated small business established over five years ago"],
    convert_to_numpy=True,
    normalize_embeddings=True
)[0]

# Weights must sum to 100
WEIGHTS = {
    "age": 20,
    "size": 20,
    "industry": 15,
    "sentiment": 10,
    "rating": 15,
    "semantic": 20
}

def compute_age_score(founded):
    if not founded or founded <= 0:
        return 0.0
    years = CURRENT_YEAR - founded
    return min(years / 20.0, 1.0) * WEIGHTS["age"]

def compute_size_score(size_val, preferred_range):
    if size_val is None:
        return 0.0
    if not preferred_range:
        return WEIGHTS["size"] * 0.5
    low, high = preferred_range
    if low <= size_val <= high:
        return float(WEIGHTS["size"])
    # Within 50% proximity → half score
    if (size_val < low and (low - size_val) <= (0.5 * low)) or \
       (size_val > high and (size_val - high) <= (0.5 * high)):
        return WEIGHTS["size"] * 0.5
    return 0.0

def compute_industry_score(industry_text, keyword_lower):
    if industry_text and keyword_lower in industry_text.lower():
        return float(WEIGHTS["industry"])
    return 0.0

def compute_sentiment_score(lead):
    try:
        prob_pos = sentiment_score(lead)  # 0–1 from DistilBERT SST-2
        return prob_pos * WEIGHTS["sentiment"]
    except:
        return 0.0

def compute_rating_score(rating):
    if rating is None or rating < 0:
        return 0.0
    return min(rating / 5.0, 1.0) * WEIGHTS["rating"]

def compute_semantic_score(lead):
    snippet = lead.get("snippet") or ""
    text = f"{lead.get('name')} {lead.get('industry')} {lead.get('location')} {snippet[:200]}"
    vec = embedder.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
    sim = float(np.dot(vec, ideal_vec))  # cosine similarity
    normalized = max((sim - 0.6) / (1 - 0.6), 0.0)
    return normalized * WEIGHTS["semantic"]

def score_company_row(row, keyword_lower, preferred_range=None):
    age = row.get("year_founded")
    if age is None and "founded" in row:
        age = row.get("founded")
    size_val = row.get("size")
    industry_text = row.get("industry", "")

    age_score = compute_age_score(age)
    size_score = compute_size_score(size_val, preferred_range)
    industry_score = compute_industry_score(industry_text, keyword_lower)
    sentiment_sc = compute_sentiment_score(row)
    rating_score = compute_rating_score(row.get("rating"))
    semantic_sc = compute_semantic_score(row)

    total = age_score + size_score + industry_score + sentiment_sc + rating_score + semantic_sc
    return round(total, 2)

def score_leads(leads, preferred_range=None):
    scored = []
    for lead in leads:
        row = {
            "name": lead.get("name"),
            "industry": lead.get("industry"),
            "location": lead.get("location"),
            "rating": lead.get("rating"),
            "snippet": lead.get("snippet"),
            "year_founded": lead.get("year_founded"),
            "founded": lead.get("year_founded"),
            "size": lead.get("size")
        }
        score = score_company_row(row, lead.get("industry", ""), preferred_range)
        lead["score"] = score
        scored.append(lead)
    return sorted(scored, key=lambda x: x["score"], reverse=True)
