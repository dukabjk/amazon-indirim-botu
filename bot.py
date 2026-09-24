import os, re, asyncio, requests, urllib.parse
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Proxy üzerinden çekiyoruz ki Amazon engellemesin
def amazonu_proxy_ile_cek(amazon_url):
    # allorigins: amazon linkini başka sunucu üzerinden çeker
    proxy_url = f"https://api.allorigins.win/get?url={urllib.parse.quote(amazon_url)}"
    r = requests.get(proxy_url, timeout=20)
    data = r.json()
    return data.get("contents", "")

def kategoriyi_tara(kategori_adi, amazon_url):
    html = amazonu_proxy_ile_cek(amazon_url)
    print(f"{kategori_adi} -> {len(html)} karakter geldi")

    if len(html) < 2000:
        return []

    # %25 ve üzeri indirimli ürünleri bul
    # Amazon kartlarında %25, %40, %50 diye yazar
    urunler = []
    # Tüm ürün bloklarını ayır
    bloklar = html.split('data-component-type="s-search-result"')[1:]

    for blok in bloklar[:20]:
        indirim_match = re.search(r'%(\d+)', blok)
        if not indirim_match:
            continue
        indirim = int(indirim_match.group(1))
        if indirim < 25:
            continue

        link_match = re.search(r'href="([^"]*?/dp/([A-Z0-9]{10})[^"]*)"', blok)
        isim_match = re.search(r'<h2.*?<span>(.*?)</span>', blok, re.DOTALL)

        if link_match:
            link = link_match.group(1)
            if not link.startswith("http"):
                link = "https://www.amazon.com.tr" + link
            link = link.split("?")[0] + f"?tag=seninortakligin-21" # istersen affiliate ekle

            isim = isim_match.group(1).strip() if isim_match else "Ürün"
            isim = re.sub(r'<.*?>', '', isim)[:90]

            urunler.append({"isim": isim, "indirim": indirim, "link": link})

    return sorted(urunler, key=lambda x: x['indirim'], reverse=True)[:4]

async def main():
    bot = Bot(token=TOKEN)

    KATEGORILER = {
        "💻 Teknoloji": "https://www.amazon.com.tr/s?i=electronics&rh=p_n_pct-off-with-tax%3A-25&s=review-rank",
        "👕 Giyim": "https://www.amazon.com.tr/s?i=fashion&rh=p_n_pct-off-with-tax%3A-25&s=review-rank",
        "🛒 Market": "https://www.amazon.com.tr/s?i=groceries&rh=p_n_pct-off-with-tax%3A-25&s=review-rank"
    }

    mesaj = "🔥 AMAZON TR %25+ İNDİRİMLER\n"
    bulundu_mu = False

    for kat, url in KATEGORILER.items():
        urunler = kategoriyi_tara(kat, url)
        if urunler:
            bulundu_mu = True
            mesaj += f"\n{kat}:\n"
            for u in urunler:
                mesaj += f" %{u['indirim']} {u['isim']}\n {u['link']}\n\n"

    if bulundu_mu:
        # Parçala gönder
        for i in range(0, len(mesaj), 3500):
            await bot.send_message(chat_id=CHAT_ID, text=mesaj[i:i+3500])
    else:
        await bot.send_message(chat_id=CHAT_ID, text="⚠️ Proxy çalıştı ama şu an filtrede ürün yok. Kod Amazon'u gerçekten tarıyor, istersen filtreyi %10'a düşüreyim mi?")

asyncio.run(main())
