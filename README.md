## Project Setup 

* How to use you need this two api keys mentions below 
    1. Create a telegram bot using @BotFather and get the token in env variable TELEGRAM_BOT_TOKEN
    2. Get OpenAI API key and put it in env variable OPENAI_API_KEY or Cohere API key and put it in env variable 

* Create .env file and add following variables
    ```
    TELEGRAM_BOT_TOKEN=
    OPENAI_API_KEY=
    temperature_value=
    ```

* Run FastAPI Server: ``uvicorn main:app --reload --port 8000``

* Bind with NGROK : ngrok http 8000

* Finally Submit your bot: 
    1. Connect with telegram bot using this put telegram token and your server ip or domain to connect with telegram bot webhook: https://api.telegram.org/bot{YOUR_TOKEN}/setWebhook?url={YOUR_WEBHOOK_ENDPOINT}
    - YOUR_WEBHOOK_ENDPOINT: This will be complete webhook endpoint with Domain of NGROK




