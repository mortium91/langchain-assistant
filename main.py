from fastapi import FastAPI
from telegram_handler import telegram_webhook
from twilio_handler import twilio_api_reply

app = FastAPI()

app.include_router(telegram_webhook)
app.include_router(twilio_api_reply)