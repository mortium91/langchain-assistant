from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from chat_handler import process_chat_message

twilio_api_reply = APIRouter()


@twilio_api_reply.post("/api")
async def handle_twilio_api_reply(Body: str = Form()):
    output = await process_chat_message(Body)

    resp = MessagingResponse()
    if isinstance(output, tuple):
        summary, image = output
        response_msg = resp.message(summary)
        response_msg.media(image)
    else:
        response_msg = resp.message(output)

    return Response(content=str(resp), media_type="application/xml")
