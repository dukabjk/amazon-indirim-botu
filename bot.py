import requests, json, os, time
from datetime import datetime

RAINFOREST_KEY = os.getenv("RAINFOREST_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

kelimeler = ["kulaklik","ayakkabi","tshirt","zeytinyagi","kahve","mutfak","telefon kilifi"]

now = datetime.now()
idx = ((now.hour * 60 + now.minute) // 15) % len(kelimeler)
secilen_kelime = kelimeler[idx]
print(f"-> Taranan kelime: {secilen_kelime}")

try:
    with open("seen.json","r", encoding="utf-8") as f:
        seen = json.load(f)
except:
    seen = {}

if len(seen) > 800:
    seen = dict(list(seen.items())[-600:])
    print(f"Budandi: {len(seen)}")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

params = {
  "api_key": RAINFOREST_KEY,
  "type": "search",
  "amazon_domain": "amazon.com.tr",
  "search_term": secilen_kelime,
  "page": "1"
}

try:
    r = requests.get("https://api.rainforestapi.com/request", params=params, timeout=30)
    data = r.json()
    products = data.get("search_results", [])

    for p in products[:20]:
        asin = p.get("asin")
        if not asin: continue
        title = p.get("title","")[:60]
        price = p.get("price",{}).get("value")
        link = p.get("link","")
        if not price: continue

        if asin not in seen:
            seen[asin] = {"max": price, "last": price}
        else:
            old_max = seen[asin].get("max", price)
            old_last = seen[asin].get("last", price)
            if price > old_max:
                seen[asin]["max"] = price
            if old_max > 0:
                dusus = (old_max - price) / old_max * 100
                if dusus >= 20 and price < old_last:
                    msg = f"🔥 %{dusus:.0f} DÜŞTÜ - {secilen_kelime}\n{title}\n{old_max}TL -> {price}TL\n{link}"
                    send_telegram(msg)
                    time.sleep(1)
            seen[asin]["last"] = price

    with open("seen.json","w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)

    print(f"Bitti. Toplam: {len(seen)}")
except Exception as e:
    print(f"Hata: {e}")
