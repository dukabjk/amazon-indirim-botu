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
    with open(SEEN_FILE,"w") as f: json.dump(d,f, indent=2)

def arama(kelime):
    url = "https://api.rainforestapi.com/request"
    params = {
        "api_key": RF_KEY,
        "type": "search",
        "amazon_domain": "amazon.com.tr",
        "search_term": kelime,
        "language": "tr_TR"
    }
    try:
        r = requests.get(url, params=params, timeout=50)
        return r.json().get("search_results", [])
    except Exception as e:
        print(f"{kelime} hata {e}")
        return []

async def main():
    bot = Bot(token=BOT_TOKEN)
    seen = load_seen() # {asin: {"max_price": 1000, "title": "", "link": ""}}

    kelimeler = ["kulaklik", "telefon kilifi", "ayakkabi", "tshirt", "zeytinyagi", "kahve", "mutfak"]
    yeni_firsatlar = []

    for k in kelimeler:
        urunler = arama(k)
        print(f"{k}: {len(urunler)}")
        for p in urunler[:20]:
            asin = p.get("asin")
            if not asin: continue
            fiyat = p.get("price",{}).get("value",0)
            if not fiyat: continue

            title = p.get("title","")[:70]
            link = p.get("link","")

            if asin not in seen:
                # ilk kez görüyoruz, kaydet
                seen[asin] = {"max_price": fiyat, "title": title, "link": link}
            else:
                max_fiyat = seen[asin].get("max_price", fiyat)
                # fiyat daha da yükseldiyse max'ı güncelle
                if fiyat > max_fiyat:
                    seen[asin]["max_price"] = fiyat
                else:
                    # düşüş var mı?
                    dusus = int((max_fiyat - fiyat) / max_fiyat * 100)
                    if dusus >= 20:
                        # daha önce bu düşüşü attık mı?
                        if seen[asin].get("last_sent_drop")!= dusus:
                            yeni_firsatlar.append({
                                "asin": asin,
                                "isim": title,
                                "oran": dusus,
                                "eski": max_fiyat,
                                "yeni": fiyat,
                                "link": link
                            })
                            seen[asin]["last_sent_drop"] = dusus
        time.sleep(2)

    yeni_firsatlar = sorted(yeni_firsatlar, key=lambda x: x["oran"], reverse=True)[:30]

    if yeni_firsatlar:
        msg = f"🔥 FİYAT DÜŞÜŞÜ %20+ {len(yeni_firsatlar)} ÜRÜN\n\n"
        for u in yeni_firsatlar:
            msg += f"%{u['oran']} {u['isim']}\n{u['eski']}TL -> {u['yeni']}TL\n{u['link']}\n\n"
            if len(msg) > 3500:
                await bot.send_message(chat_id=CHAT_ID, text=msg)
                msg = ""
                await asyncio.sleep(1)
        if msg:
            await bot.send_message(chat_id=CHAT_ID, text=msg)
    else:
        print("Yeni %20 düşüş yok, sadece fiyatlar kaydedildi")
        # İlk kurulumda bilgi ver
        if len(seen) < 30:
            await bot.send_message(chat_id=CHAT_ID, text=f"Bot öğreniyor... {len(seen)} ürün kaydedildi. Fiyatlar düşmeye başlayınca %20+ olarak atacağım.")

    save_seen(seen)

asyncio.run(main())
