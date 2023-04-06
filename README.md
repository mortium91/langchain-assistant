# LangChain Assistant

A simple setup to chat with LLMs (GPT3 for now) via Telegram and Whatsapp. 
Goal: keep the AI development open & fun!


## Deploy for Free
If you want to try it out for free:
[Setup on Replit guide](https://searchwith.ai/blog/your-own-chatgpt-ai-assistant-on-telegram-with-langchain)


Roadmap:
- Support more GPT models via config
- Send emails
- Add to calendar 
- Write and store some code ideas
- Docker support
- ....


## Host it yourself

* Install requirements : ``pip install -r requirements.txt``


### Setup Telegram

* How to use you need this two api keys mentions below 
    1. Create a telegram bot using @BotFather and get the token in env variable TELEGRAM_BOT_TOKEN
    2. Get OpenAI API key and put it in env variable OPENAI_API_KEY or Cohere API key and put it in env variable 

* Create .env file and add following variables
    ```
    TELEGRAM_BOT_TOKEN=
    OPENAI_API_KEY=
    TEMPERATURE_VALUE=
    ACCOUNT_SID= #Twillio
    AUTH_TOKEN= #Twillio
    ```

* Run FastAPI Server: ``uvicorn main:app --reload --port 8000``

(when running locally on Windows)
* Bind with NGROK : ngrok http 8000

* Finally Submit your bot: 
    1. Connect with telegram bot using this put telegram token and your server ip or domain to connect with telegram bot webhook: https://api.telegram.org/bot{YOUR_TOKEN}/setWebhook?url={YOUR_WEBHOOK_ENDPOINT}
    - YOUR_WEBHOOK_ENDPOINT: This will be complete webhook endpoint with Domain of NGROK


### Setup Whatsapp


* Before you can send a WhatsApp message from your web language, you'll need to sign up for a Twilio account or sign into your existing account and activate the Twilio Sandbox for WhatsApp. The Sandbox allows you to prototype with WhatsApp immediately using a shared phone number without waiting for your Twilio number to be approved by WhatsApp.

* After You Login In twilio You need 
1. Account SID - Used to identify yourself in API requests
2. Auth Token - Used to authenticate REST API requests

* Set in your .env file after all done you just need to get number from twilio and authenticate code ex- Join xyz

* Save Your twilio number in your contact list then send message join to join your sandbox 

* After All you need to set URL in sanbox setting just save your web api url in sanbox setting 

* Reference URL to follow -: https://www.twilio.com/docs/whatsapp/tutorial/send-and-receive-media-messages-whatsapp-python
