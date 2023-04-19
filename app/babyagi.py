import os
import openai
import pinecone
import time
import sys
from collections import deque
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from config import BABYAGI, ACCOUNT_SID, AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, FACEBOOK_PAGE_ID
from langchain.docstore import InMemoryDocstore
from langchain import LLMChain, OpenAI, PromptTemplate, FAISS, SerpAPIWrapper
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains.base import Chain
from pydantic import BaseModel, Field
from langchain.llms import BaseLLM
from langchain.vectorstores.base import VectorStore
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
import faiss


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
    USE_PINECONE = os.getenv("USE_PINECONE", False)

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

    # Create Pinecone index or langchain vector store
    if PINECONE_API_KEY and USE_PINECONE:
        if YOUR_TABLE_NAME not in pinecone.list_indexes():
            pinecone.create_index(YOUR_TABLE_NAME, dimension=1536, metric="cosine", pod_type="p1")
        index = pinecone.Index(YOUR_TABLE_NAME)
    else:
        # Initialize the FAISS vector store
        embeddings_model = OpenAIEmbeddings()
        embedding_size = 1536
        index = faiss.IndexFlatL2(embedding_size)
        vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})


class TaskCreationChain(LLMChain):
    """Chain to generates tasks."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = True) -> LLMChain:
        """Get the response parser."""
        task_creation_template = (
            "You are an task creation AI that uses the result of an execution agent"
            " to create new tasks with the following objective: {objective},"
            " The last completed task has the result: {result}."
            " This result was based on this task description: {task_description}."
            " These are incomplete tasks: {incomplete_tasks}."
            " Based on the result, create new tasks to be completed"
            " by the AI system that do not overlap with incomplete tasks."
            " Return the tasks as an array."
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=["result", "task_description", "incomplete_tasks", "objective"],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

class TaskPrioritizationChain(LLMChain):
    """Chain to prioritize tasks."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = True) -> LLMChain:
        """Get the response parser."""
        task_prioritization_template = (
            "You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing"
            " the following tasks: {task_names}."
            " Consider the ultimate objective of your team: {objective}."
            " Do not remove any tasks. Return the result as a numbered list, like:"
            " #. First task"
            " #. Second task"
            " Start the task list with number {next_task_id}."
        )
        prompt = PromptTemplate(
            template=task_prioritization_template,
            input_variables=["task_names", "next_task_id", "objective"],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)


todo_prompt = PromptTemplate.from_template("You are a chat bot who is an expert at coming up with a todo list for a given objective. Come up with a todo list for this objective: {objective}")
todo_chain = LLMChain(llm=OpenAI(temperature=0), prompt=todo_prompt)
search = SerpAPIWrapper()
tools = [
    Tool(
        name = "Search",
        func=search.run,
        description="useful for when you need to answer questions about current events"
    ),
    Tool(
        name = "TODO",
        func=todo_chain.run,
        description="useful for when you need to come up with todo lists. Input: an objective to create a todo list for. Output: a todo list for that objective. Please be very clear what the objective is!"
    )
]


prefix = """You are an AI who performs one task based on the following objective: {objective}. Take into account these previously completed tasks: {context}."""
suffix = """Question: {task}
{agent_scratchpad}"""
prompt = ZeroShotAgent.create_prompt(
    tools, 
    prefix=prefix, 
    suffix=suffix, 
    input_variables=["objective", "task", "context","agent_scratchpad"]
)

def get_next_task(task_creation_chain: LLMChain, result: Dict, task_description: str, task_list: List[str], objective: str) -> List[Dict]:
    """Get the next task."""
    incomplete_tasks = ", ".join(task_list)
    response = task_creation_chain.run(result=result, task_description=task_description, incomplete_tasks=incomplete_tasks, objective=objective)
    new_tasks = response.split('\n')
    return [{"task_name": task_name} for task_name in new_tasks if task_name.strip()]

def prioritize_tasks(task_prioritization_chain: LLMChain, this_task_id: int, task_list: List[Dict], objective: str) -> List[Dict]:
    """Prioritize tasks."""
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id) + 1
    response = task_prioritization_chain.run(task_names=task_names, 
                                             next_task_id=next_task_id, 
                                             objective=objective)
    new_tasks = response.split('\n')
    prioritized_task_list = []
    for task_string in new_tasks:
        if not task_string.strip():
            continue
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            prioritized_task_list.append({"task_id": task_id, "task_name": task_name})
    return prioritized_task_list

def _get_top_tasks(vectorstore, query: str, k: int) -> List[str]:
    """Get the top k tasks based on the query."""
    results = vectorstore.similarity_search_with_score(query, k=k)
    if not results:
        return []
    sorted_results, _ = zip(*sorted(results, key=lambda x: x[1], reverse=True))
    return [str(item.metadata['task']) for item in sorted_results]

