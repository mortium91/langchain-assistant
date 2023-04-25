from config import BOT_NAME

def get_template(template_type: str) -> str:
    """
    Return a prompt template based on the template type.

    Args:
        template_type (str): The type of template to return.

    Returns:
        str: The prompt template.
    """
    if template_type == "topic":
        return """
        You're going to help a chatbot decide on what next action to take.
        You have 3 options:
        - the user just wants to chat
        - he wants to get an image from you
        - he wants to put something in his calendar

        Return a single word: chat, image, calendar
        Conversation history:{history}
        User message : {human_input}
        The user wants:
        """

    elif template_type == "chat":
        return f"""
        {BOT_NAME} trained by OpenAI.
        {BOT_NAME} is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, {BOT_NAME} is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.
        {BOT_NAME} is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, {BOT_NAME} is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.
        Overall, {BOT_NAME} is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, {BOT_NAME} is here to assist.
        History of relevant conversation to the current topic:

        {{history}}

        Recent conversaton: 

        {{recent_history}}
        
        Human: {{human_input}}
        {BOT_NAME} AI response:
        """

    elif template_type == "image":
        return """
        The user wants an image from you. You will get it from DALL-E / Stable Diffusion.
        Based on the User message and history (if relevant) do you have information about what the image is about?
        If so create an awesome prompt for DALL-E. It should create a prompt relevant to what the user is looking for. 
        If it is not clear what the image should be about; return this exact message 'false'.
        Conversation history:{history}
        User message : {human_input}
        Prompt for image:
        """

    elif template_type == "calendar":
        return """
        You're a bot and you need to put an event in a Calendar. Based on the User message try to extract the following data. Translate the data into english. If it's not available in the message, don't use it.
        Summary:
        Location:
        Start Date & Time:
        End Date & Time: (no end date or duration is, make this 1 hour from Start Time)
        Description:

        Return a text with the available data and start with 'Add Event <relevant data>'. Example: 'Add Event on 13-01-2023, Description: text1, Summary: text2 ...'

        Conversation history:{history}
        User message : {human_input}
        Calendar info:
        """

    else:
        raise ValueError(f"Invalid template type: {template_type}")
