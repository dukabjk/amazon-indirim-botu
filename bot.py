import os, re, asyncio, requests, urllib.parse
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

def amazon_cek(url):
    for proxy in [
        f"https://api.allorigins.win/raw?url={urllib.parse.quote(url)}",
        f"https://corsproxy.io/?{urllib.parse.quote(url)}",
        url
    ]:
        try:
            r = requests.get(proxy, headers=HEADERS, timeout=25)
            if len(r.text) > 5000:
                print(f"OK {len(r.text)} {proxy[:40]}")
                return r.text
        except Exception as e:
            print(f"Fail {e}")
    return ""

async def main():
    bot = Bot(token=TOKEN)
    # Filtresiz + %20 filtreli ikisini deniyoruz
    test_urls = {
        "💻 Teknoloji Düz": "https://www.amazon.com.tr/s?i=electronics&s=price-desc-rank",
        "💻 Teknoloji %20": "https://www.amazon.com.tr/s?k=kulaklik&i=electronics&rh=p_n_pct-off-with-tax%3A-20",
    }

    full_msg = "🔍 DEBUG RAPORU\n"

    for isim, url in test_urls.items():
        html = amazon_cek(url)
        blok_sayisi = html.count('data-component-type="s-search-result"')
        full_msg += f"\n{isim}: {len(html)} karakter, {blok_sayisi} ürün bloğu\n"

        # İsimleri ve rozetleri ne görüyor?
        isimler = re.findall(r'<h2.*?<span>(.*?)</span>', html, re.DOTALL)[:3]
        rozetler = re.findall(r'a-badge-text[^>]*>([^<]*%[^<]*)<', html)[:5]

        full_msg += f"Örnek isim: {isimler[0][:60] if isimler else 'BULAMADI'}\n"
        full_msg += f"Rozetler: {rozetler if rozetler else 'ROZET YOK'}\n"

        # Rozet yoksa bile ilk 3 ürünü link olarak at
        if blok_sayisi > 0:
            links = re.findall(r'href="([^"]*?/dp/[A-Z0-9]{10}[^"]*)"', html)[:3]
            for l in links:
                clean = "https://www.amazon.com.tr" + l.split("?")[0] if not l.startswith("http") else l.split("?")[0]
                full_msg += f"{clean}\n"

    print(full_msg)
    await bot.send_message(chat_id=CHAT_ID, text=full_msg[:3800])

asyncio.run(main())
