import httpx
from fastapi import FastAPI, Request
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate

from langchain.chains.conversation.memory import ConversationBufferMemory, ConversationSummaryMemory

from config import TOKEN
from config import openai_api_key,botTemplate,temperature_value

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
import os

client = httpx.AsyncClient()

app = FastAPI()

@app.post("/webhook/")
async def webhook(req: Request):
    data = await req.json()
    
    chat_id = data['message']['chat']['id']
    text = data['message']['text']
    print(text)
    template =botTemplate
    prompt = PromptTemplate(
    input_variables=["history", "human_input"],
    template=template
    )
    chatgpt_chain = LLMChain(
    llm=OpenAI(temperature=temperature_value),
    prompt=prompt,
    verbose=False,
    # memory=ConversationalBufferWindowMemory(k=2),
    memory=ConversationBufferMemory(),
    )
     
     
    output = chatgpt_chain.predict(human_input=text)
    print("Chatbot: ", output)
    await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={output}")
    return output
        