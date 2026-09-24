import os
import asyncio
import requests
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Takip etmek istediğin ürünler - İstediğin gibi ekle/sil
# Linkteki /dp/ kısmından sonraki kodu al
URUNLER = [
    {"asin": "B0CHX1W1XY", "isim": "AirPods Pro 2. Nesil", "hedef_fiyat": 8000},
    {"asin": "B0BDHWDR12", "isim": "Apple Watch SE 2", "hedef_fiyat": 9000},
    {"asin": "B0C8JBQNBV", "isim": "Samsung 1TB SSD", "hedef_fiyat": 3000},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9"
}

def fiyat_al(asin):
    try:
        url = f"https://www.amazon.com.tr/dp/{asin}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        # Fiyatı sayfadan bul
        text = r.text
        # Amazon TR fiyat formatı
        import re
        match = re.search(r'"priceToPay".*?"amount":(\d+)', text)
        if match:
            return int(match.group(1))
        # Alternatif
        match2 = re.search(r'(\d+[.,]\d+)\s*TL', text)
        if match2:
            return float(match2.group(1).replace('.','').replace(',','.'))
    except Exception as e:
        print(f"{asin} hata: {e}")
    return None

async def main():
    bot = Bot(token=TOKEN)
    mesajlar = []
    for urun in URUNLER:
        fiyat = fiyat_al(urun["asin"])
        print(f"{urun['isim']}: {fiyat}")
        if fiyat and fiyat <= urun["hedef_fiyat"]:
            link = f"https://www.amazon.com.tr/dp/{urun['asin']}"
            msg = f"🔥 İNDİRİM!\n{urun['isim']}\n💰 {fiyat} TL (Hedef: {urun['hedef_fiyat']} TL)\n🔗 {link}"
            mesajlar.append(msg)

    if mesajlar:
        for m in mesajlar:
            await bot.send_message(chat_id=CHAT_ID, text=m)
    else:
        print("İndirim yok")
        # Test için istersen bunu aç, her çalıştığında mesaj atsın
        # await bot.send_message(chat_id=CHAT_ID, text="Bot kontrol etti, şu an hedef fiyatın altında ürün yok.")

asyncio.run(main())
