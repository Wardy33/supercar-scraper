import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time, random, re

# -------------------------------
# Fetch fully rendered HTML with scrolling
# -------------------------------
def fetch_html(url, container_selector):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        try:
            # Wait for the car listings container
            page.wait_for_selector(container_selector, timeout=15000)
        except:
            print(f"⚠️ Timeout waiting for container {container_selector} at {url}")

        # Scroll to bottom to load lazy content
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
# Scrape AutoTrader
# -------------------------------
def scrape_autotrader(max_pages=3):
    base_url = "https://www.autotrader.co.uk/car-search?postcode=SW1A1AA&include-delivery-option=on&keywords=supercar&page={}"
    container_selector = 'a[data-testid="search-listing-title"]'
    all_results = []

    for page_num in range(1, max_pages+1):
        url = base_url.format(page_num)
        print(f"Scraping AutoTrader page {page_num}: {url}")
        html = fetch_html(url, container_selector)
        soup = BeautifulSoup(html, "html.parser")
        cars = soup.select(container_selector)
        print(f"Found {len(cars)} cars on page {page_num}")

        for car in cars:
            try:
                # Full text: "Bentley Continental6.0 GT 2dr, £13,795"
                make_model = car.get_text(strip=True).split(",")[0]
                # Price: extract from <span> inside <a>
                span = car.select_one("span")
                price_text = span.get_text(strip=True) if span else ""
                price_match = re.search(r"£([\d,]+)", price_text)
                price = price_match.group(1) if price_match else None

                all_results.append({
                    "make_model": make_model,
                    "price": price
                })
            except Exception as e:
                print(f"Error parsing car: {e}")

        time.sleep(random.uniform(2, 4))

    return all_results

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
    data = scrape_autotrader(max_pages=3)  # Test with 3 pages
    print(f"Total cars scraped: {len(data)}")

    normalised = [parse_entry(entry) for entry in data]
    df = pd.DataFrame(normalised)
    df.to_csv("autotrader_supercars.csv", index=False)
    print(f"✅ Saved {len(df)} cars to autotrader_supercars.csv")
