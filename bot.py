import os, json, requests, urllib.parse

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("RAINFOREST_KEY")

KEYWORDS = ["ayakkabi", "t-shirt", "kulaklik", "mutfak", "kahve", "zeytinyagi"]

def get_price():
    try:
        with open("seen.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_price(data):
    with open("seen.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False})

def main():
    seen = get_price()
    # Eski sayı formatını düzelt
    for k, v in list(seen.items()):
        if isinstance(v, (int, float)):
            seen[k] = {"max_price": float(v), "title": k, "link": f"https://www.amazon.com.tr/dp/{k}"}

    keyword = KEYWORDS[0] # Actions her seferinde 1 kelime için tetikleniyor, cron ile dönüyor
    # kelime seçimi main.yml'den gelmiyor ise random
    import random, datetime
    keyword = random.choice(KEYWORDS)

    params = {
        "api_key": API_KEY,
        "type": "search",
        "amazon_domain": "amazon.com.tr",
        "search_term": keyword,
        "sort_by": "price_low_to_high"
    }

    r = requests.get("https://api.rainforestapi.com/request", params=params, timeout=30)
    data = r.json()
    products = data.get("search_results", [])[:10]

    for p in products:
        asin = p.get("asin")
        price = p.get("price", {}).get("value")
        title = p.get("title", "")[:80]
        link = p.get("link", "")

        if not asin or not price:
            continue

        old_data = seen.get(asin)
        old_max = old_data["max_price"] if old_data else 0

        if old_max == 0:
            seen[asin] = {"max_price": price, "title": title, "link": link}
        else:
            if old_max > 0 and (old_max - price) / old_max >= 0.2:
                discount = int((old_max - price) / old_max * 100)
                msg = f"🔥 %{discount} İNDİRİM!\n\n{title}\n\n💰 {old_max} TL -> {price} TL\n\n🔗 {link}"
                send_telegram(msg)
                seen[asin]["max_price"] = price # yeni düşük fiyatı kaydet
            else:
                # fiyat arttıysa max'ı güncelle
                if price > old_max:
                    seen[asin]["max_price"] = price

    save_price(seen)
    print(f"Kelime: {keyword}")
    print("ok")

if __name__ == "__main__":
    main()
