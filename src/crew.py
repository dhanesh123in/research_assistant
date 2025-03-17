import os
from crewai import Agent, Task, Crew, Process
from tools import fetch_arxiv_papers, search_tool, summarize_text, generate_report
import yaml
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import Ollama
from typing import Dict, Any

# Load configurations
with open("src/config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Set these environment variables to work with Ollama
os.environ["OPENAI_API_KEY"] = config["OPENAI_API_KEY"]
os.environ["OPENAI_API_BASE"] = config["OPENAI_API_BASE"]
os.environ["OPENAI_API_MODEL"] = config["OPENAI_API_MODEL"]
os.environ["LITELLM_MODEL_PROVIDER"] = config["LITELLM_MODEL_PROVIDER"]

# Load configurations
with open("src/agents.yaml", "r") as file:
    agents_config = yaml.safe_load(file)

with open("src/tasks.yaml", "r") as file:
    tasks_config = yaml.safe_load(file)

# Configure Ollama with streaming
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

# Construct the full model path
full_model_path = f"{config['LITELLM_MODEL_PROVIDER']}/{config['OPENAI_API_MODEL']}"

llm = Ollama(
    model=full_model_path,
    callback_manager=callback_manager,
    temperature=config["temperature"],
    base_url=config["base_url"]
)

# Define Agents
arxiv_researcher = Agent(
    role=agents_config["arxiv_researcher"]["role"],
    goal=agents_config["arxiv_researcher"]["goal"],
    backstory=agents_config["arxiv_researcher"]["backstory"],
    tools=[fetch_arxiv_papers],
    llm=llm,
    allow_delegation=False,
    verbose=True,
    system_prompt=agents_config["arxiv_researcher"]["system_prompt"],
    cache=False
)

summarizer = Agent(
    role=agents_config["summarizer"]["role"],
    goal=agents_config["summarizer"]["goal"],
    backstory=agents_config["summarizer"]["backstory"],
    tools=[summarize_text],
    llm=llm,
    allow_delegation=False 
)

web_researcher = Agent(
    role=agents_config["web_researcher"]["role"],
    goal=agents_config["web_researcher"]["goal"],
    backstory=agents_config["web_researcher"]["backstory"],
    tools=[search_tool],
    llm=llm,
    allow_delegation=False 
)

report_generator = Agent(
    role=agents_config["report_generator"]["role"],
    goal=agents_config["report_generator"]["goal"],
    backstory=agents_config["report_generator"]["backstory"],
    tools=[generate_report],
    llm=llm,
    allow_delegation=False 
)

# Define Tasks
fetch_papers_task = Task(
    description=tasks_config["fetch_papers"]["description"],
    expected_output=tasks_config["fetch_papers"]["expected_output"],
    agent=arxiv_researcher
)

summarize_task = Task(
    description=tasks_config["summarize_papers"]["description"],
    expected_output=tasks_config["summarize_papers"]["expected_output"],
    agent=summarizer
)

find_sources_task = Task(
    description=tasks_config["find_related_sources"]["description"],
    expected_output=tasks_config["find_related_sources"]["expected_output"],
    agent=web_researcher
)

generate_report_task = Task(
    description=tasks_config["generate_report"]["description"],
    expected_output=tasks_config["generate_report"]["expected_output"],
    agent=report_generator
)

# def task_callback(task_output: Any) -> None:
#     # Assuming task_output has a property called 'output'
#     print(f"\n=== Task Output ===\n{task_output.raw}\n")
#     if not hasattr(task_callback, 'results'):
#         task_callback.results = []
#     task_callback.results.append(task_output.raw)  # Append the output directly

# Assemble Crew
research_crew = Crew(
    # agents=[arxiv_researcher, summarizer, web_researcher, report_generator],
    # tasks=[fetch_papers_task, summarize_task, find_sources_task, generate_report_task],
    # agents=[arxiv_researcher, summarizer],
    # tasks=[fetch_papers_task, summarize_task],
    agents=[arxiv_researcher],
    tasks=[fetch_papers_task],
    process=Process.sequential,
    # task_callback=task_callback
)

# task_callback.results = []

def run_research(topic):
    # Reset results for new research
    # task_callback.results = []
    
    # Run the crew
    research_crew.kickoff(inputs={'topic': topic})
    # Combine all results including intermediate steps
    # all_results = "\n\n=== Research Process ===\n"
    all_results = "===Summary\n"

    for task in research_crew.tasks:
        task_output = task.output
        if task_output:
            all_results += f"{task_output.raw}\n"
    
        agent = task.agent
        # all_results += "===Details\n"
        for result in agent.tools_results:
            all_results += result['result']

    # all_results += f"\n\n=== Final Result ===\n{final_result}" 
    return all_results
