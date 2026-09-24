import requests, json, os
from datetime import datetime

KEY = os.getenv("RAINFOREST_KEY")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("CHAT_ID")

words = ["kulaklik","ayakkabi","tshirt","zeytinyagi","kahve","mutfak","telefon kilifi"]

# rotasyon
now = datetime.now()
i = ((now.hour * 60 + now.minute) // 15) % len(words)
word = words[i]

print(f"Kelime: {word}")

try:
    with open("seen.json","r") as f:
        seen = json.load(f)
except:
    seen = {}

params = {"api_key": KEY, "type": "search", "amazon_domain": "amazon.com.tr", "search_term": word}
r = requests.get("https://api.rainforestapi.com/request", params=params).json()

for p in r.get("search_results", [])[:20]:
    asin = p.get("asin")
    price = p.get("price",{}).get("value")
    if not asin or not price:
        continue
    if asin not in seen:
        seen[asin] = price
    else:
        old = seen[asin]
        if old > 0 and (old - price) / old >= 0.2:
            txt = f"INDIRIM {word} {old} -> {price}\n{p.get('link')}"
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT, "text": txt})
        if price > old:
            seen[asin] = price
        else:
            if price < old:
                seen[asin] = price

with open("seen.json","w") as f:
    json.dump(seen, f)

print("ok")
