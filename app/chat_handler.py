from typing import Dict, Union, Tuple
from models import initialize_language_model
from templates import get_template
from config import SELECTED_MODEL
from utils import get_topic, process_chat, process_image, process_calendar

# Initialize a dictionary to keep track of the last message for each user
last_messages: Dict[int, str] = {}

async def process_chat_message(text: str, chat_id: int) -> Union[str, Tuple[str, str]]:
    """
    Process an incoming chat message and generate an appropriate response.
    Args:
        text (str): Input text message.
        chat_id (int): Unique identifier for the chat.
    Returns:
        Union[str, Tuple[str, str]]: The generated response as a string, or a tuple containing a string and an image URL.
    """
    # Get the last 3 messages for this user
    last_3_messages = last_messages.get(chat_id, ["", "", ""])
    history_string = f"""\n{last_3_messages[0]}\n{last_3_messages[1]}\n{last_3_messages[2]}\n"""

    # Determine the topic
    topic = await get_topic(text, history_string)
    print('topic: ', topic)
    # Process the message based on the topic
    output = ""
    if topic == "chat":
        output = process_chat(text, history_string)
    elif topic == "image":
        output = await process_image(text, history_string)
    elif topic == "calendar":
        output = process_calendar(text, history_string)

    # Update the last messages for this user
    last_messages[chat_id] = [text] + last_3_messages[:-1]
    print(output)
    return output
