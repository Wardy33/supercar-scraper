import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time, random, re

# -------------------------------
# Supercar makes/models
# -------------------------------
supercars = {
    "Ferrari": ["488", "F8", "812", "Portofino", "SF90"],
    "Lamborghini": ["Aventador", "Huracan", "Urus", "Gallardo"],
    "McLaren": ["720S", "765LT", "GT", "600LT", "P1"],
    "Aston Martin": ["DB11", "Vantage", "DBS", "Valhalla"],
    "Porsche": ["911 Turbo", "911 GT3", "911 GT2 RS", "Cayman GT4"],
    "Bentley": ["Continental GT", "Flying Spur"],
    "Audi": ["R8"],
    "Jaguar": ["F-Type SVR"],
    "Mercedes": ["AMG GT", "SLS"],
    "BMW": ["i8"],
    "Pagani": ["Huayra", "Zonda"],
    "Koenigsegg": ["Jesko", "Regera"],
    "Lotus": ["Evora", "Elise", "Emira"],
    "Maserati": ["MC20"]
}

# -------------------------------
# Fetch fully rendered HTML
# -------------------------------
def fetch_html(url, container_selector):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        try:
            page.wait_for_selector(container_selector, timeout=15000)
        except:
            print(f"⚠️ Timeout waiting for container {container_selector} at {url}")

        # Scroll to bottom to load all lazy-loaded content
        previous_height = 0
        while True:
            height = page.evaluate("document.body.scrollHeight")
            if height == previous_height:
                break
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            previous_height = height
            time.sleep(2)

        html = page.content()
        browser.close()
    return html

# -------------------------------
# Scrape one make/model
# -------------------------------
def scrape_make_model(make, model, max_pages=3, postcode="SW1A1AA", radius=500):
    base_url = ("https://www.autotrader.co.uk/car-search?"
                "postcode={postcode}&radius={radius}&make={make}&model={model}&page={page}")
    container_selector = 'a[data-testid="search-listing-title"]'
    results = []

    for page_num in range(1, max_pages + 1):
        url = base_url.format(postcode=postcode, radius=radius, make=make, model=model, page=page_num)
        print(f"Scraping {make} {model}, page {page_num}: {url}")
        html = fetch_html(url, container_selector)
        soup = BeautifulSoup(html, "html.parser")
        cars = soup.select(container_selector)
        print(f"Found {len(cars)} cars on page {page_num}")

        if not cars:
            break

        for car in cars:
            try:
                make_model_text = car.get_text(strip=True).split(",")[0]
                span = car.select_one("span")
                price_text = span.get_text(strip=True) if span else ""
                price_match = re.search(r"£([\d,]+)", price_text)
                price = price_match.group(1) if price_match else None

                results.append({
                    "make_model": make_model_text,
                    "price": price
                })
            except Exception as e:
                print(f"Error parsing car: {e}")

        time.sleep(random.uniform(2, 4))

    return results

# -------------------------------
# Normalize data
# -------------------------------
def parse_entry(entry):
    text = entry["make_model"]
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    year = year_match.group(0) if year_match else ""
    parts = text.split()
    make = parts[0] if not year else parts[1]
    model = " ".join(parts[1:]) if not year else " ".join(parts[2:])
    price_clean = re.sub(r"[^\d]", "", entry["price"]) if entry["price"] else None
    return {
        "year": year,
        "make": make,
        "model": model,
        "price": int(price_clean) if price_clean and price_clean.isdigit() else None
    }

# -------------------------------
# Main runner
# -------------------------------
if __name__ == "__main__":
    all_data = []

    for make, models in supercars.items():
        for model in models:
            data = scrape_make_model(make, model, max_pages=3)  # adjust pages as needed
            all_data.extend(data)

    print(f"Total cars scraped: {len(all_data)}")

    # Normalize and save CSV as 'supercars.csv'
    normalised = [parse_entry(entry) for entry in all_data]
    df = pd.DataFrame(normalised)
    df.to_csv("supercars.csv", index=False)
    print(f"✅ Saved {len(df)} cars to supercars.csv")
