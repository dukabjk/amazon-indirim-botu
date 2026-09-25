import os, json, random, re, time
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
KEYWORDS = ["ayakkabi", "t-shirt", "kulaklik", "mutfak", "kahve", "zeytinyagi"]

def load_seen():
    try:
        with open("seen.json", "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_seen(d):
    with open("seen.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

# Daha gerçekçi tarayıcı taklidi
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.amazon.com.tr/",
})

# İlk önce amazon ana sayfasına git çerez al
session.get("https://www.amazon.com.tr/", timeout=15)
time.sleep(2)

keyword = random.choice(KEYWORDS)
url = f"https://www.amazon.com.tr/s?k={keyword}&s=price-asc-rank"
print(f"Gidilen URL: {url}")

r = session.get(url, timeout=20)
print(f"Status: {r.status_code}, Sayfa uzunluğu: {len(r.text)}")

# Debug: sayfa amazon mu captcha mı?
if "captcha" in r.text.lower() or "Robot kontrolü" in r.text:
    print("AMAZON CAPTCHA ENGELİ!")
    # Bu durumda seen.json'a dokunma
    save_seen(load_seen())
    print("ok")
    return

soup = BeautifulSoup(r.text, "lxml")
items = soup.select("div[data-component-type='s-search-result']")
print(f"Bulunan ürün div sayısı: {len(items)}")

seen = load_seen()
count = 0
for item in items[:10]:
    asin = item.get("data-asin")
    title_tag = item.select_one("h2 a span")
    price_tag = item.select_one("span.a-price span.a-offscreen")

    if not asin or not title_tag or not price_tag:
        continue

    title = title_tag.get_text(strip=True)[:90]
    price_text = price_tag.get_text()
    price_text = price_text.replace("TL","").replace(".","").replace(",",".").strip()
    try:
        price = float(re.findall(r"[\d\.]+", price_text)[0])
    except:
        continue

    link = f"https://www.amazon.com.tr/dp/{asin}"
    print(f" -> {asin} | {price} TL | {title[:30]}")

    if asin not in seen:
        seen[asin] = {"max_price": price, "title": title, "link": link}
        count += 1
    else:
        old_max = seen[asin].get("max_price", price)
        if isinstance(old_max, dict): old_max = old_max.get("max_price", price)
        if old_max > price and (old_max - price) / old_max >= 0.2:
            disc = int((old_max - price)/old_max*100)
            send_telegram(f"🔥 %{disc} DÜŞÜŞ! {keyword}\n\n{title}\n{old_max} TL -> {price} TL\n{link}")

        if price > old_max:
            seen[asin]["max_price"] = price

save_seen(seen)
print(f"Kaydedilen yeni ürün: {count}, Toplam: {len(seen)}")
print("ok")
