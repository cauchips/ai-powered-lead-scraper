# AI-Powered Lead Scraper

A free, data-driven Streamlit application that aggregates, enriches, and ranks high-impact business leads. This tool combines live HTML scraping (YellowPages, Yelp, Manta) with the “BigPicture” Kaggle dataset (~17 million global companies) to generate a top-20 list of acquisition-grade targets without paid APIs or subscriptions.

---

## 📂 Repository Structure
```
ai-powered-lead-scraper/  
├── app.py                 # Main Streamlit application  
├── style.css              # Optional custom CSS for UI styling  
├── requirements.txt       # Python dependencies  
├── deployment.ipynb       # Notebook for ngrok-based deployment  
├── data/  
│   └── companies-2023-q4-sm.csv  # company dataset from Kaggle (now being replaced by placeholder, download manually)  
└── src/  
    ├── data_loader.py     # Loads & preprocesses company dataset
    ├── scraper.py         # Live scrapers (YellowPages, Yelp, Manta)  
    ├── evaluation.py      # Scoring logic (Age, Size, Industry, Sentiment, Rating, Semantic)  
    ├── llm.py             # DistilBERT SST-2 for sentiment inference  
    └── utils.py           # JSON cache helper (for geocoding)  
```
---

## 🎯 Overview

### 1. Live Scraping

- Scrapes YellowPages, Yelp, and Manta (up to 10 results each) using rotating User-Agents, delays (0.3 s), and fuzzy deduplication.  
- Captures:  
  - `name`  
  - `industry`  
  - `location` (address string)  
  - `phone`  
  - `rating` (Yelp)  
  - `snippet` (Yelp review preview)  

### 2. Kaggle Dataset Filtering

- Uses “BigPicture 2023 Q4” CSV (~17 million entries).  
- Loads a configurable subset (default: first 500 000 rows).  
- Key columns:  
  - `name` (company)  
  - `industry`  
  - `size` (employee range, e.g. “1-10”, “51-200”)  
  - `founded` (year established)  
  - `city`, `state`, `country_code` → mapped to `country_name` via **pycountry**  
- Filters by:  
  - **Keyword** (substring match in `name` or `industry`)  
  - **Location** (substring match in `city`, `state`, or full `country_name`)  
  - **Optional Category** (filters both scraped and Kaggle sources)  
  - **Preferred Size** (Small 1–50, Medium 51–500, Large 501+, Any)  

### 3. Scoring Model (0–100)

A composite score for each lead, combining six weighted components:

| Component               | Weight | Calculation                                                                                                     |
|-------------------------|:------:|:-----------------------------------------------------------------------------------------------------------------|
| **Age**                 |  20%   | `(CurrentYear – founded) / 20`, capped at 1.0 → × 20                                                              |
| **Size**                |  20%   | In preferred range → 20; within 50% proximity → 10; otherwise 0                                                   |
| **Industry Fit**        |  15%   | +15 if keyword appears (case-insensitive) in `industry`                                                            |
| **Sentiment**           |  10%   | DistilBERT SST-2 predicts P(positive) on `snippet` (or fallback “industry + location”) → × 10                       |
| **Rating**              |  15%   | Yelp rating (0–5) normalized: `(rating / 5) × 15`                                                                  |
| **Semantic Similarity** |  20%   | SentenceTransformer (“all-MiniLM-L6-v2”) embeds lead text (`name` + `industry` + `location` + first 200 chars of snippet). Cosine similarity vs. “ideal target” → normalize to [0,1] → × 20. |

**Total Score** = sum of all components (0–100). Leads are sorted descending by score; top 20 are displayed. Hover over “ⓘ” next to **Score** for a breakdown.

### 4. Geocoding & Map

- Uses **Geopy Nominatim** (OpenStreetMap) to geocode up to the top 10 leads.  
- Caches coordinates in `geo_cache.json` to reduce repeated lookups.  
- Displays locations on an interactive `st.map`.

### 5. Export & Download

- **Download CSV** and **Download JSON** buttons export the top 20 leads for CRM integration or analysis.  
- Exported fields:  
  `Name`, `Industry`, `Location`, `Phone`, `Founded`, `Size`, `Rating`, `Score`.

---

## 🛠 Setup & Installation

### 1. Clone or Download

