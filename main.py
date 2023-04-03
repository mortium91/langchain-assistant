import httpx
from fastapi import FastAPI, Request,Response
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
import openai
from langchain.chains.conversation.memory import ConversationBufferMemory, ConversationSummaryMemory
import  telegram
from fastapi import FastAPI, Form, Depends
from twilio.twiml.messaging_response import MessagingResponse


from config import TOKEN
from config import openai_api_key,botTemplate,temperature_value

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
import os
import requests
openai.api_key = os.getenv("OPENAI_API_KEY")

client = httpx.AsyncClient()
bot = telegram.Bot(token=TOKEN)
app = FastAPI()

@app.post("/webhook/")
async def webhook(req: Request):
    data = await req.json()
    
    chat_id = data['message']['chat']['id']
    try:
        text = data['message']['text']
        print(text)
    except:
        pass
    flag="image" in text.lower()

    #Image generate code
    try:    
        response = openai.Image.create(
        prompt=text,
        n=1,
        size="256x256",
        )
        deissue=False
        image=response["data"][0]["url"]
        
    except:
        deissue=True
    #Generate Summary about text
    template =botTemplate
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
    
    if flag:
        if deissue:
            output="Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system"
        else:
            await bot.send_photo(chat_id, image)        
    # else:
    await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={output}")
        

    return output


@app.post("/api")
async def reply(Body: str = Form()):
    
    
    flag="image" in Body.lower()
    
    response = openai.Image.create(
        prompt=Body,
        n=1,
        size="256x256",
        )
        
    image=response["data"][0]["url"]
    
    
    template =botTemplate
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
   
    resp = MessagingResponse()
    if flag:    
        response_msg = resp.message(output)
        response_msg.media(image)
    else:
        response_msg = resp.message(output)
        
        

    return Response(content=str(resp), media_type="application/xml")