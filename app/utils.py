import os
import faiss
import pickle
import config
import openai
import functools
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferWindowMemory, ConversationBufferMemory
from langchain.agents.agent_toolkits import ZapierToolkit
from langchain.utilities.zapier import ZapierNLAWrapper
from langchain.agents import initialize_agent
from langchain.docstore import InMemoryDocstore
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import VectorStoreRetrieverMemory, CombinedMemory
from langchain.chat_models import ChatOpenAI
from config import SELECTED_MODEL, IMAGE_SIZE, ZAPIER_NLA_API_KEY, BOT_NAME
from models import initialize_language_model
from templates import get_template



if ZAPIER_NLA_API_KEY:
    llm = OpenAI(temperature=0)
    zapier = ZapierNLAWrapper()
    toolkit = ZapierToolkit.from_zapier_nla_wrapper(zapier)
    agent = initialize_agent(toolkit.get_tools(), llm, agent="zero-shot-react-description", verbose=True)
else:
    zapier = None
    toolkit = None
    agent = None


def load_memory(chat_id: str):
    '''Loads memory for langchain chain 
    It is a combination of two types of memory - first: Faiss based memory and 
    second: recent K interaction memory. Faiss baised memory retrieves top P related
    memory to the curent input. This has the benefit of being able to retrieve contextual
    memory that is burried deep in the conversation history, but also being highly 
    relevant to the latest interactions.

    Args:
        chat_id (str): Chat id (used for caching)

    Returns:
        memory object for langchain chain
    '''

    # First check if memory is saved on disk and load it

    fp = os.path.join(config.HISTORY_DIR, '{}_memory.p'.format(chat_id))
    try:
        with open(fp, 'rb') as f:
            memory = pickle.load(f)
            return memory
    except FileNotFoundError:
        pass

    # Create new memory
    memconfig = config.MEMORYCONFIG
    embedding_size = 1536 # Dimensions of the OpenAIEmbeddings
    index = faiss.IndexFlatL2(embedding_size)
    embedding_fn = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY).embed_query
    vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})
    retriever = vectorstore.as_retriever(search_kwargs=dict(k=memconfig["K_latest"]))

    conv_memory = ConversationBufferWindowMemory(
        memory_key="recent_history",
        input_key="human_input",
        k=memconfig["K_latest"], # Number of latest interactions to keep in memory
    )

    faissmemory = VectorStoreRetrieverMemory(retriever=retriever)

    memory = CombinedMemory(memories=[faissmemory, conv_memory])
    return memory


@functools.cache
def load_chat_model(chat_id: str):
    ''' Loads the langchain chain for chat.
        cache is used to avoid reloading the model for each request

    Args:
        chat_id (str): Chat id (used for caching)

    Returns:
        langchain chain for chat
    '''
    print ('Loading chat model...')
    prompt_template = get_template("chat")
    prompt = PromptTemplate(input_variables=["history", "recent_history", "human_input"], template=prompt_template)
    memory = load_memory(chat_id)
    return LLMChain(
        llm=initialize_language_model(SELECTED_MODEL),
        prompt=prompt,
        verbose=True,
        memory=memory
    )


def save_memory_to_disk(chat_id, chatgpt_chain):
    ''' Saves the memory of the langchain chain to disk '''
    # TODO memory is currently serialized and saved at every step
    # It's probably better to do it on exit or on every 10 steps etc.
    
    if not os.path.exists(config.HISTORY_DIR):
        os.makedirs(config.HISTORY_DIR)
    fp = os.path.join(config.HISTORY_DIR, '{}_memory.p'.format(chat_id))
    with open(fp, 'wb') as f:
        pickle.dump(chatgpt_chain.memory, f, protocol=pickle.HIGHEST_PROTOCOL)


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

def process_chat(chat_id:str, text: str, history_string: str) -> str:
    """
    Process a chat message and generate a response.

    Args:
        chat_id(str): Chat id (used for caching)
        text (str): Input text message.
        history_string (str): Formatted conversation history string.

    Returns:
        str: The generated response.
    """

    chatgpt_chain = load_chat_model(chat_id)
    output = chatgpt_chain.predict(human_input=text)
    save_memory_to_disk(chat_id, chatgpt_chain)
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