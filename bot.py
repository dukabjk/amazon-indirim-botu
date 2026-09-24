import requests, json, os
from datetime import datetime

KEY = os.getenv("RAINFOREST_KEY")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("CHAT_ID")

words = ["kulaklik","ayakkabi","tshirt","zeytinyagi","kahve","mutfak","telefon kilifi"]
now = datetime.now()
i = ((now.hour * 60 + now.minute) // 15) % len(words)
word = words[i]
print(f"Kelime: {word}")

try:
    with open("seen.json","r") as f:
        seen = json.load(f)
except:
    seen = {}

def get_price(val):
    if isinstance(val, dict):
        return val.get("max", val.get("last", 0))
    return val

params = {"api_key": KEY, "type": "search", "amazon_domain": "amazon.com.tr", "search_term": word}
r = requests.get("https://api.rainforestapi.com/request", params=params).json()

for p in r.get("search_results", [])[:20]:
    asin = p.get("asin")
    price = p.get("price",{}).get("value")
    if not asin or not price:
        continue

    old_raw = seen.get(asin)
    old = get_price(old_raw) if old_raw else None

    if old is None:
        seen[asin] = price
    else:
        if old > 0 and (old - price) / old >= 0.2:
            txt = f"INDIRIM {word} {old} -> {price}\n{p.get('link')}"
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT, "text": txt})
        # her zaman en düşük fiyatı güncelle, en yükseği sakla mantığı için düz sayıya çevir
        seen[asin] = max(old, price) if price > old else min(old, price)
        # düşüş için aslında en yüksek fiyatı tutmamız lazım, sade olsun diye max tutuyoruz
        if price > old:
            seen[asin] = price
        else:
            # indirim varsa en yüksekte kalsın ki bir daha atmasın
            pass
            # seen[asin] = old

with open("seen.json","w") as f:
    json.dump(seen, f)

print("ok")
