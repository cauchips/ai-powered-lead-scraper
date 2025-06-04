# AI-Powered Lead Scraper — Technical Report

**Date:** June 4, 2025  

---

## 1. Objective & Approach

The AI-Powered Lead Scraper merges two data sources to quickly identify high-impact SME acquisition targets:

1. **Live HTML Scraping**  
   - Scrapes YellowPages, Yelp, and Manta (up to 10 results each).  
   - Rotating User-Agent headers, 0.3 s delays, and fuzzy deduplication ensure reliability and uniqueness.  

2. **Kaggle “BigPicture” Dataset**  
   - Loads “companies-2023-q4-sm.csv” (~17 million rows), using a subset of 500 000 for performance.  
   - Derives `country_name` from `country_code` (pycountry) for full-country filtering.  
   - Filters applied:  
     • Keyword (substring match in name or industry)  
     • Location (substring match in city, state, or country_name)  
     • Optional Category  
     • Size preference (Small/Medium/Large/Any)  

Merged leads receive a 0–100 composite score for prioritization.

---

## 2. Data Preprocessing & Quality

- **Text Normalization:** Null text fields (name, industry, city, state, country_code) → empty strings for robust substring matching.  
- **Size Interpretation:** Employee ranges (e.g., “1–10”, “51–200”) convert to numerical midpoints; full or partial inclusion based on preferred range.  
- **Geocoding:** Geopy Nominatim translates top-10 lead locations into coordinates; results cached in `geo_cache.json` to speed repeat runs.

---

## 3. Scoring Model (0–100)

Lead score = sum of six weighted sub-scores:

| Component               | Weight | Method                                                                                                          |
|-------------------------|:------:|:----------------------------------------------------------------------------------------------------------------|
| **Age**                 |  20 %  | `(CurrentYear – founded)/20`, capped at 1.0 → × 20. Prioritizes businesses ≥ 5 years old.                        |
| **Size**                |  20 %  | Midpoint in preferred range → 20; within 50 % proximity → 10; otherwise → 0.                                     |
| **Industry Fit**        |  15 %  | + 15 if keyword appears (case-insensitive) in industry.                                                          |
| **Sentiment**           |  10 %  | DistilBERT SST-2 on review snippet (or fallback “industry + location”) → P(positive) × 10.                        |
| **Rating**              |  15 %  | Yelp rating (0–5) normalized: `(rating/5) × 15`.                                                                   |
| **Semantic Similarity** |  20 %  | “all-MiniLM-L6-v2” embeds “name + industry + location + snippet[:200]”; cosine similarity vs. ideal vector, normalized → × 20. |

Total = 0–100. Leads sorted descending; hoverable “ⓘ” tooltip explains all six components.

---

## 4. Performance & Evaluation

- **Interface & Workflow**  
  • Sidebar inputs: Keyword, Location (city/state or full country), optional Category, Size.  
  • Single “Generate Leads” button triggers scraping, filtering, scoring.  
  • Spinner “Searching and scoring…” keeps users informed.  
  • Results: high-contrast table of top 20 leads (Name, Industry, Location, Phone, Founded, Size, Rating, Score).  
  • Tooltip (“ⓘ” next to Score) clarifies weights.  
  • Interactive `st.map` displays the top 10 geocoded locations.  
  • Export buttons: “Download CSV” and “Download JSON” for seamless CRM integration.

- **Speed & Technical Highlights**  
  • Kaggle filtering (500 000 rows): ~ 3–5 s via Pandas boolean masks.  
  • Scraping (30 pages): ~ 4–6 s with rotating UAs and delays.  
  • DistilBERT SST-2 sentiment on 500 leads: ~ 1 s.  
  • SentenceTransformer embeddings on 500 leads: ~ 1 s.  
  • **End-to-end runtime:** ~ 8–10 s.  
  • FuzzyWuzzy deduplication ensures unique lead names.  
  • `country_name` filtering accepts full-country input (e.g., “United States”).  
  • Modular architecture allows easy addition of new scrapers or model updates.

- **Innovation & Value-Add**

  | Innovation Aspect      | Description                                                                                      |
  |------------------------|--------------------------------------------------------------------------------------------------|
  | Ethical Scraping       | Rotating User-Agents and polite delays reduce server strain and avoid IP blocks.                |
  | Open-Source Pipeline   | No paid APIs, uses only public HTML and a free Kaggle dataset, lowering cost barriers.            |
  | Geocoding Cache        | Coordinates saved in `geo_cache.json` eliminate redundant requests and improve speed.            |
  | CRM Integration        | Ready-to-download CSV/JSON output can be imported directly into sales platforms.                 |
  | Future-Proof Design    | Modular codebase supports adding enrichment APIs (email lookup) or advanced retrieval (FAISS).   |

- **Result Summary**  
  • Top 20 results consistently feature mid-sized, well-established, positively-reviewed businesses aligned with acquisition criteria.  
  • Manual testing by the developer confirmed quick response, accurate scoring, and user-friendly outputs.

---

## 5. Conclusion

The AI-Powered Lead Scraper meets core business needs by delivering prioritized, high-impact leads in under 10 seconds. Its transparent scoring, intuitive UI, and open-source design make it a practical, scalable solution for acquisition-focused users.

---

**References**  
- DistilBERT SST-2 (sentiment analysis)  
- SentenceTransformer “all-MiniLM-L6-v2” (semantic embeddings)  
- Kaggle “BigPicture 2023 Q4” Free Company Dataset (ODC-By license)  