def execute_task(vectorstore, execution_chain: LLMChain, objective: str, task: str, k: int = 5) -> str:
    """Execute a task."""
    context = _get_top_tasks(vectorstore, query=objective, k=k)
    return execution_chain.run(objective=objective, context=context, task=task)


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

class BabyAGI(Chain, BaseModel):
    """Controller model for the BabyAGI agent."""

    task_list: deque = Field(default_factory=deque)
    task_creation_chain: TaskCreationChain = Field(...)
    task_prioritization_chain: TaskPrioritizationChain = Field(...)
    execution_chain: AgentExecutor = Field(...)
    task_id_counter: int = Field(1)
    vectorstore: VectorStore = Field(init=False)
    max_iterations: Optional[int] = None
        
    class Config:
        """Configuration for this pydantic object."""
        arbitrary_types_allowed = True

    def add_task(self, task: Dict):
        self.task_list.append(task)
  
    async def send_message(self, chat_id: str, message: str, platform: str, client=None, base_url=None):
      if platform == 'telegram':
          await client.get(f"{base_url}/sendMessage?chat_id={chat_id}&text={message}")
      elif platform == 'twilio':
          await self.send_twilio_message(chat_id, message)
  
  
    def print_task_list(self):
        print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m")
        for t in self.task_list:
            print(str(t["task_id"]) + ": " + t["task_name"])

    def print_next_task(self, task: Dict):
        print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
        print(str(task["task_id"]) + ": " + task["task_name"])

    def print_task_result(self, result: str):
        print("\033[93m\033[1m" + "\n*****TASK RESULT*****\n" + "\033[0m\033[0m")
        print(result)
        
    @property
    def input_keys(self) -> List[str]:
        return ["objective"]
    
    @property
    def output_keys(self) -> List[str]:
        return []

    async def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        objective = inputs['objective']
        chat_id = inputs['chat_id']
        platform = inputs['platform']
        client = inputs.get('client')
        base_url = inputs.get('base_url')

        first_task = {
            "task_id": 1,
            "task_name": YOUR_FIRST_TASK
        }
        self.add_task(first_task)

        self.task_id_counter = 1
        while True:
            if self.task_list:
                self.print_task_list()
                temp = ""
                for t in self.task_list:
                    tsk = str(t['task_id']) + ": " + t['task_name']
                    temp = temp + tsk + "\n"

                await self.send_message(chat_id, temp, platform, client, base_url)

                task = self.task_list.popleft()
                self.print_next_task(task)

                next_tsk = str(task['task_id']) + ": " + task['task_name']
                await self.send_message(chat_id, next_tsk, platform, client, base_url)

                result = await self.execution_chain.call({"objective": objective, "task_name": task["task_name"]})
                this_task_id = int(task["task_id"])
                self.print_task_result(result)

                await self.send_message(chat_id, result, platform, client, base_url)

                result_id = f"result_{task['task_id']}"
                self.vectorstore.add_texts(
                    texts=[result],
                    metadatas=[{"task": task["task_name"]}],
                    ids=[result_id],
                )

                if self.task_id_counter < 6:
                    new_tasks = get_next_task(
                        self.task_creation_chain, result, task["task_name"], [t["task_name"] for t in self.task_list], objective
                    )
                    for new_task in new_tasks:
                        self.task_id_counter += 1
                        new_task.update({"task_id": self.task_id_counter})
                        self.add_task(new_task)
                    self.task_list = deque(
                        prioritize_tasks(
                            self.task_prioritization_chain, this_task_id, list(self.task_list), objective
                        )
                    )

            if len(self.task_list) < 1:
                print("Tasks completed")
                await self.send_message(chat_id, "\n\nTask completed", platform, client, base_url)
                break
        return {}

  
    @classmethod
    def from_llm(
        cls,
        llm: BaseLLM,
        vectorstore: VectorStore,
        verbose: bool = False,
        **kwargs
    ) -> "BabyAGI":
        """Initialize the BabyAGI Controller."""
        task_creation_chain = TaskCreationChain.from_llm(
            llm, verbose=verbose
        )
        task_prioritization_chain = TaskPrioritizationChain.from_llm(
            llm, verbose=verbose
        )
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        tool_names = [tool.name for tool in tools]
        agent = ZeroShotAgent(llm_chain=llm_chain, allowed_tools=tool_names)
        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)
        return cls(
            task_creation_chain=task_creation_chain,
            task_prioritization_chain=task_prioritization_chain,
            execution_chain=agent_executor,
            vectorstore=vectorstore,
            **kwargs
        )

async def process_objective_with_babyagi(objective: str, chat_id: str, platform: str, client=None, base_url=None):
    llm = OpenAI(temperature=0)

    verbose = False
    max_iterations: Optional[int] = 2
    baby = BabyAGI.from_llm(
        llm=llm,
        vectorstore=vectorstore,
        verbose=verbose,
        max_iterations=max_iterations
    )

    await baby._call({
    "objective": objective,
    "chat_id": chat_id,
    "platform": platform,
    "client": client,
    "base_url": base_url
})
