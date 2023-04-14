import openai
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from config import SELECTED_MODEL, IMAGE_SIZE, ZAPIER_NLA_API_KEY, BOT_NAME
from models import initialize_language_model
from templates import get_template
from langchain.agents.agent_toolkits import ZapierToolkit
from langchain.utilities.zapier import ZapierNLAWrapper
from langchain.agents import initialize_agent


if ZAPIER_NLA_API_KEY:
    llm = OpenAI(temperature=0)
    zapier = ZapierNLAWrapper()
    toolkit = ZapierToolkit.from_zapier_nla_wrapper(zapier)
    agent = initialize_agent(toolkit.get_tools(), llm, agent="zero-shot-react-description", verbose=True)
else:
    zapier = None
    toolkit = None
    agent = None

async def get_topic(text: str, history_string: str) -> str:
    """
    Get the topic of the given text based on the conversation history.

    Args:
        text (str): Input text message.
        history_string (str): Formatted conversation history string.

    Returns:
        str: The detected topic.
    """
    prompt_template = get_template("topic")
    prompt = PromptTemplate(input_variables=["history", "human_input"], template=prompt_template)

    chatgpt_chain = LLMChain(
        llm=initialize_language_model(SELECTED_MODEL),
        prompt=prompt,
        verbose=False,
        memory=ConversationBufferMemory(),
    )

    topic = chatgpt_chain.predict(history=history_string, human_input=text)

    return topic

def process_chat(text: str, history_string: str) -> str:
    """
    Process a chat message and generate a response.

    Args:
        text (str): Input text message.
        history_string (str): Formatted conversation history string.

    Returns:
        str: The generated response.
    """
    prompt_template = get_template("chat")
    prompt = PromptTemplate(input_variables=["history", "human_input"], template=prompt_template)

    chatgpt_chain = LLMChain(
        llm=initialize_language_model(SELECTED_MODEL),
        prompt=prompt,
        verbose=False,
        memory=ConversationBufferMemory(),
    )

    output = chatgpt_chain.predict(history=history_string, human_input=text)

    return output

async def process_image(text: str, history_string: str) -> str:
    """
    Process an image request and generate a response.

    Args:
        text (str): Input text message.
        history_string (str): Formatted conversation history string.

    Returns:
        str: The generated response.
    """
    prompt_template = get_template("image")
    prompt = PromptTemplate(input_variables=["history", "human_input"], template=prompt_template)

    chatgpt_chain = LLMChain(
        llm=initialize_language_model(SELECTED_MODEL),
        prompt=prompt,
        verbose=False,
        memory=ConversationBufferMemory(),
    )

    prompt_text = chatgpt_chain.predict(history=history_string, human_input=text)

    if prompt_text == "false":
        output = "Please provide more details about the image you're looking for."
    else:
        try:
            response = openai.Image.create(prompt=prompt_text, n=1, size=IMAGE_SIZE)
            deissue = False
            image = response["data"][0]["url"]
        except:
            deissue = True

        if deissue:
            output = "Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system."
        else:
            output = ("image of " + prompt_text, image)

    return output

def process_calendar(text: str, history_string: str) -> str:
    """
    Process a calendar event request and generate a response.

    Args:
        text (str): Input text message.
        history_string (str): Formatted conversation history string.

    Returns:
        str: The generated response.
    """
    if agent is None:
        return f"{BOT_NAME}: I'm sorry, but I cannot access your calendar without proper configuration. Please configure the Zapier API key to enable calendar integration."

    prompt_template = get_template("calendar")
    prompt = PromptTemplate(input_variables=["history", "human_input"], template=prompt_template)

    chatgpt_chain = LLMChain(
        llm=initialize_language_model(SELECTED_MODEL),
        prompt=prompt,
        verbose=False,
        memory=ConversationBufferMemory(),
    )

    prompt_calendar = chatgpt_chain.predict(history=history_string, human_input=text)
    output = agent.run(prompt_calendar)

    return output