# LangChain Assistant

LangChain Assistant is a versatile chatbot that leverages state-of-the-art Language Models (currently GPT-3) to interact with users via Telegram and WhatsApp. The primary goal is to keep AI development open, fun, and accessible. LangChain Assistant can handle text messages, voice messages, and even generate images using OpenAI's DALL-E.


## Features

- Communicate with OpenAIs GPT-3, GPT-3.5-Turbo, GPT-4 models via config.py
- Support for text and voice messages
- Integration with Telegram and WhatsApp
- Generate images using OpenAI's DALL-E


## Roadmap

- Support gpt4all
- Support Facebook Messenger 
- Send emails
- Add events to calendar
- Write and store code ideas
- Docker support
- AGI...
- ... and more!


## Get Images from DALL-E

To generate images using OpenAI's DALL-E, include the text '/image' in your chat message. The default image size is "256x256" and can be modified in the `config.py` file.


## Deployment

### Try for Free

To deploy LangChain Assistant for free on Replit:

- [Telegram guide](https://searchwith.ai/blog/your-own-chatgpt-ai-assistant-on-telegram-with-langchain)
- [WhatsApp Guide](https://searchwith.ai/blog/create-your-own-chatgpt-ai-assistant-on-whatsapp)


### Prerequisites

- Python 3.7 or higher
- A Telegram bot token from @BotFather
- An OpenAI API key
- A Twilio account with a WhatsApp enabled phone number


### Installation

1. Clone the repository and navigate to the project directory.

2. Install the required Python packages:

```pip install -r requirements.txt```

3. Create a `.env` file in the project directory and add the following variables:
    ```
    TELEGRAM_BOT_TOKEN=
    OPENAI_API_KEY=
    TEMPERATURE_VALUE=
    ACCOUNT_SID= #Twillio
    AUTH_TOKEN= #Twillio
    ```


### Setup Telegram

1. Run the FastAPI server:
```
uvicorn main:app --reload --port 8000
```

(when running locally on Windows)
2. Expose the local server using NGROK:
```
ngrok http 8000
```

3. Set up the webhook for your Telegram bot:

- Replace `{YOUR_TOKEN}` with your Telegram bot token.
- Replace `{YOUR_WEBHOOK_ENDPOINT}` with your NGROK domain followed by `/webhook/`.

```
https://api.telegram.org/bot{YOUR_TOKEN}/setWebhook?url={YOUR_WEBHOOK_ENDPOINT}
```


### Setup WhatsApp

1. Activate the Twilio Sandbox for WhatsApp and obtain the Account SID and Auth Token.

2. Add the Twilio WhatsApp phone number to your contacts and send a message to join the sandbox.

3. Update the webhook URL in the Twilio Sandbox settings with your FastAPI server URL.

For more details, follow the Twilio tutorial: [Send and Receive Media Messages with WhatsApp in Python](https://www.twilio.com/docs/whatsapp/tutorial/send-and-receive-media-messages-whatsapp-python)
