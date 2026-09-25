import os, json, time, random, re
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KEYWORDS = ["ayakkabi", "t-shirt", "kulaklik", "mutfak", "kahve", "zeytinyagi"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

def load_seen():
    try:
        with open("seen.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # eski sayı formatını düzelt
            for k,v in list(data.items()):
                if isinstance(v, (int,float)):
                    data[k] = {"max_price": float(v), "title": k, "link": f"https://www.amazon.com.tr/dp/{k}"}
            return data
    except:
        return {}

def save_seen(d):
    with open("seen.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def parse_price(text):
    # "1.479,00 TL" -> 1479.0
    if not text: return None
    text = text.replace(".", "").replace(",", ".")
    m = re.search(r"(\d+[\.\d]*\d*)", text)
    if m:
        try: return float(m.group(1))
        except: return None
    return None

def scrape_keyword(keyword, seen):
    url = f"https://www.amazon.com.tr/s?k={keyword}"
    print(f"Araniyor: {keyword} - {url}")
    r = requests.get(url, headers=HEADERS, timeout=20)

    if r.status_code!= 200:
        print(f"Amazon engelledi: {r.status_code}")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div[data-asin]")

    count = 0
    for item in items:
        asin = item.get("data-asin")
        if not asin or len(asin)!= 10: continue

        title_el = item.select_one("h2 span")
        price_el = item.select_one("span.a-price-whole, span.a-offscreen")
        link_el = item.select_one("a.a-link-normal")

        if not title_el or not price_el: continue

        title = title_el.get_text(strip=True)[:80]
        price = parse_price(price_el.get_text())
        link = "https://www.amazon.com.tr" + link_el.get("href").split("?")[0] if link_el else f"https://www.amazon.com.tr/dp/{asin}"

        if not price or price < 50: continue # saçma fiyatları atla

        old = seen.get(asin)
        old_max = old["max_price"] if old else 0

        if old_max == 0:
            seen[asin] = {"max_price": price, "title": title, "link": link}
        else:
            if old_max > 0 and (old_max - price) / old_max >= 0.2:
                disc = int((old_max - price) / old_max * 100)
                msg = f"🔥 %{disc} İNDİRİM! ({keyword})\n\n{title}\n\n💰 {old_max} TL -> {price} TL\n\n🔗 {link}"
                send_telegram(msg)
                seen[asin]["max_price"] = price
            elif price > old_max:
                seen[asin]["max_price"] = price

        count += 1
        if count >= 10: break # her kelimede 10 ürün yeter

    print(f"{keyword} -> {count} ürün işlendi")

def main():
    seen = load_seen()
    keyword = random.choice(KEYWORDS)
    scrape_keyword(keyword, seen)
    save_seen(seen)
    print("ok")

if __name__ == "__main__":
    main()
