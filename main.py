import httpx
import openai
import os
import telegram
from fastapi import FastAPI, Request, Response, Form, Depends
from twilio.twiml.messaging_response import MessagingResponse
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferMemory, ConversationSummaryMemory

from config import TOKEN, openai_api_key, botTemplate, temperature_value

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Initialize HTTP client and Telegram bot
client = httpx.AsyncClient()
bot = telegram.Bot(token=TOKEN)

# Initialize FastAPI application
app = FastAPI()

# Define a webhook route for Telegram
@app.post("/webhook/")
async def telegram_webhook(req: Request):
    data = await req.json()
    
    chat_id = data['message']['chat']['id']
    try:
        text = data['message']['text']
        print(text)
    except:
        pass
    
    # Check if "image" is in the user's message
    flag = "image" in text.lower()

    # Generate an image based on user's message
    try:    
        response = openai.Image.create(
        prompt=text,
        n=1,
        size="256x256",
        )
        deissue = False
        image = response["data"][0]["url"]
        
    except:
        deissue = True
    
    # Generate a summary based on user's message
    template = botTemplate
    prompt = PromptTemplate(
        input_variables=["history", "human_input"],
        template=template
    )
    
    chatgpt_chain = LLMChain(
        llm=OpenAI(temperature=temperature_value),
        prompt=prompt,
        verbose=False,
        memory=ConversationBufferMemory(),
    )
    
    output = chatgpt_chain.predict(human_input=text)
    
    # If the user requested an image and it was generated successfully, send the image
    if flag:
        if deissue:
            output = "Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system"
        else:
            await bot.send_photo(chat_id, image)        
    # Otherwise, send the summary
    else:
        await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={output}")
        
    return output

# Define an API route for Twilio
@app.post("/api")
async def twilio_api_reply(Body: str = Form()):
    
    # Check if "image" is in the user's message
    flag = "image" in Body.lower()
    
    # Generate an image based on user's message
    response = openai.Image.create(
        prompt=Body,
        n=1,
        size="256x256",
    )
    image = response["data"][0]["url"]
    
    # Generate a summary based on user's message
    template = botTemplate
    prompt = PromptTemplate(
        input_variables=["history", "human_input"],
        template=template
    )
    
    chatgpt_chain = LLMChain(
        llm=OpenAI(temperature=0),
        prompt=prompt,
        verbose=False,
        memory=ConversationBufferMemory(),
    )
    output = chatgpt_chain.predict(human_input=Body)
   
    # Create a Twilio messaging response with the generated image and summary
    resp = MessagingResponse()
    if flag:    
        response_msg = resp.message(output)
        response_msg.media(image)
    else:
        response_msg = resp.message