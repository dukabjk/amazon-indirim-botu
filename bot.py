import os, re, asyncio, requests, urllib.parse
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

def amazon_cek(amazon_url):
    html = ""
    try:
        url = f"https://api.allorigins.win/raw?url={urllib.parse.quote(amazon_url)}"
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code == 200 and len(r.text) > 5000:
            html = r.text
    except:
        pass
    if len(html) < 5000:
        try:
            url2 = f"https://corsproxy.io/?{urllib.parse.quote(amazon_url)}"
            r2 = requests.get(url2, headers=HEADERS, timeout=25)
            if r2.status_code == 200 and len(r2.text) > 5000:
                html = r2.text
        except:
            pass
    if len(html) < 5000:
        try:
            r3 = requests.get(amazon_url, headers=HEADERS, timeout=15)
            html = r3.text
        except:
            pass
    return html

def parse_et(html):
    urunler = []
    if len(html) < 2000:
        return urunler
    bloklar = html.split('data-component-type="s-search-result"')[1:]
    for blok in bloklar[:30]: # 30 ürüne bak
        m_indirim = re.search(r'%(\d+)', blok)
        if not m_indirim:
            continue
        indirim = int(m_indirim.group(1))
        if indirim < 20: # <--- BURASI %20 OLDU
            continue
        m_link = re.search(r'href="([^"]*?/dp/([A-Z0-9]{10})[^"]*)"', blok)
        m_isim = re.search(r'<h2.*?<span>(.*?)</span>', blok, re.DOTALL)
        if m_link:
            link = m_link.group(1)
            if not link.startswith("http"):
                link = "https://www.amazon.com.tr" + link
            link = link.split("?")[0]
            isim = m_isim.group(1).strip() if m_isim else "Fırsat Ürünü"
            isim = re.sub(r'<.*?>', '', isim)[:90]
            urunler.append({"isim": isim, "indirim": indirim, "link": link})
    return sorted(urunler, key=lambda x: x['indirim'], reverse=True)[:5]

async def main():
    bot = Bot(token=TOKEN)
    # BURASI %20 OLDU
    KATS = {
        "💻 Teknoloji": "https://www.amazon.com.tr/s?i=electronics&rh=p_n_pct-off-with-tax%3A-20&s=review-rank",
        "👕 Giyim": "https://www.amazon.com.tr/s?i=fashion&rh=p_n_pct-off-with-tax%3A-20&s=review-rank",
        "🛒 Market": "https://www.amazon.com.tr/s?i=groceries&rh=p_n_pct-off-with-tax%3A-20&s=review-rank",
    }
    mesaj = "🔥 AMAZON TR %20+ İNDİRİMLER (Canlı Tarama)\n"
    var_mi = False
    for kat, url in KATS.items():
        html = amazon_cek(url)
        urunler = parse_et(html)
        print(f"{kat} -> {len(urunler)} ürün bulundu")
        if urunler:
            var_mi = True
            mesaj += f"\n{kat}:\n"
            for u in urunler:
                mesaj += f"%{u['indirim']} {u['isim']}\n{u['link']}\n\n"

    if var_mi:
        for i in range(0, len(mesaj), 3500):
            await bot.send_message(chat_id=CHAT_ID, text=mesaj[i:i+3500])
    else:
        await bot.send_message(chat_id=CHAT_ID, text="Bot Amazon'a bağlandı ama %20+ da bile şu an ürün yok. Bir sonraki taramada tekrar bakacak.")

asyncio.run(main())
