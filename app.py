import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from datetime import datetime

from src.scraper import search_yellowpages, search_yelp, search_manta
from src.data_loader import load_company_data
from src.evaluation import score_leads, score_company_row
from src.utils import load_cache, save_cache

# 1) Streamlit page configuration (must be first)
st.set_page_config(page_title="AI-Powered Lead Scraper", layout="wide")

# # 2) Load custom CSS (optional; comment out to use default styling)
# with open("style.css") as f:
#     st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3) App title
st.title("AI-Powered Lead Scraper")

# 4) Sidebar inputs
st.sidebar.header("Lead Search")
keyword = st.sidebar.text_input("Keyword (e.g., Bakery)", "").strip()
location = st.sidebar.text_input("Location (e.g., Austin, TX or United States)", "").strip()
category_input = st.sidebar.text_input("Industry/Category (optional)", "").strip()

size_option = st.sidebar.radio(
    "Preferred Company Size:",
    options=["Any", "Small (1–50)", "Medium (51–500)", "Large (501+)"]
)

if st.sidebar.button("Generate Leads"):
    # Validate required inputs
    if not keyword or not location:
        st.sidebar.error("Please enter both Keyword and Location.")
        st.stop()

    # Normalize for filtering
    kw_lower = keyword.lower()
    loc_lower = location.lower()
    cat_lower = category_input.lower()

    # Map size_option to numeric range
    preferred_range = None
    if size_option == "Small (1–50)":
        preferred_range = (1, 50)
    elif size_option == "Medium (51–500)":
        preferred_range = (51, 500)
    elif size_option == "Large (501+)":
        preferred_range = (501, float("inf"))

    with st.spinner("Searching and scoring leads..."):
        # --- Live Scraping from three sources (limit 10 each) ---
        yp_leads = search_yellowpages(keyword, location, max_results=10)
        yelp_leads = search_yelp(keyword, location, max_results=10)
        manta_leads = search_manta(keyword, location, max_results=10)
        scraped_all = yp_leads + yelp_leads + manta_leads

        # If user specified a category, filter scraped leads by it
        if cat_lower:
            scraped_all = [
                lead for lead in scraped_all
                if cat_lower in lead.get("industry", "").lower()
            ]

        # --- Kaggle Dataset Filtering (behind the scenes) ---
        df_all = load_company_data()
        df_scan = df_all.head(500_000)  # scan first 500k rows for performance
        # Keyword match: company name or industry
        mask_kw = (
            df_scan["name"].str.lower().str.contains(kw_lower, na=False)
            | df_scan["industry"].str.lower().str.contains(kw_lower, na=False)
        )
        # Location match: city, state, or full country name
        mask_loc = (
            df_scan["city"].str.lower().str.contains(loc_lower, na=False)
            | df_scan["state"].str.lower().str.contains(loc_lower, na=False)
            | df_scan["country_name"].str.lower().str.contains(loc_lower, na=False)
        )

        if cat_lower:
            mask_cat = df_scan["industry"].str.lower().str.contains(cat_lower, na=False)
            df_filtered = df_scan[mask_kw & mask_loc & mask_cat]
        else:
            df_filtered = df_scan[mask_kw & mask_loc]

        # Build Kaggle leads (limit to first 500 matches)
        kaggle_leads = []
        for _, row in df_filtered.head(500).iterrows():
            size_str = row.get("size", "")
            try:
                if "-" in size_str:
                    parts = size_str.split("-")
                    mid = (int(parts[0]) + int(parts[1])) // 2
                elif size_str.endswith("+"):
                    mid = int(size_str.replace("+", ""))
                else:
                    mid = int(size_str)
            except:
                mid = 0

            # Filter by preferred_range if specified
            if preferred_range:
                low, high = preferred_range
                if mid < low or mid > high:
                    continue

            country_full = row.get("country_name", "")
            loc_str = ", ".join(filter(None, [row["city"], row["state"], country_full]))
            kaggle_leads.append({
                "name": row["name"],
                "industry": row["industry"],
                "location": loc_str,
                "phone": None,
                "rating": None,
                "snippet": None,
                "year_founded": int(row["founded"]) if pd.notnull(row["founded"]) else None,
                "size": mid,
                "score": 0
            })

        # Combine scraped + Kaggle leads
        all_leads = scraped_all + kaggle_leads
        if not all_leads:
            st.error("No leads found for the given inputs.")
            st.stop()

        # Score all leads (0–100 scale)
        scored_leads = score_leads(all_leads, preferred_range)
        top20 = scored_leads[:20]
        df_top = pd.DataFrame(top20)

    # --- Display top 20 leads in a DataFrame ---
    st.subheader("Top 20 Leads")
    display_cols = ["name", "industry", "location", "phone", "year_founded", "size", "rating", "score"]
    df_display = df_top[display_cols].rename(columns={
        "name": "Name",
        "industry": "Industry",
        "location": "Location",
        "phone": "Phone",
        "year_founded": "Founded",
        "size": "Size",
        "rating": "Rating",
        "score": "Score"
    })

    # Add a tooltip next to the header (explains how the Score is calculated)
    st.markdown(
        "<div style='display: flex; align-items: center;'>"
        "<h4>Leads sorted by descending Score</h4>"
        "<span title='Score (0–100) = Age (20%) + Size (20%) + Industry Fit (15%) + Sentiment (10%) + Rating (15%) + Semantic Match (20%)' "
        "style='margin-left:10px; cursor: help;'>ⓘ</span>"
        "</div>",
        unsafe_allow_html=True
    )

    st.dataframe(df_display, use_container_width=True)

    # --- Map visualization of the first 10 leads ---
    geolocator = Nominatim(user_agent="lead_scraper")
    geo_cache = load_cache("geo_cache.json")
    coords = []
    for lead in top20[:10]:
        loc_string = lead.get("location") or ""
        if not loc_string.strip():
            coords.append((None, None))
            continue
        if loc_string in geo_cache:
            coords.append(tuple(geo_cache[loc_string]))
        else:
            try:
                geo = geolocator.geocode(loc_string)
                coord = (geo.latitude, geo.longitude) if geo else (None, None)
            except:
                coord = (None, None)
            geo_cache[loc_string] = coord
            coords.append(coord)
    save_cache("geo_cache.json", geo_cache)

    df_map = pd.DataFrame({
        "latitude": [c[0] for c in coords],
        "longitude": [c[1] for c in coords]
    })
    df_map = df_map.dropna()
    if not df_map.empty:
        st.subheader("Map of Top 10 Leads")
        st.map(df_map)

    # --- Export Buttons (side by side) ---
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        csv_data = df_top.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv_data, file_name="top20_leads.csv", mime="text/csv")
    with c2:
        json_data = df_top.to_json(orient="records", force_ascii=False)
        st.download_button("Download JSON", data=json_data, file_name="top20_leads.json", mime="application/json")

    st.success(f"Displayed {len(df_top)} leads. Export them using the buttons above.")
