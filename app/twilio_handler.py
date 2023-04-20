import asyncio
from fastapi import APIRouter, Form, Response, Request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from chat_handler import process_chat_message
from voice_handler import process_voice_message
from config import BABYAGI, ACCOUNT_SID, AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, FACEBOOK_PAGE_ID
from babyagi import process_objective_with_babyagi

twilio_api_reply = APIRouter()

async def send_twilio_response(chat_id: str, message: str, platform: str = "whatsapp", is_voice: bool = False):
    """
    Process an incoming chat or voice message and send a response using Twilio.
    Args:
        chat_id (str): Unique identifier for the chat.
        message (str): Input message, either text or a URL of a voice message.
        platform (str): Messaging platform, either "whatsapp" or "messenger". Default is "whatsapp".
        is_voice (bool): Whether the input message is a voice message (True) or a text message (False). Default is False.
    """

    if platform not in ("whatsapp", "messenger"):
        raise ValueError("Invalid platform specified. Valid platforms are 'whatsapp' and 'messenger'.")

    if platform == "whatsapp" and not TWILIO_WHATSAPP_NUMBER:
        print("Twilio WhatsApp number not configured. Please set the TWILIO_WHATSAPP_NUMBER environment variable.")
        return
    elif platform == "messenger" and not FACEBOOK_PAGE_ID:
        print("Facebook Page ID not configured. Please set the FACEBOOK_PAGE_ID environment variable.")
        return

    if platform == "messenger":
        twilio_phone_number = f'messenger:{FACEBOOK_PAGE_ID}'
    else:
        twilio_phone_number = f'whatsapp:{TWILIO_WHATSAPP_NUMBER}'
    print(message)
    # Rest of the function remains unchanged
    if is_voice:
        # Process voice messages
        output = await process_voice_message(message, chat_id)
    elif BABYAGI and message.startswith("/task"):
        # Process text messages with Babyagi
        task = message[5:]
        await process_objective_with_babyagi(task, chat_id=chat_id, platform='twilio', client=None, base_url=None)
        output = task
    else:
        # Process normal text messages
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
    account_sid = ACCOUNT_SID
    auth_token = AUTH_TOKEN
    client = Client(account_sid, auth_token)

    if is_voice:
        # Send voice messages
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
        # Send text messages
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
    platform = form_data.get("To")

    if platform.startswith("whatsapp"):
        platform = "whatsapp"
    elif platform.startswith("messenger"):
        platform = "messenger"
    else:
        return Response(content="Invalid platform", media_type="text/plain", status_code=400)

    # Only process Twilio messages if the Twilio WhatsApp number or Facebook Page ID is configured
    if (platform == "whatsapp" and TWILIO_WHATSAPP_NUMBER) or (platform == "messenger" and FACEBOOK_PAGE_ID):
        if MediaUrl0:
            asyncio.create_task(send_twilio_response(chat_id, MediaUrl0, platform=platform, is_voice=True))
        else:
            asyncio.create_task(send_twilio_response(chat_id, Body.strip(), platform=platform))

    # Return an empty response to Twilio
    resp = MessagingResponse()
    return Response(content=str(resp), media_type="application/xml")

