import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time, random, re

# -------------------------------
# Fetch fully rendered HTML with scrolling
# -------------------------------
def fetch_html(url, container_selector, wait_time=5000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        try:
            # Wait for main container
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
# Scraper function
# -------------------------------
def scrape_site(base_url, container_selector, title_selector, price_selector, mileage_selector, source_name, max_pages=5):
    page_num = 1
    results = []
    while page_num <= max_pages:
        url = base_url.format(page_num)
        print(f"Scraping {source_name} page {page_num}: {url}")
        html = fetch_html(url, container_selector)
        soup = BeautifulSoup(html, "html.parser")
        cars = soup.select(container_selector)
        print(f"Found {len(cars)} cars on page {page_num} of {source_name}")

        if not cars:
            break

        for car in cars:
            try:
                title = car.select_one(title_selector)
                price = car.select_one(price_selector)
                mileage = car.select_one(mileage_selector)
                if title and price:
                    results.append({
                        "source": source_name,
                        "make_model": title.get_text(strip=True),
                        "price": price.get_text(strip=True),
                        "mileage": mileage.get_text(strip=True) if mileage else ""
                    })
            except Exception as e:
                print(f"Error parsing car: {e}")
        page_num += 1
        time.sleep(random.uniform(2, 5))
    return results

# -------------------------------
# Individual site scrapers
# -------------------------------
def scrape_autotrader():
    return scrape_site(
        "https://www.autotrader.co.uk/car-search?postcode=SW1A1AA&include-delivery-option=on&keywords=supercar&page={}",
        ".product-card",
        ".product-card-details__title",
        ".product-card-pricing__price",
        ".product-card-details__mileage",
        "AutoTrader",
        max_pages=10
    )

# Add other sites similarly, updating container_selector, title_selector, etc.

# -------------------------------
# Normalize data
# -------------------------------
def parse_entry(entry):
    text = entry["make_model"]
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    year = year_match.group(0) if year_match else ""
    price_clean = re.sub(r"[^\d]", "", entry["price"])
    mileage_clean = re.sub(r"[^\d]", "", entry["mileage"]) if entry["mileage"] else ""
    parts = text.split()
    make = parts[1] if year else parts[0]
    model = " ".join(parts[2:]) if year else " ".join(parts[1:])
    return {
        "source": entry["source"],
        "year": year,
        "make": make,
        "model": model,
        "price": int(price_clean) if price_clean.isdigit() else None,
        "mileage": int(mileage_clean) if mileage_clean.isdigit() else None
    }

# -------------------------------
# Main runner
# -------------------------------
if __name__ == "__main__":
    scrapers = [
        scrape_autotrader,
        # add other site functions here like scrape_amari, scrape_romans, etc.
    ]

    all_data = []
    for scraper in scrapers:
        try:
            print(f"Starting scraper: {scraper.__name__}")
            data = scraper()
            all_data.extend(data)
        except Exception as e:
            print(f"Error scraping {scraper.__name__}: {e}")

    print(f"Total cars scraped: {len(all_data)}")

    # Normalize and save CSV
    normalised = [parse_entry(entry) for entry in all_data]
    df = pd.DataFrame(normalised)
    df.to_csv("supercars.csv", index=False)
    print(f"✅ Scraped {len(df)} cars. Saved to supercars.csv")