```bash  
git clone https://github.com/cauchips/ai-powered-lead-scraper.git 
cd ai-powered-lead-scraper  
```

### 2. Download the Kaggle CSV

- Visit:  
  https://www.kaggle.com/datasets/mfrye0/bigpicture-company-dataset/data  
- Download `companies-2023-q4-sm.csv` (approximately 2 GB).  
- Place it in the `data/` folder so the path is:  
        ```
         data/companies-2023-q4-sm.csv
         ```

### 3. Install Dependencies

```bash  
pip install -r requirements.txt  
```

Key packages include:  
- `streamlit`  
- `pandas`, `numpy`  
- `requests`, `beautifulsoup4`, `fuzzywuzzy`, `python-Levenshtein`  
- `geopy`  
- `sentence-transformers`, `torch`, `transformers`, `faiss-cpu`  
- `pycountry`

### 4. (Optional) Adjust Kaggle Subset Size

Edit `USE_ROWS` in `src/data_loader.py` to change how many rows load (default: 500 000).

---

## ▶️ Running Locally

```bash  
streamlit run app.py  
```

- The app opens in your browser at `http://localhost:8501` (or another available port).  
- **Sidebar Inputs**:  
    1. **Keyword** (required)  
    2. **Location** (city/state or full country name, required)  
    3. **Industry/Category** (optional)  
    4. **Preferred Company Size** (Any / Small / Medium / Large)  
- Click **Generate Leads**.  
- View the **Top 20** leads sorted by **Score**. Hover “ⓘ” next to **Score** for details.  
- Scroll down to see a **Map** of the top 10 geocoded leads.  
- Use **Download CSV** or **Download JSON** to export results.

---

## ☁️ Deploy via `deployment.ipynb` (Ngrok)

1. **Open** `deployment.ipynb` in a Jupyter environment (e.g., Google Colab).  
2. **Upload** `data/companies-2023-q4-sm.csv` into the notebook’s file system.  
3. **Run all cells** sequentially:  
     - Installs dependencies (from `requirements.txt`)  
     - Starts an ngrok tunnel (generates a public URL)  
     - Launches Streamlit behind the ngrok URL  
4. **Copy** the ngrok public URL and open it in your browser to use the live app remotely.

> When the notebook session ends, the ngrok tunnel and public URL expire automatically.

---

## ✨ Key Advantages

| Feature                  | Benefit                                                                                                      |
|--------------------------|--------------------------------------------------------------------------------------------------------------|
| **Hybrid Data Sources**  | Live HTML scraping + 17 M+ Kaggle entries → both local directories and global coverage.                       |
| **Precise Filtering**    | Keyword, location (city/state/country), optional category, and size preference filters minimize noise.        |
| **Granular Scoring**     | Six weighted components yield a 0–100 score, producing fine-grained ranking and reducing ties.                |
| **Transparent Metrics**  | Tooltip on **Score** clearly explains the weight breakdown.                                                 |
| **Free & Open**          | Only public HTML scraping and a free Kaggle dataset—no paid APIs or subscriptions required.                  |
| **User-Friendly UI**     | Clean Streamlit interface, intuitive sidebar, interactive map, and export buttons.                           |
| **Caching Efficiency**   | Geocoding results cached locally to speed up subsequent runs.                                                |

---

## 🔧 Customization & Extension

- **Change Dataset Size**: Modify `USE_ROWS` in `src/data_loader.py`.  
- **Add More Scrapers**: Extend `src/scraper.py` to include additional directories or sources.  
- **Swap Models**: Replace DistilBERT or SentenceTransformer names in `src/llm.py` or `src/evaluation.py`.  
- **Adjust Styling**: Edit `style.css` (or remove it to use Streamlit’s default theme).  
- **Deploy to Cloud**: Containerize with Docker or host on Streamlit Cloud, Heroku, AWS, etc.

---

## 🤝 Contributing

- **Report Issues**: Open an issue for bug reports or feature requests.  
- **Pull Requests**: Fork the repository, create a feature branch, implement changes, and submit a PR. Please maintain existing code style and modular structure.

---

## 📜 License

- **Code**: MIT License  
- **Dataset**: ODC Attribution License (ODC-By) via Kaggle  
- **Libraries**: Subject to their respective open-source licenses

---

Thank you for using **AI-Powered Lead Scraper**! If you have questions or need assistance, feel free to open an issue on GitHub.
