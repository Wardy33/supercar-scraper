import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time, random, re

# -------------------------------
# HTML fetcher with Playwright
# -------------------------------
def fetch_html(url, wait=5000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(wait)
        html = page.content()
        browser.close()
    return html

# -------------------------------
# Scraper Functions (with pagination)
# -------------------------------
def scrape_site(base_url, page_param, container_selector, title_selector, price_selector, mileage_selector, source_name, max_pages=10):
    page_num = 1
    results = []
    while True:
        url = base_url.format(page_num)
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        cars = soup.select(container_selector)
        if not cars or page_num > max_pages:  # stop if no cars or exceeds max_pages
            break
        for car in cars:
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
        page_num += 1
        time.sleep(random.uniform(2, 5))
    return results

# -------------------------------
# Individual Site Scrapers
# -------------------------------
def scrape_amari():
    return scrape_site(
        "https://www.amarisupercars.com/stock/?pg={}",
        "pg",
        ".vehicle-card",
        ".vehicle-card__title",
        ".vehicle-card__price",
        ".vehicle-card__mileage",
        "Amari"
    )

def scrape_romans():
    return scrape_site(
        "https://www.romansinternational.com/used-cars/page/{}/",
        "page",
        ".stocklist-vehicle",
        ".vehicle-title",
        ".vehicle-price",
        ".vehicle-mileage",
        "Romans"
    )

def scrape_hr_owen():
    return scrape_site(
        "https://www.hrowen.co.uk/used-cars/page/{}/",
        "page",
        ".vehicle",
        ".vehicle-title",
        ".vehicle-price",
        ".vehicle-mileage",
        "H.R. Owen"
    )

def scrape_redline():
    return scrape_site(
        "https://www.redlinespecialistcars.co.uk/used-cars?page={}",
        "page",
        ".vehicle-listing",
        ".vehicle-title",
        ".vehicle-price",
        ".vehicle-mileage",
        "Redline"
    )

def scrape_gve():
    return scrape_site(
        "https://gvelondon.com/used-cars/page/{}/",
        "page",
        ".car-box",
        ".car-title",
        ".car-price",
        ".car-mileage",
        "GVE London"
    )

def scrape_tom_hartley():
    return scrape_site(
        "https://www.tomhartley.com/used/page/{}/",
        "page",
        ".vehicle-card",
        ".vehicle-card__title",
        ".vehicle-card__price",
        ".vehicle-card__mileage",
        "Tom Hartley Jr"
    )

def scrape_clive_sutton():
    return scrape_site(
        "https://www.clivesutton.co.uk/stocklist/page/{}/",
        "page",
        ".stocklist-item",
        ".stocklist-item__title",
        ".stocklist-item__price",
        ".stocklist-item__mileage",
        "Clive Sutton"
    )

def scrape_joe_macari():
    return scrape_site(
        "https://www.joemacari.com/used-cars/page/{}/",
        "page",
        ".car-card",
        ".car-card__title",
        ".car-card__price",
        ".car-card__mileage",
        "Joe Macari"
    )

def scrape_pistonheads():
    return scrape_site(
        "https://www.pistonheads.com/buy/search?category=supercars&page={}",
        "page",
        ".phui-picture-card",
        ".phui-picture-card__title",
        ".phui-picture-card__price",
        ".phui-picture-card__mileage",
        "PistonHeads",
        max_pages=20
    )

def scrape_autotrader():
    return scrape_site(
        "https://www.autotrader.co.uk/car-search?postcode=SW1A1AA&include-delivery-option=on&keywords=supercar&page={}",
        "page",
        ".product-card-details",
        ".product-card-details__title",
        ".product-card-pricing__price",
        ".product-card-details__mileage",
        "AutoTrader",
        max_pages=20
    )

# -------------------------------
# Normalise Data
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
# Main Runner
# -------------------------------
if __name__ == "__main__":
    scrapers = [
        scrape_amari, scrape_romans, scrape_hr_owen, scrape_redline, scrape_gve,
        scrape_tom_hartley, scrape_clive_sutton, scrape_joe_macari,
        scrape_pistonheads, scrape_autotrader
    ]

    all_data = []
    for scraper in scrapers:
        try:
            print(f"Scraping {scraper.__name__} ...")
            data = scraper()
            all_data.extend(data)
            time.sleep(random.uniform(2,5))
        except Exception as e:
            print(f"❌ Error scraping {scraper.__name__}: {e}")

    # Normalise and save
    normalised = [parse_entry(entry) for entry in all_data]
    df = pd.DataFrame(normalised)
    df.to_csv("supercars.csv", index=False)
    print(f"✅ Scraped {len(df)} cars. Saved to supercars.csv")
