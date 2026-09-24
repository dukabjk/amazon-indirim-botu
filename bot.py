pythonimport os, requests, asyncio
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Artık sayı olacak

bot = Bot(token=BOT_TOKEN)

async def main():
    try:
        await bot.send_message(chat_id=CHAT_ID, text="✅ Bot düzeldi! Şimdi her 30 dakikada Amazon'da %25+ indirim arayacağım.\n\nTest başarılı.")
        print("Mesaj gönderildi")
    except Exception as e:
        print(f"HATA: {e}")
        # Hatanın ne olduğunu logda görelim
        raise e

asyncio.run(main())
