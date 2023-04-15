from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from chat_handler import process_chat_message
from voice_handler import process_voice_message
from babyagi import process_task

twilio_api_reply = APIRouter()


@twilio_api_reply.post("/api")
async def handle_twilio_api_reply(Body: str = Form(""), MediaUrl0: str = Form("")):
    """
    Handle incoming text or voice messages from Twilio and generate appropriate responses.

    Args:
        Body (str): Input text message.
        MediaUrl0 (str): URL of the voice message.

    Returns:
        Response: The generated response as a text message or a photo with a caption, depending on the type of output.
    """
    if MediaUrl0:
        # Process voice messages
        output = await process_voice_message(MediaUrl0, 0)
    else:
        # Process text messages

        resp = MessagingResponse()
        text = Body.lower()
        if text[0:5] == "/task":
            task = text[5:]
            responses = await process_task(task)
            response_msg = resp.message(responses)
            return Response(content=str(resp), media_type="application/xml")

        output = await process_chat_message(Body, 0)

        # Send the output as a text message or a photo with a caption, depending on the type of output
        if isinstance(output, tuple):
            summary, image = output
            response_msg = resp.message(summary)
            response_msg.media(image)
        else:
            response_msg = resp.message(output)

        return Response(content=str(resp), media_type="application/xml")
