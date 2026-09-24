import os, re, asyncio, requests
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

# 3 kategori, her biri Amazon'un fırsat sayfası
KATEGORILER = {
    "💻 Teknoloji": "https://www.amazon.com.tr/gp/goldbox?gb_f_deals1_sortOrder=BEST_DEAL&pf_rd_p=0f52a9b3-8c2b-4761-b8a9-cf9a8d45597d&pf_rd_s=slot-3&rh=i%3Aelectronics&ie=UTF8&ref_=sv_elec_6",
    "👕 Giyim": "https://www.amazon.com.tr/gp/goldbox?gb_f_deals1_sortOrder=BEST_DEAL&rh=i%3Aapparel&ie=UTF8&ref_=sv_app_6",
    "🛒 Market": "https://www.amazon.com.tr/gp/goldbox?gb_f_deals1_sortOrder=BEST_DEAL&rh=i%3Agrocery&ie=UTF8"
}

def firsatlari_al(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        html = r.text

        urunler = []
        # Amazon indirim rozetleri: %25, %30 gibi
        # Desen: %25, %32, %40 İndirim veya savingPercentage
        pattern = r'data-testid="product-card".*?%(\d+).*?</div>'

        # Daha basit ve sağlam yöntem: tüm kartları regex ile tara
        bloklar = re.findall(r'<div class="a-section a-spacing-medium.*?">(.*?)</div>\s*</div>\s*</div>\s*</div>', html, re.DOTALL)[:40]
        if not bloklar:
            bloklar = html.split('a-spacing-medium')[1:40]

        for blok in bloklar:
            indirim_match = re.search(r'%(\d+)', blok)
            if not indirim_match:
                continue
            indirim = int(indirim_match.group(1))
            if indirim < 25:
                continue

            # Link ve isim al
            link_match = re.search(r'href="(/dp/[A-Z0-9]+|/.*?/dp/[A-Z0-9]+)"', blok)
            isim_match = re.search(r'title="(.*?)"|class="a-size-base[^"]*">([^<]{10,100})<', blok)

            if link_match:
                link = "https://www.amazon.com.tr" + link_match.group(1).split('?')[0]
                # ASIN temizle
                asin_match = re.search(r'/dp/([A-Z0-9]+)', link)
                asin = asin_match.group(1) if asin_match else "link"

                isim = "Amazon Fırsat Ürünü"
                if isim_match:
                    isim = (isim_match.group(1) or isim_match.group(2) or isim).strip()[:80]

                urunler.append({"isim": isim, "indirim": indirim, "link": link})

        # İndirime göre sırala, en yüksekten
        urunler = sorted(urunler, key=lambda x: x['indirim'], reverse=True)
        return urunler[:5] # Kategori başı en iyi 5

    except Exception as e:
        print(f"Hata {url}: {e}")
        return []

async def main():
    bot = Bot(token=TOKEN)
    toplam_mesaj = ""

    for kat_isim, kat_url in KATEGORILER.items():
        print(f"Taranıyor: {kat_isim}")
        urunler = firsatlari_al(kat_url)
        if not urunler:
            continue

        toplam_mesaj += f"\n{kat_isim} - %25+ İndirimler:\n"
        for u in urunler:
            toplam_mesaj += f"🔥 %{u['indirim']} - {u['isim']}\n{u['link']}\n\n"

    if toplam_mesaj:
        # Telegram 4096 karakter limiti için parçala
        for i in range(0, len(toplam_mesaj), 3500):
            await bot.send_message(chat_id=CHAT_ID, text=toplam_mesaj[i:i+3500])
        print("Mesajlar gönderildi")
    else:
        print("Bu sefer %25+ fırsat bulunamadı")
        await bot.send_message(chat_id=CHAT_ID, text="🤖 Kontrol ettim, şu an %25+ fırsat yok. 30 dk sonra tekrar bakacağım.")

asyncio.run(main())
