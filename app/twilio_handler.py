from fastapi import APIRouter, Form, Response, Request
from twilio.twiml.messaging_response import MessagingResponse
from chat_handler import process_chat_message
from voice_handler import process_voice_message

twilio_api_reply = APIRouter()


@twilio_api_reply.post("/api")
async def handle_twilio_api_reply(request:Request,Body: str = Form(""), MediaUrl0: str = Form("")):
    """
    Handle incoming text or voice messages from Twilio and generate appropriate responses.

    Args:
        Body (str): Input text message.
        MediaUrl0 (str): URL of the voice message.

    Returns:
        Response: The generated response as a text message or a photo with a caption, depending on the type of output.
    """

    form_data= await request.form()
    chat_id=form_data.get("From")
    if MediaUrl0:
        # Process voice messages
        output = await process_voice_message(MediaUrl0, chat_id)
    else:
        # Process text messages
        output = await process_chat_message(Body, chat_id)

    print(output)
    resp = MessagingResponse()
    
    # Send the output as a text message or a photo with a caption, depending on the type of output
    if isinstance(output, tuple):
        summary, image = output
        response_msg = resp.message(summary)
        response_msg.media(image)
    else:
        response_msg = resp.message(output)

    return Response(content=str(resp), media_type="application/xml")
