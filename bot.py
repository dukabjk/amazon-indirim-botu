import os, re, asyncio, requests
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Accept": "text/html,application/xhtml+xml"
}

# DOĞRU YÖNTEM: Amazon'un kendi %25 indirim filtresi
# p_n_pct-off-with-tax:25- = %25 ve üzeri indirim demek
KATEGORILER = {
    "💻 Teknoloji": "https://www.amazon.com.tr/s?i=electronics&rh=p_n_pct-off-with-tax%3A-25&s=review-rank&fs=true",
    "👕 Giyim": "https://www.amazon.com.tr/s?i=fashion&rh=p_n_pct-off-with-tax%3A-25&s=review-rank&fs=true",
    "🛒 Market": "https://www.amazon.com.tr/s?i=groceries&rh=p_n_pct-off-with-tax%3A-25&s=review-rank&fs=true"
}

def tara(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        print(f"URL: {url}")
        print(f"Status: {r.status_code} | Boyut: {len(r.text)} karakter")

        # Amazon engelledi mi kontrol et
        if "api-services-support" in r.text or len(r.text) < 5000:
            print("AMAZON ENGELLEDİ - Captcha sayfası geldi")
            return None, "engellendi"

        html = r.text
        # Ürün kartlarını bul
        items = re.findall(r'data-component-type="s-search-result".*?href="/([^"]+/dp/[^"]+)".*?<span class="a-size-base-plus[^>]*>([^<]+)</span>.*?%(\d+)', html, re.DOTALL)

        if not items:
            # Alternatif pattern
            items = re.findall(r'/dp/([A-Z0-9]{10}).*?class="a-badge-text">%(\d+)', html)

        bulunanlar = []
        for item in items[:10]:
            if len(item) == 3:
                link_part, isim, indirim = item
                link = f"https://www.amazon.com.tr/{link_part.split('?')[0]}"
                if int(indirim) >= 25:
                    bulunanlar.append(f"%{indirim} - {isim[:70]}\n{link}")
            elif len(item) == 2:
                asin, indirim = item
                if int(indirim) >= 25:
                    bulunanlar.append(f"%{indirim} - https://www.amazon.com.tr/dp/{asin}")

        return bulunanlar, f"{len(html)} karakter geldi"

    except Exception as e:
        print(f"Hata: {e}")
        return [], str(e)

async def main():
    bot = Bot(token=TOKEN)
    log_mesaji = "🔍 Tarama Raporu:\n"
    tum_firsatlar = ""

    for isim, url in KATEGORILER.items():
        urunler, durum = tara(url)
        log_mesaji += f"\n{isim}: {durum}\n"

        if urunler is None:
            tum_firsatlar += f"\n{isim}: Amazon şu an botu engelliyor, 1 saat sonra tekrar deneyecek.\n"
            continue

        if urunler:
            tum_firsatlar += f"\n{isim} (%25+):\n" + "\n\n".join(urunler[:3]) + "\n"
            log_mesaji += f"-> {len(urunler)} ürün bulundu\n"
        else:
            log_mesaji += f"-> Ürün bulunamadı (filtre çalışıyor ama stok yok)\n"

    print(log_mesaji)
    # Telegram'a ne yaptığını at
    if tum_firsatlar:
        await bot.send_message(chat_id=CHAT_ID, text=tum_firsatlar[:3500])
    else:
        await bot.send_message(chat_id=CHAT_ID, text=log_mesaji + "\n\nAmazon şu an boş sayfa döndü. Eğer sürekli böyle olursa Keepa API'ye geçeceğiz, o %100 çalışır.")

asyncio.run(main())
