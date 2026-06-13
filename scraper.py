# src/scraper.py

import requests
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Common User-Agent headers to act like a normal compliant browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def fetch_appointment_availability(country: str, city: str, url: str) -> list:
    """
    Fetches the visa appointment availability page and extracts open slots.
    Complies with strict rules: only monitors publicly accessible HTML.
    """
    logger.info(f"Scraping availability from: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching appointment page {url}: {e}")
        return []

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. First, check if it's our Mock Visa Center Page (it has specific classes/IDs)
        mock_table = soup.find('table', id='slots-table')
        if mock_table or "VFS Global - Italy Visa Center Algeria" in soup.title.string if soup.title else False:
            return parse_mock_page(soup, city)
            
        # 2. Otherwise, fall back to a Generic Page Parser
        # Look for table rows, list items, or paragraphs that contain dates and availability words
        return parse_generic_page(soup, city, country)
        
    except Exception as e:
        logger.error(f"Error parsing page content: {e}", exc_info=True)
        return []

def parse_mock_page(soup: BeautifulSoup, target_city: str) -> list:
    """
    Parses the mock visa center's structured HTML format.
    """
    slots = []
    rows = soup.find_all('tr', class_='slot-row')
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 5:
            date_str = cols[0].text.strip()
            city = cols[1].text.strip()
            country = cols[2].text.strip()
            visa_type = cols[3].text.strip().lower()
            status = cols[4].text.strip().lower()
            
            # Check if this match matches the city we are looking for
            if city.lower() == target_city.lower() and "available" in status:
                slots.append({
                    "date": date_str,
                    "city": city,
                    "country": country,
                    "type": visa_type
                })
                
    return slots

def parse_generic_page(soup: BeautifulSoup, target_city: str, target_country: str) -> list:
    """
    A fallback generic parser that searches table columns or paragraphs on any HTML page
    for standard date strings (YYYY-MM-DD or DD/MM/YYYY) and the keyword "available" or "open".
    """
    slots = []
    
    # Common date regex formats
    date_pattern = re.compile(r'\b(202\d[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]202\d)\b')
    
    # Look at all tables first
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            text = row.text.lower()
            # If the row mentions the city and indicates availability
            if target_city.lower() in text and any(kw in text for kw in ["available", "open", "free", "vacant", "yes", "active"]):
                # Extract date from the row
                dates = date_pattern.findall(row.text)
                for date_str in dates:
                    slots.append({
                        "date": date_str,
                        "city": target_city,
                        "country": target_country,
                        "type": "generic"
                    })
                    
    # If no slots found in tables, scan paragraph text as a fallback
    if not slots:
        for p in soup.find_all(['p', 'div', 'li']):
            text = p.text.lower()
            if target_city.lower() in text and any(kw in text for kw in ["available", "open", "slot", "appointment"]):
                dates = date_pattern.findall(p.text)
                for date_str in dates:
                    slots.append({
                        "date": date_str,
                        "city": target_city,
                        "country": target_country,
                        "type": "generic"
                    })
                    
    # Remove duplicates
    unique_slots = []
    seen = set()
    for s in slots:
        key = (s["date"], s["city"].lower())
        if key not in seen:
            seen.add(key)
            unique_slots.append(s)
            
    return unique_slots
