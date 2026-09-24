import os
import asyncio
from telegram import BotTOKEN = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")print(f"TOKEN var mi: {bool(TOKEN)}")
print(f"CHAT_ID: {CHAT}")bot = Bot(token=TOKEN)async def main():
    await bot.send_message(chat_id=CHAT, text="✅ Sonunda oldu! Bot bağlandı.")asyncio.run(main())
