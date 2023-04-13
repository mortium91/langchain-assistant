import os
from fastapi import APIRouter, Request
import httpx
import telegram
from chat_handler import process_chat_message
from voice_handler import process_voice_message

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
    voice = data['message'].get('voice', None)
    print(text)
    
    if voice:
        # Process voice messages
        voice_file_id = voice['file_id']
        voice_file_info = await bot.get_file(voice_file_id)
        voice_url = voice_file_info.file_path

        output = await process_voice_message(voice_url, chat_id)
    else:
        # Process text messages
        output = await process_chat_message(text,chat_id)

    # Send the output as a text message or a photo with a caption, depending on the type of output
    if isinstance(output, tuple):
        summary, image = output
        await bot.send_photo(chat_id, image)
        await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={summary}")
    else:
        await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={output}")

    return {"message": output}
