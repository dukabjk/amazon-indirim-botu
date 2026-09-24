import os, requests, asyncio
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RF_KEY = os.getenv("RAINFOREST_KEY")

def rainforest_ara(kelime):
    url = "https://api.rainforestapi.com/request"
    params = {
        "api_key": RF_KEY,
        "type": "search",
        "amazon_domain": "amazon.com.tr",
        "search_term": kelime,
        "sort_by": "price_high_to_low",
        "language": "tr_TR"
    }
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    return data.get("search_results", [])

def indirim_hesapla(p):
    # Rainforest bazen eski fiyat veriyor
    try:
        fiyat = p.get("price", {}).get("value", 0)
        eski = p.get("prices", [{}])[0].get("value", 0) if p.get("prices") else 0
        # Alternatif alanlar
        if not eski:
            eski = p.get("price_strikethrough", {}).get("value", 0)
        if fiyat and eski and eski > fiyat:
            oran = int((eski - fiyat) / eski * 100)
            return oran, fiyat, eski
    except:
        pass
    return 0, 0, 0

async def main():
    bot = Bot(token=BOT_TOKEN)
    aramalar = ["kulaklik", "telefon", "laptop"]
    tum_urunler = []

    for kelime in aramalar:
        try:
            sonuclar = rainforest_ara(kelime)
            print(f"{kelime} -> {len(sonuclar)} sonuç")
            for p in sonuclar[:20]:
                oran, fiyat, eski = indirim_hesapla(p)
                if oran >= 20: # %20 filtre
                    tum_urunler.append({
                        "isim": p.get("title","")[:80],
                        "oran": oran,
                        "link": p.get("link",""),
                        "fiyat": fiyat
                    })
        except Exception as e:
            print(f"Hata {kelime}: {e}")

    # En yüksek indirimden sırala
    tum_urunler = sorted(tum_urunler, key=lambda x: x["oran"], reverse=True)[:7]

    if tum_urunler:
        mesaj = "🔥 AMAZON TR %20+ CANLI (Rainforest API)\n\n"
        for u in tum_urunler:
            mesaj += f"%{u['oran']} {u['isim']}\n{u['link']}\n\n"
        await bot.send_message(chat_id=CHAT_ID, text=mesaj[:3800])
    else:
        await bot.send_message(chat_id=CHAT_ID, text="Rainforest bağlandı ama %20+ hesaplanamadı. API ham veriyi gönderiyorum debug için.")
        # Debug ilk ürün
        try:
            ornek = rainforest_ara("kulaklik")[0]
            await bot.send_message(chat_id=CHAT_ID, text=str(ornek)[:3500])
        except:
            pass

asyncio.run(main())
