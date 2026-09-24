import os
import asyncio
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

async def main():
    await bot.send_message(chat_id=CHAT, text="✅ Oldu! Sonunda çalıştı.")

asyncio.run(main())
