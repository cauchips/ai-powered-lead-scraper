import requests
import random
import time
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]
name_cache = []

def random_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

def attempt_request(url, params=None):
    try:
        return requests.get(url, params=params, headers=random_headers(), timeout=5)
    except:
        return None

def fuzzy_unique(name):
    """
    Avoid near-duplicate names using fuzzy match (>90% similarity).
    """
    for existing in name_cache:
        if fuzz.token_sort_ratio(name.lower(), existing.lower()) > 90:
            return False
    name_cache.append(name)
    return True

def search_yellowpages(keyword, location, max_results=10):
    """
    Scrape YellowPages for keyword+location.
    Returns list of dicts with keys:
      name, industry, location, phone, rating=None, snippet=None,
      website_url=None, year_founded=None, size=None, score=0
    """
    name_cache.clear()
    base_url = "https://www.yellowpages.com/search"
    params = {"search_terms": keyword, "geo_location_terms": location}
    r = attempt_request(base_url, params)
    leads = []

    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        results = soup.select(".result")[:max_results]
        for entry in results:
            name_tag = entry.select_one(".business-name span")
            phone_tag = entry.select_one(".phones.phone")
            category_tag = entry.select_one(".categories")
            street = entry.select_one(".street-address")
            locality = entry.select_one(".locality")

            name = name_tag.get_text(strip=True) if name_tag else None
            if not name or not fuzzy_unique(name):
                continue
            phone = phone_tag.get_text(strip=True) if phone_tag else None
            loc = (
                f"{street.get_text(strip=True)}, {locality.get_text(strip=True)}"
                if (street or locality) else None
            )

            leads.append({
                "name": name,
                "industry": category_tag.get_text(strip=True) if category_tag else "",
                "location": loc,
                "phone": phone,
                "rating": None,
                "snippet": None,
                "website_url": None,
                "year_founded": None,
                "size": None,
                "score": 0
            })
            time.sleep(0.3)

    return leads

def search_yelp(keyword, location, max_results=10):
    """
    Scrape Yelp for keyword+location. Returns a similar dict structure, but with 'rating' and 'snippet' if available.
    """
    name_cache.clear()
    base_url = (
        f"https://www.yelp.com/search?find_desc="
        f"{keyword.replace(' ', '%20')}&find_loc={location.replace(' ', '%20')}"
    )
    r = attempt_request(base_url)
    leads = []

    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.select(".container__09f24__21w3G")[:max_results]
        for entry in listings:
            name_tag = entry.select_one("a.link__09f24__1kwXV")
            rating_tag = entry.select_one("div.i-stars__09f24__1T6rz")
            snippet_tag = entry.select_one("p.comment__09f24__gu0rG")
            phone_tag = entry.select_one("p.text__09f24__2NHRu")

            name = name_tag.get_text(strip=True) if name_tag else None
            if not name or not fuzzy_unique(name):
                continue
            rating = None
            if rating_tag and "aria-label" in rating_tag.attrs:
                try:
                    rating = float(rating_tag["aria-label"].split()[0])
                except:
                    rating = None
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else None
            phone = phone_tag.get_text(strip=True) if phone_tag else None

            leads.append({
                "name": name,
                "industry": keyword,  # Yelp doesn't label industry in HTML scrape
                "location": location,
                "phone": phone,
                "rating": rating,
                "snippet": snippet,
                "website_url": None,
                "year_founded": None,
                "size": None,
                "score": 0
            })
            time.sleep(0.3)

    return leads

def search_manta(keyword, location, max_results=10):
    """
    Scrape Manta for keyword+location. Returns same structure as YellowPages.
    """
    name_cache.clear()
    base_url = (
        "https://www.manta.com/search?"
        f"search_source=nav&search_category=businesses&search_term={keyword.replace(' ', '%20')}"
        f"&search_location={location.replace(' ', '%20')}"
    )
    r = attempt_request(base_url)
    leads = []

    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.select("div.search-result-card")[:max_results]
        for entry in listings:
            name_tag = entry.select_one("a.search-result-title")
            category_tag = entry.select_one("div.category")
            location_tag = entry.select_one("div.location")
            phone_tag = entry.select_one("div.phone")
            website_tag = entry.select_one("a.website-link")

            name = name_tag.get_text(strip=True) if name_tag else None
            if not name or not fuzzy_unique(name):
                continue
            cat = category_tag.get_text(strip=True) if category_tag else ""
            loc = location_tag.get_text(strip=True) if location_tag else location
            phone = phone_tag.get_text(strip=True) if phone_tag else None
            website = website_tag["href"] if website_tag else None

            leads.append({
                "name": name,
                "industry": cat,
                "location": loc,
                "phone": phone,
                "rating": None,
                "snippet": None,
                "website_url": website,
                "year_founded": None,
                "size": None,
                "score": 0
            })
            time.sleep(0.3)

    return leads
