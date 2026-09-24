import os, json, requests, asyncio, time
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RF_KEY = os.getenv("RAINFOREST_KEY")
SEEN_FILE = "seen.json"

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f: return json.load(f)
    except: return {}
def save_seen(d):
    with open(SEEN_FILE, "w") as f: json.dump(d, f)

def arama_yap(kelime):
    url = "https://api.rainforestapi.com/request"
    params = {
        "api_key": RF_KEY,
        "type": "search",
        "amazon_domain": "amazon.com.tr",
        "search_term": kelime,
        "language": "tr_TR",
        "sort_by": "deal_rank", # fırsatları öne getir
        "page": "1"
    }
    try:
        r = requests.get(url, params=params, timeout=40)
        return r.json().get("search_results", [])
    except Exception as e:
        print(f"{kelime} hata: {e}")
        return []

async def main():
    bot = Bot(token=BOT_TOKEN)
    seen = load_seen()

    # GENEL TARAMA İÇİN ANAHTAR KELİMELER
    kelimeler = ["elektronik", "giyim", "gıda", "kulaklik", "ayakkabi", "mutfak"]
    tum_urunler = []

    for k in kelimeler:
        urunler = arama_yap(k)
        print(f"{k} -> {len(urunler)}")
        for p in urunler[:15]:
            # Rainforest search'te indirim alanı
            oran = 0
            # Bazen list_price vs price farkı
            try:
                fiyat = p.get("price",{}).get("value",0)
                # Eski fiyat için farklı alanlar dene
                eski = 0
                if p.get("prices"):
                    # ilk fiyat current, ikinci eski olabilir
                    if len(p["prices"]) > 1:
                        eski = p["prices"][1].get("value",0)
                if not eski:
                    eski = p.get("price_strikethrough",{}).get("value",0) or p.get("list_price",{}).get("value",0)

                if p.get("is_deal") or p.get("deal_percent_off"):
                    oran = p.get("deal_percent_off") or p.get("savings_percent") or 0

                if fiyat and eski and eski > fiyat:
                    oran = int((eski - fiyat) / eski * 100)
            except: pass

            if oran >= 20:
                asin = p.get("asin","")
                if not asin: continue
                if seen.get(asin) == oran: continue

                tum_urunler.append({
                    "asin": asin,
                    "isim": p.get("title","")[:65],
                    "oran": oran,
                    "link": p.get("link",""),
                    "fiyat": p.get("price",{}).get("raw","")
                })
        time.sleep(2) # API'yi yormamak için

    # En iyi 30
    tum_urunler = sorted(tum_urunler, key=lambda x: x["oran"], reverse=True)[:30]

    if not tum_urunler:
        await bot.send_message(chat_id=CHAT_ID, text="Bugün %20+ yeni fırsat yok (hafızadakiler hariç).")
        return

    mesaj = f"🔥 GENEL %20+ {len(tum_urunler)} YENİ FIRSAT\n\n"
    parcalar = []
    cur = mesaj
    for u in tum_urunler:
        satir = f"%{u['oran']} {u['isim']} {u['fiyat']}\n{u['link']}\n\n"
        if len(cur)+len(satir) > 3800:
            parcalar.append(cur)
            cur = satir
        else:
            cur += satir
    parcalar.append(cur)

    for p in parcalar:
        await bot.send_message(chat_id=CHAT_ID, text=p)
        await asyncio.sleep(1)

    for u in tum_urunler:
        seen[u["asin"]] = u["oran"]
    save_seen(seen)

asyncio.run(main())
