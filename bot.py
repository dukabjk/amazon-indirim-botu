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
    params = {"api_key": RF_KEY,"type": "search","amazon_domain": "amazon.com.tr","search_term": kelime,"language": "tr_TR"}
    try:
        r = requests.get(url, params=params, timeout=50)
        return r.json().get("search_results", [])
    except: return []

async def main():
    bot = Bot(token=BOT_TOKEN)
    seen = load_seen()
    kelimeler = ["kulaklik","ayakkabi","tshirt","zeytinyagi","kahve","mutfak","telefon kilifi"]
    yeni = []

    for k in kelimeler:
        for p in arama(k)[:20]:
            asin = p.get("asin")
            fiyat = p.get("price",{}).get("value",0)
            if not asin or not fiyat: continue
            title = p.get("title","")[:70]
            link = p.get("link","")
            if asin not in seen:
                seen[asin] = {"max_price": fiyat, "title": title, "link": link}
            else:
                max_f = seen[asin].get("max_price", fiyat)
                if fiyat > max_f:
                    seen[asin]["max_price"] = fiyat
                else:
                    dusus = int((max_f - fiyat) / max_f * 100)
                    if dusus >= 20 and seen[asin].get("last_sent")!= dusus:
                        yeni.append({"isim": title, "oran": dusus, "eski": max_f, "yeni": fiyat, "link": link})
                        seen[asin]["last_sent"] = dusus
        time.sleep(1)

    if yeni:
        yeni = sorted(yeni, key=lambda x: x["oran"], reverse=True)[:20]
        txt = f"🔥 %{20}+ DUSUS {len(yeni)} URUN\n\n"
        for u in yeni:
            txt += f"%{u['oran']} {u['isim']}\n{u['eski']}TL -> {u['yeni']}TL\n{u['link']}\n\n"
        await bot.send_message(chat_id=CHAT_ID, text=txt[:4000])
    else:
        if len(seen) < 50:
            await bot.send_message(chat_id=CHAT_ID, text=f"Bot ogreniyor... {len(seen)} urun kaydedildi. 2. calismadan sonra dususleri atacagim.")
        print(f"Kayitli {len(seen)}, yeni {len(yeni)}")

    save_seen(seen)

asyncio.run(main())
