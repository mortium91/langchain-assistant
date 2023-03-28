import httpx
from fastapi import FastAPI, Request
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate

from langchain.chains.conversation.memory import ConversationBufferMemory, ConversationSummaryMemory

TOKEN = "6143326122:AAHO0f2_H8pZCu2HS7tpcW5IgPHyOWwwGYM"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
import os

os.environ["OPENAI_API_KEY"] = "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"

client = httpx.AsyncClient()

app = FastAPI()

@app.post("/webhook/")
async def webhook(req: Request):
    data = await req.json()
    # print(data)
    chat_id = data['message']['chat']['id']
    text = data['message']['text']
    print(text)
    template = """Jinni is a large language model trained by OpenAI.
    Jinni is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Jinni is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.
    Jinni is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Jinni is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.
    Overall, Jinni is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Jinni is here to assist.
    {history}
    Human: {human_input}
    Jinni:"""
    prompt = PromptTemplate(
    input_variables=["history", "human_input"],
    template=template
    )
    chatgpt_chain = LLMChain(
    llm=OpenAI(temperature=0),
    prompt=prompt,
    verbose=False,
    # memory=ConversationalBufferWindowMemory(k=2),
    memory=ConversationBufferMemory(),
    )
    
    output = chatgpt_chain.predict(human_input=text)
    print("Chatbot: ", output)
    await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text={output}")
    return output
        
        
        
        
# https://api.telegram.org/bot{YOUR_TOKEN}/setWebhook?url={YOUR_WEBHOOK_ENDPOINT}  connect with webhook 
# >uvicorn newbot:app --reload --port 9000