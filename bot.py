import os, json, requests, asyncio, time
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RF_KEY = os.getenv("RAINFOREST_KEY")
SEEN_FILE = "seen.json"

def load_seen():
    try:
        with open(SEEN_FILE,"r") as f: return json.load(f)
    except: return {}
def save_seen(d):
    with open(SEEN_FILE,"w") as f: json.dump(d,f)

def deals_kategori(cat_id):
    url = "https://api.rainforestapi.com/request"
    params = {
        "api_key": RF_KEY,
        "type": "deals",
        "amazon_domain": "amazon.com.tr",
        "category_id": cat_id,
        "language": "tr_TR"
    }
    for deneme in range(2):
        try:
            print(f"{cat_id} çekiliyor deneme {deneme+1}")
            r = requests.get(url, params=params, timeout=90)
            data = r.json()
            urunler = data.get("deals_results", []) or data.get("deal_products", []) or []
            print(f"{cat_id} -> {len(urunler)} ürün")
            return urunler
        except Exception as e:
            print(f"{cat_id} hata: {e}")
            time.sleep(3)
    return []

async def main():
    bot = Bot(token=BOT_TOKEN)
    seen = load_seen()

    kategoriler = {
        "electronics": "Elektronik",
        "apparel": "Giyim",
        "grocery": "Gida",
        "home": "Ev Yasam",
        "toys": "Oyuncak"
    }

    tum_urunler = []
    for cat_id, isim in kategoriler.items():
        urunler = deals_kategori(cat_id)
        for p in urunler:
            oran = p.get("deal_percent_off") or p.get("savings_percent") or p.get("percent_off") or 0
            try: oran = int(float(str(oran).replace("%","")))
            except: oran = 0
            if oran < 20: continue
            
            asin = p.get("asin","")
            if not asin: continue
            if seen.get(asin) == oran: continue

            tum_urunler.append({
                "asin": asin,
                "kat": isim,
                "isim": p.get("title","")[:65],
                "oran": oran,
                "link": p.get("link",""),
                "fiyat": p.get("deal_price",{}).get("raw","") or p.get("price",{}).get("raw","")
            })
        time.sleep(2)

    tum_urunler = sorted(tum_urunler, key=lambda x: x["oran"], reverse=True)[:30]

    if not tum_urunler:
        # Debug: en azından kaç ürün çektiğimizi at
        await bot.send_message(chat_id=CHAT_ID, text="Bugün hiç yeni %20+ yok. Hafızayı sıfırlamak için seen.json dosyasını sil.")
        return

    # 30 ürünü 10'arlı 3 mesaja böl
    header = f"🔥 TÜM KATEGORİLER EN İYİ {len(tum_urunler)} FIRSAT %20+\n\n"
    cur = header
    parcalar = []
    for u in tum_urunler:
        satir = f"[{u['kat']}] %{u['oran']} {u['isim']} {u['fiyat']}\n{u['link']}\n\n"
        if len(cur)+len(satir) > 3800:
            parcalar.append(cur)
            cur = satir
        else:
            cur += satir
    parcalar.append(cur)

    for pc in parcalar:
        await bot.send_message(chat_id=CHAT_ID, text=pc)
        await asyncio.sleep(1)

    for u in tum_urunler:
        seen[u["asin"]] = u["oran"]
    save_seen(seen)

asyncio.run(main())
