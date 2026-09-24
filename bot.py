pythonimport requests
import re
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot

# ===== SADECE BURAYI DOLDUR =====
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "dukabjk"
# =================================

bot = Bot(token=BOT_TOKEN)

def fiyat_cevir(txt):
    try:
        t = txt.replace("TL","").replace("₺","").strip().replace(".","").replace(",",".")
        m = re.findall(r"\d+\.?\d*", t)
        return float(m[0]) if m else None
    except:
        return None

async def tara():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    url = "https://www.amazon.com.tr/gp/goldbox"

    print("Amazon taraniyor...")
    try:
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        sayac = 0

        for item in soup.select('div[data-component-type="s-search-result"]'):
            if sayac >= 10: break
            try:
                baslik_el = item.select_one('h2')
                if not baslik_el: continue
                baslik = baslik_el.get_text(strip=True)

                yeni_el = item.select_one('.a-price.a-offscreen')
                eski_el = item.select_one('.a-price.a-text-price.a-offscreen')
                link_el = baslik_el.find_parent('a')

                if not yeni_el or not eski_el: continue

                yeni = fiyat_cevir(yeni_el.get_text())
                eski = fiyat_cevir(eski_el.get_text())

                if yeni and eski and eski > yeni:
                    indirim = int((1 - yeni/eski) * 100)
                    if indirim >= 25:
                        link = "https://www.amazon.com.tr" + link_el.get('href') if link_el else url
                        mesaj = f"🔥 %{indirim} INDIRIM\n\n{baslik}\n\n💰 {int(eski)} TL -> {int(yeni)} TL\n\n🔗 {link}\n\n#teknoloji #giyim #market"
                        await bot.send_message(chat_id=CHAT_ID, text=mesaj)
                        print(f"Gonderildi: %{indirim} {baslik[:40]}")
                        sayac += 1
            except Exception as e:
                continue
    except Exception as e:
        print(f"Hata: {e}")
        await bot.send_message(chat_id=CHAT_ID, text=f"Bot hata aldi: {e}")

async def main():
    await tara()

asyncio.run(main())
