import openai
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from config import BOT_TEMPLATE, TEMPERATURE_VALUE, IMAGE_SIZE, SELECTED_MODEL, ZAPIER_NLA_API_KEY
import urllib.request
import librosa
import soundfile as sf
from langchain.llms import OpenAI
from langchain.agents import initialize_agent
from langchain.agents.agent_toolkits import ZapierToolkit
from langchain.utilities.zapier import ZapierNLAWrapper
from typing import Dict
ZAPIER_NLA_API_KEY=ZAPIER_NLA_API_KEY

llm = OpenAI(temperature=0)
zapier = ZapierNLAWrapper()
toolkit = ZapierToolkit.from_zapier_nla_wrapper(zapier)
agent = initialize_agent(toolkit.get_tools(), llm, agent="zero-shot-react-description", verbose=True)

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



# Initialize a dictionary to keep track of the last message for each user
last_messages: Dict[int, str] = {}

# async def process_chat_message(text: str ,chat_id: int):
async def process_chat_message(text: str, chat_id: int):


    print('prompt: ', text)

    
        # Get the last 3 messages for this user
    last_3_messages = last_messages.get(chat_id, ["", "", ""])
    history_string =f"""\n{last_3_messages[0]}\n{last_3_messages[1]}\n{last_3_messages[2]}\n"""


    print('history: ', history_string)
    
    # Create a prompt that includes the last 3 messages as context
    # template = f"Conversation history:\n{last_3_messages[0]}\n{last_3_messages[1]}\n{last_3_messages[2]}\n\nBot: {{human_input}}"
    # prompt = PromptTemplate(
    #     input_variables=["history", "human_input"],
    #     template=template
    # )

    topic_template = """
    You're going to help a chatbot decide on what next action to take.
    You have 3 options:
    - the user just wants to chat
    - he wants to get an image from you
    - he wants to put something in his calendar

    Return a single word: chat, image, calendar
    Conversation history:{history}
    User message : {human_input}
    The user wants:"""


    prompt = PromptTemplate(
        # input_variables=["human_input"],
        input_variables=["history", "human_input"],
        template=topic_template
    )

    chatgpt_chain = LLMChain(
        llm=initialize_language_model(SELECTED_MODEL),
        prompt=prompt,
        verbose=False,
        memory=ConversationBufferMemory(),
    )

    topic = chatgpt_chain.predict(history=history_string, human_input=text)
    print('topic: ', topic)


    if topic == 'chat':
      # Generate a response based on user's message
      template = BOT_TEMPLATE
      prompt = PromptTemplate(
          input_variables=["history", "human_input"],
          template=template
      )

      chatgpt_chain = LLMChain(
          llm=initialize_language_model(SELECTED_MODEL),
          prompt=prompt,
          verbose=False,
          memory=ConversationBufferMemory(),
      )
      # Predict the response for the given input
      # Generate a response based on the user's message and the last 3 messages
      output = chatgpt_chain.predict(history=history_string, human_input=text)

    elif topic == 'image':
      # Generate a response based on user's message
      template = """
      The user wants an image from you. You will get it from DALL-E / Stable Diffusion.
      Based on the User message and history (if relevant) do you have information about what the image is about?
      If so create an awesome prompt for DALL-E. It should create a prompt relevant to what the user is looking for. 
      If it is not clear what the image should be about; return this exact message 'false'.
      Conversation history:{history}
      User message : {human_input}
      Prompt for image:"""

      prompt = PromptTemplate(
          input_variables=["history", "human_input"],
          template=template
      )

      chatgpt_chain = LLMChain(
          llm=initialize_language_model(SELECTED_MODEL),
          prompt=prompt,
          verbose=False,
          memory=ConversationBufferMemory(),
      )
      # Predict the response for the given input
      # Generate a response based on the user's message and the last 3 messages
      prompt_text = chatgpt_chain.predict(history=history_string, human_input=text)

      if prompt_text == 'false':
        
        output = 'Please provide more details about the image your looking for.'

      else:

        try:
          response = openai.Image.create(
              prompt=prompt_text,
              n=1,
              size=IMAGE_SIZE,
          )
          deissue = False
          image = response["data"][0]["url"]
        except:
            deissue = True

        if deissue:
            output = "Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system"
        else:
            output = ('image of '+prompt_text, image)

      print('output image: ', output)


          
    elif topic == 'calendar':
      # Generate a response based on user's message
      template = """
      You're a bot and you need to put an event in a Calendar. Based on the User message try to extract the following data. Translate the data into english. If it's not available in the message, don't use it.
      Summary:
      Location:
      Start Date & Time:
      End Date & Time: (no end date or duration is, make this 1 hour from Start Time)
      Description:

      Return a text with the available data and start with 'Add Event <relevant data>'. Example: 'Add Event on 13-01-2023, Description: text1, Summary: text2 ...'

      Conversation history:{history}
      User message : {human_input}
      Calendar info:"""

      prompt = PromptTemplate(
          input_variables=["history", "human_input"],
          template=template
      )


      chatgpt_chain = LLMChain(
          llm=initialize_language_model(SELECTED_MODEL),
          prompt=prompt,
          verbose=True,
          memory=ConversationBufferMemory(),
      )
      # Predict the response for the given input
      # Generate a response based on the user's message and the last 3 messages
      prompt_calendar = chatgpt_chain.predict(history=history_string, human_input=text)
      print(prompt_calendar)
      # zapier = ZapierNLAWrapper()
      # toolkit = ZapierToolkit.from_zapier_nla_wrapper(zapier)
      # agent = initialize_agent(toolkit.get_tools(), initialize_language_model(SELECTED_MODEL), agent="zero-shot-react-description", verbose=True)
      response = agent.run(prompt_calendar
                          )
      output = response

      # print(output)
        # Update the last messages for this user
    last_messages[chat_id] = [text] + last_3_messages[:-1]
  
    return output