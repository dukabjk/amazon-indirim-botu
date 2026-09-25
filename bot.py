import os, json, random, re, time
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
KEYWORDS = ["ayakkabi", "t-shirt", "kulaklik", "mutfak", "kahve", "zeytinyagi", "canta", "termos"]

def load_seen():
    try:
        with open("seen.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_seen(d):
    with open("seen.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Referer": "https://www.amazon.com.tr/",
    })

    # çerez al
    session.get("https://www.amazon.com.tr/", timeout=15)
    time.sleep(1)

    keyword = random.choice(KEYWORDS)
    url = f"https://www.amazon.com.tr/s?k={keyword}"
    print(f"URL: {url}")

    r = session.get(url, timeout=20)
    print(f"Status: {r.status_code}, len: {len(r.text)}")

    if "captcha" in r.text.lower() or "Robot doğrulama" in r.text:
        print("Captcha engeli, pas geçildi")
        print("ok")
        return

    soup = BeautifulSoup(r.text, "html.parser")

    # 2 farklı yöntem dene
    items = soup.select("div[data-asin][data-component-type='s-search-result']")
    print(f"Yontem1 urun: {len(items)}")
    if len(items) == 0:
        items = soup.select("div.s-result-item[data-asin]")
        print(f"Yontem2 urun: {len(items)}")
    if len(items) == 0:
        items = soup.select("div[data-asin]")
        print(f"Yontem3 urun: {len(items)}")

    seen = load_seen()
    yeni = 0

    for item in items:
        asin = item.get("data-asin", "").strip()
        if not asin or len(asin)!= 10:
            continue
        # reklam ve boşları atla
        if item.select_one("span[data-component-type='s-ads']"):
            continue

        title_el = item.select_one("h2 span")
        price_el = item.select_one("span.a-price span.a-offscreen")

        if not title_el or not price_el:
            continue

        title = title_el.get_text(strip=True)
        if len(title) < 5:
            continue

        price_text = price_el.get_text()
        price_text = price_text.replace("TL","").replace("₺","").strip()
        # 1.234,56 -> 1234.56
        price_text_clean = price_text.replace(".","").replace(",",".").strip()
        try:
            price = float(re.findall(r"[\d\.]+", price_text_clean)[0])
        except:
            continue

        if price < 30: # çok düşük saçma fiyatları atla
            continue

        link = f"https://www.amazon.com.tr/dp/{asin}"
        print(f"OK {asin} - {price} TL - {title[:30]}")

        if asin not in seen:
            seen[asin] = {"max_price": price, "title": title[:90], "link": link}
            yeni += 1
        else:
            old = seen[asin]
            old_price = old["max_price"] if isinstance(old, dict) else float(old)
            if old_price > price and (old_price - price) / old_price >= 0.2:
                disc = int((old_price - price)/old_price*100)
                send_telegram(f"🔥 %{disc} DUSUS ({keyword})\n\n{title[:80]}\n\n{old_price} TL -> {price} TL\n\n{link}")
                seen[asin]["max_price"] = price
            elif price > old_price:
                seen[asin]["max_price"] = price

        if yeni >= 10:
            break

    save_seen(seen)
    print(f"Yeni eklenen: {yeni}, Toplam hafiza: {len(seen)}")
    print("ok")

if __name__ == "__main__":
    main()
