from crew import run_research
from crewai import Agent
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import Ollama

# Configure Ollama with streaming
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
import yaml

# Load parameters from a YAML file
with open("src/config.yaml", "r") as file:
    config = yaml.safe_load(file)

full_model_path = f"{config['LITELLM_MODEL_PROVIDER']}/{config['OPENAI_API_MODEL']}"

llm = Ollama(
    model=full_model_path,
    callback_manager=callback_manager,
    temperature=config['temperature'],
    base_url=config['base_url']
)

if __name__ == "__main__":
    # Set the default LLM for all agents
    Agent.llm = llm
    
    topic = input("Enter a research topic: ")
    print("Running research... This may take a while.\n")
    result = run_research(topic)
    print("\n=== Research Summary ===\n")
    print(result)
