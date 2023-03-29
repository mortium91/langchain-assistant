## Project Setup 

* How to use you need this two api keys mentions below 
    1. Create a telegram bot using @BotFather and get the token in env variable TELEGRAM_BOT_TOKEN
    2. Get OpenAI API key and put it in env variable OPENAI_API_KEY or Cohere API key and put it in env variable 

* After You get key 
    1. Connect with telegram bot using this put telegram token and your server ip or domain to connect with telegram bot webhook: https://api.telegram.org/bot{YOUR_TOKEN}/setWebhook?url={YOUR_WEBHOOK_ENDPOINT}

* After You connect with sucessfully run you FastAPI : uvicorn main:app --reload --port 8000


