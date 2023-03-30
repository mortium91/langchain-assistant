import httpx
from fastapi import FastAPI, Request
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
import openai
from langchain.chains.conversation.memory import ConversationBufferMemory, ConversationSummaryMemory
import  telegram
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
    
    text = data['message']['text']
    print(text)
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