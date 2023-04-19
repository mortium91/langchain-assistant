import os
import openai
import pinecone
import time
import sys
from collections import deque
from typing import Dict, List
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from config import BABYAGI, ACCOUNT_SID, AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, FACEBOOK_PAGE_ID

if BABYAGI:
  # Load environment variables
  load_dotenv()
  
  # Set API Keys and other environment variables
  OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
  PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
  PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
  YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")
  YOUR_FIRST_TASK = os.getenv("FIRST_TASK", "")
  USE_GPT4 = os.getenv("USE_GPT4", True)
  
  # Ensure required variables are set
  if not OPENAI_API_KEY:
      print("OPENAI_API_KEY environment variable is missing from .env")
  if not YOUR_TABLE_NAME:
      print("TABLE_NAME environment variable is missing from .env")
  if not YOUR_FIRST_TASK:
      print("FIRST_TASK environment variable is missing from .env")
  
  # Configure OpenAI and Pinecone
  openai.api_key = OPENAI_API_KEY
  if PINECONE_API_KEY:
      pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
  
  # Create Pinecone index if PINECONE_API_KEY is set
  if PINECONE_API_KEY and YOUR_TABLE_NAME not in pinecone.list_indexes():
      pinecone.create_index(YOUR_TABLE_NAME, dimension=1536, metric="cosine", pod_type="p1")
  
  # Connect to the index if PINECONE_API_KEY is set
  if PINECONE_API_KEY:
      index = pinecone.Index(YOUR_TABLE_NAME)
  
  # Task list
  task_list = deque([])
  
# Functions
def add_task(task: Dict):
    task_list.append(task)

def get_ada_embedding(text: str) -> List[float]:
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

def openai_call(prompt: str, use_gpt4: bool = False, temperature: float = 0.5, max_tokens: int = 100):
    if not use_gpt4:
        # Call GPT-3 DaVinci model
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].text.strip()
    else:
        # Call GPT-4 chat model
        messages = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            n=1,
            stop=None,
        )
        return response.choices[0].message.content.strip()

def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str], gpt_version: str = 'gpt-3'):
    prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."
    response = openai_call(prompt, USE_GPT4)
    new_tasks = response.split('\n')
    return [{"task_name": task_name} for task_name in new_tasks]


def prioritization_agent(this_task_id: int, objective, gpt_version: str = 'gpt-3'):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id)+1
    prompt = f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{objective}. Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    response = openai_call(prompt, USE_GPT4)
    new_tasks = response.split('\n')
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})


def execution_agent(objective: str, task: str, gpt_version: str = 'gpt-3') -> str:
    #context = context_agent(index="quickstart", query="my_search_query", n=5)
    context = context_agent(index=YOUR_TABLE_NAME, query=objective, n=5)
    #print("\n*******RELEVANT CONTEXT******\n")
    # print(context)
    prompt = f"You are an AI who performs one task based on the following objective: {objective}.\nTake into account these previously completed tasks: {context}\nYour task: {task}\nResponse:"
    return openai_call(prompt, USE_GPT4, 0.7, 2000)


def context_agent(query: str, index: str, n: int):
    query_embedding = get_ada_embedding(query)
    index = pinecone.Index(index_name=index)
    results = index.query(query_embedding, top_k=n,
                          include_metadata=True)
    #print("***** RESULTS *****")
    # print(results)
    sorted_results = sorted(
        results.matches, key=lambda x: x.score, reverse=True)
    return [(str(item.metadata['task'])) for item in sorted_results]

async def send_message(chat_id: str, message: str, platform: str, client=None, base_url=None):
    if platform == 'telegram':
        await client.get(f"{base_url}/sendMessage?chat_id={chat_id}&text={message}")
    elif platform == 'twilio':
        await send_twilio_message(chat_id, message)

async def process_task(objective: str, chat_id: str, platform='telegram', client=None, base_url=None):
    first_task = {
        "task_id": 1,
        "task_name": YOUR_FIRST_TASK
    }

    add_task(first_task)

    task_id_counter = 1
    while True:
        if task_list:
            # Print the task list
            print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m")
            temp = ""
            for t in task_list:
                tsk = str(t['task_id']) + ": " + t['task_name']
                print(tsk)
                temp = temp + tsk + "\n"

            await send_message(chat_id, temp, platform, client, base_url)

            # Step 1: Pull the first task
            task = task_list.popleft()
            print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
            next_tsk = str(task['task_id']) + ": " + task['task_name']
            print(next_tsk)

            await send_message(chat_id, next_tsk, platform, client, base_url)

            # Send to execution function to complete the task based on the context
            result = execution_agent(objective, task["task_name"])
            this_task_id = int(task["task_id"])
            print("\033[93m\033[1m" + "\n*****TASK RESULT*****\n" + "\033[0m\033[0m")
            print(result)

            await send_message(chat_id, result, platform, client, base_url)

            # Step 2: Enrich result and store in Pinecone
            # This is where you should enrich the result if needed
            enriched_result = {'data': result}
            result_id = f"result_{task['task_id']}"
            # extract the actual result from the dictionary
            vector = enriched_result['data']
            index.upsert([(result_id, get_ada_embedding(vector), {
                "task": task['task_name'], "result": result})])

        # Step 3: Create new tasks and reprioritize task list
        if task_id_counter < 6:
            print(f"tt: {task_id_counter}")
            new_tasks = task_creation_agent(objective, enriched_result, task["task_name"], [
                                            t["task_name"] for t in task_list])

            for new_task in new_tasks:
                task_id_counter += 1
                new_task.update({"task_id": task_id_counter})
                add_task(new_task)
            prioritization_agent(this_task_id, objective)
        if len(task_list) < 1:
            print("Tasks completed")
            await send_message(chat_id, "\n\nTask completed", platform, client, base_url)
            break


async def send_twilio_message(chat_id: str, message: str, platform: str = "whatsapp"):
    account_sid = ACCOUNT_SID
    auth_token = AUTH_TOKEN
    client = Client(account_sid, auth_token)

    if platform not in ("whatsapp", "messenger"):
        raise ValueError("Invalid platform specified. Valid platforms are 'whatsapp' and 'messenger'.")

    if platform == "whatsapp" and not TWILIO_WHATSAPP_NUMBER:
        print("Twilio WhatsApp number not configured. Please set the TWILIO_WHATSAPP_NUMBER environment variable.")
        return
    elif platform == "messenger" and not FACEBOOK_PAGE_ID:
        print("Facebook Page ID not configured. Please set the FACEBOOK_PAGE_ID environment variable.")
        return

    if platform == "messenger":
        twilio_phone_number = f'messenger:{FACEBOOK_PAGE_ID}'
    else:
        twilio_phone_number = f'whatsapp:{TWILIO_WHATSAPP_NUMBER}'

    try:
        client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=chat_id
        )
    except TwilioException as e:
        print(f"Error sending message: {e}")