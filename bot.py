import os, re, asyncio
from telegram import Bot
from playwright.async_api import async_playwright

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def gercek_tarama(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(7000)
        html = await page.content()
        await browser.close()
        return html

def parse_et(html):
    urunler = []
    bloklar = html.split('data-component-type="s-search-result"')[1:]
    print(f"Blok sayisi: {len(bloklar)} HTML uzunluk: {len(html)}")
    for blok in bloklar[:30]:
        m_ind = re.search(r'%(\d+)', blok)
        if not m_ind: continue
        indirim = int(m_ind.group(1))
        if indirim < 20: continue
        m_link = re.search(r'href="([^"]*?/dp/([A-Z0-9]{10})[^"]*)"', blok)
        m_isim = re.search(r'<h2.*?<span>(.*?)</span>', blok, re.DOTALL)
        if m_link:
            link = m_link.group(1)
            if not link.startswith("http"):
                link = "https://www.amazon.com.tr" + link
            link = link.split("?")[0]
            isim = re.sub(r'<.*?>', '', m_isim.group(1)).strip()[:80] if m_isim else "Firsat"
            urunler.append({"isim": isim, "indirim": indirim, "link": link})
    return sorted(urunler, key=lambda x: x['indirim'], reverse=True)[:5]

async def main():
    bot = Bot(token=TOKEN)
    url = "https://www.amazon.com.tr/s?i=electronics&rh=p_n_pct-off-with-tax%3A-20&s=review-rank"
    html = await gercek_tarama(url)
    urunler = parse_et(html)

    if urunler:
        mesaj = "🔥 CANLI TARAMA %20+ (Gercek Tarayici)\n\n"
        for u in urunler:
            mesaj += f"%{u['indirim']} {u['isim']}\n{u['link']}\n\n"
        await bot.send_message(chat_id=CHAT_ID, text=mesaj[:3500])
    else:
        # Debug: ilk 500 karakteri at
        await bot.send_message(chat_id=CHAT_ID, text=f"Chrome acildi ama rozet bulunamadi. Blok:{html.count('s-search-result')} HTML:{len(html)}")

asyncio.run(main())
