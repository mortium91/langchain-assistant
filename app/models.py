from langchain.chat_models import ChatOpenAI
from config import TEMPERATURE_VALUE
from langchain import OpenAI

def initialize_language_model(selected_model):
    if selected_model == 'gpt-3':
        # Initialize GPT-3 model here
        return OpenAI(temperature=TEMPERATURE_VALUE)
    elif selected_model == 'gpt-3.5-turbo':
        # Initialize GPT-3.5 model here
        return ChatOpenAI(model_name="gpt-3.5-turbo",temperature=TEMPERATURE_VALUE)
    elif selected_model == 'gpt-4':
        # Initialize GPT-4 model here
        return ChatOpenAI(model_name="gpt-4",temperature=TEMPERATURE_VALUE)
    else:
        raise ValueError(f"Invalid model selected: {selected_model}")