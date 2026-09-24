import os, json, requests, asyncio, time
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RF_KEY = os.getenv("RAINFOREST_KEY")
SEEN_FILE = "seen.json"

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)

def rainforest_istek_denemeli():
    url = "https://api.rainforestapi.com/request"
    params = {"api_key": RF_KEY, "type": "deals", "amazon_domain": "amazon.com.tr", "language": "tr_TR"}
    
    # 3 kez dene, timeout'u 60sn yap
    for deneme in range(3):
        try:
            print(f"Deneme {deneme+1}/3...")
            r = requests.get(url, params=params, timeout=60)
            data = r.json()
            urunler = data.get("deals_results", []) or data.get("deal_products", []) or []
            if urunler:
                return urunler
            print(f"Bos geldi, tekrar deniyorum: {data}")
            time.sleep(5)
        except Exception as e:
            print(f"Timeout/Hata {deneme+1}: {e}")
            time.sleep(5)
    return []

async def main():
    bot = Bot(token=BOT_TOKEN)
    seen = load_seen()

    urunler = rainforest_istek_denemeli()
    
    if not urunler:
        await bot.send_message(chat_id=CHAT_ID, text="⚠️ Rainforest şu an yanıt vermedi (timeout). 30dk sonra tekrar deneyecek.")
        return

    print(f"Toplam: {len(urunler)}")
    
    filtreli = []
    for p in urunler:
        asin = p.get("asin","")
        oran = p.get("deal_percent_off") or p.get("savings_percent") or 0
        try: oran = int(float(str(oran).replace("%","")))
        except: oran = 0
        if oran < 20 or not asin:
            continue
        eski_oran = seen.get(asin, -1)
        if eski_oran == oran:
            continue
        filtreli.append({
            "asin": asin,
            "isim": p.get("title","")[:70],
            "oran": oran,
            "link": p.get("link",""),
            "fiyat": p.get("deal_price",{}).get("raw","") or ""
        })

    filtreli = sorted(filtreli, key=lambda x: x["oran"], reverse=True)[:30]

    if not filtreli:
        print("Yeni %20+ yok")
        return

    mesaj_parcalari = []
    baslik = f"🔥 AMAZON TR EN İYİ {len(filtreli)} YENİ FIRSAT %20+\n\n"
    mevcut = baslik
    for u in filtreli:
        satir = f"%{u['oran']} | {u['isim']}\n💰 {u['fiyat']}\n{u['link']}\n\n"
        if len(mevcut) + len(satir) > 3800:
            mesaj_parcalari.append(mevcut)
            mevcut = satir
        else:
            mevcut += satir
    mesaj_parcalari.append(mevcut)

    for parca in mesaj_parcalari:
        await bot.send_message(chat_id=CHAT_ID, text=parca)
        await asyncio.sleep(1)

    for u in filtreli:
        seen[u["asin"]] = u["oran"]
    save_seen(seen)

asyncio.run(main())
