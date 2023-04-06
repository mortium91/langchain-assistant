import httpx
import os
import telegram
from fastapi import APIRouter, Request
from chat_handler import process_chat_message

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
client = httpx.AsyncClient()
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

telegram_webhook = APIRouter()

@telegram_webhook.post("/webhook/")
async def handle_telegram_webhook(req: Request):
    data = await req.json()
    chat_id = data['message']['chat']['id']
    text = data['message'].get('text', '')

    output = await process_chat_message(text)

    if isinstance(output, tuple):
        summary, image = output
        await bot.send_photo(chat_id, image)
        await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={summary}")
    else:
        await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={output}")

    return {"message": output}
