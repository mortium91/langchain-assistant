import openai
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferMemory
from config import BOT_TEMPLATE, TEMPERATURE_VALUE, IMAGE_SIZE
import urllib.request
import librosa
import soundfile as sf

async def process_chat_message(text: str):
    # Check if "image" is in the user's message
    flag = "/image" in text.lower()

    # Generate an image based on user's message
    try:
        response = openai.Image.create(
            prompt=text,
            n=1,
            size=IMAGE_SIZE,
        )
        deissue = False
        image = response["data"][0]["url"]
    except:
        deissue = True

    # Generate a summary based on user's message
    template = BOT_TEMPLATE
    prompt = PromptTemplate(
        input_variables=["history", "human_input"],
        template=template
    )

    chatgpt_chain = LLMChain(
        llm=OpenAI(temperature=TEMPERATURE_VALUE),
        prompt=prompt,
        verbose=False,
        memory=ConversationBufferMemory(),
    )

    # Predict the response for the given input
    output = chatgpt_chain.predict(human_input=text)

    # Check if there was an issue with the image generation and handle accordingly
    if flag:
        if deissue:
            output = "Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system"
        else:
            output = (output, image)

    return output
