from fastapi import FastAPI
from telegram_handler import telegram_webhook
from twilio_handler import twilio_api_reply
from uvicorn.config import Config

# Create a FastAPI app instance
app = FastAPI()

# Include the routers for the Telegram webhook and Twilio API reply
app.include_router(telegram_webhook)
app.include_router(twilio_api_reply)
