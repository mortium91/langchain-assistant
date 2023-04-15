import asyncio
from fastapi import APIRouter, Form, Response, Request
from twilio.twiml.messaging_response import MessagingResponse
from chat_handler import process_chat_message
from voice_handler import process_voice_message
from config import ACCOUNT_SID, AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER

twilio_api_reply = APIRouter()

async def send_twilio_response(chat_id: str, message: str, is_voice: bool = False):
    """
    Process an incoming chat or voice message and send a response using Twilio.

    Args:
        chat_id (str): Unique identifier for the chat.
        message (str): Input message, either text or a URL of a voice message.
        is_voice (bool): Whether the input message is a voice message (True) or a text message (False). Default is False.
    """

    if not TWILIO_WHATSAPP_NUMBER:
      print("Twilio WhatsApp number not configured. Please set the TWILIO_WHATSAPP_NUMBER environment variable.")
      return

    # Replace 'your_twilio_whatsapp_number' with the variable from config.py
    twilio_phone_number = f'whatsapp:{TWILIO_WHATSAPP_NUMBER}'

    print(f"Twilio phone number: {twilio_phone_number}")
    print(f"Chat ID: {chat_id}")


    if is_voice:
        # Process voice messages
        output = await process_voice_message(message, chat_id)
    else:
        # Process text messages
        output = await process_chat_message(message, chat_id)

    # Initialize Twilio response
    resp = MessagingResponse()

    # Send the output as a text message or a photo with a caption, depending on the type of output
    if isinstance(output, tuple):
        summary, image = output
        response_msg = resp.message(summary)
        response_msg.media(image)
    else:
        response_msg = resp.message(output)

    # Send the message using Twilio client
    from twilio.rest import Client
    account_sid = ACCOUNT_SID
    auth_token = AUTH_TOKEN
    client = Client(account_sid, auth_token)

    if is_voice:
        if isinstance(output, tuple):
            summary, image = output
            client.messages.create(
                body=summary,
                media_url=image,
                from_=twilio_phone_number,
                to=chat_id
            )
        else:
            client.messages.create(
                body=output,
                from_=twilio_phone_number,
                to=chat_id
            )
    else:
        if isinstance(output, tuple):
            summary, image = output
            client.messages.create(
                body=summary,
                media_url=image,
                from_=twilio_phone_number,
                to=chat_id
            )
        else:
            client.messages.create(
                body=output,
                from_=twilio_phone_number,
                to=chat_id
            )

@twilio_api_reply.post("/api")
async def handle_twilio_api_reply(request: Request, Body: str = Form(""), MediaUrl0: str = Form("")):
    form_data = await request.form()
    chat_id = form_data.get("From")

    # Ensure the 'whatsapp:' prefix is present in the chat_id
    if not chat_id.startswith('whatsapp:'):
        chat_id = f'whatsapp:{chat_id}'
    
    # Only process Twilio messages if the Twilio WhatsApp number is configured
    if TWILIO_WHATSAPP_NUMBER:
        if MediaUrl0:
            asyncio.create_task(send_twilio_response(chat_id, MediaUrl0, is_voice=True))
        else:
            asyncio.create_task(send_twilio_response(chat_id, Body))

    # Return an empty response to Twilio
    resp = MessagingResponse()
    return Response(content=str(resp), media_type="application/xml")
