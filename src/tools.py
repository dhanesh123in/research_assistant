import arxiv
from crewai_tools import SerperDevTool
from crewai.tools import tool
import yaml
import ollama

# Load configurations
with open("src/config.yaml", "r") as file:
    config = yaml.safe_load(file)

@tool
def fetch_arxiv_papers(query: str) -> str:
    """Fetches the top 5 relevant research papers from Arxiv based on a query."""
    search = arxiv.Search(
        query=query,
        max_results=10,
        sort_by=arxiv.SortCriterion.Relevance
    )
    papers = []
    for result in search.results():
        papers.append(f"=== {result.title}\nAbstract: {result.summary}\nLink: {result.entry_id}\n")
    return "\n".join(papers) if papers else "No relevant papers found."

# Web search tool using Google Search API
search_tool = SerperDevTool()

@tool
def summarize_text(text: str) -> str:
    """Summarizes a given text using Ollama's model."""
    response = ollama.chat(model=config["OPENAI_API_MODEL"], messages=[{"role": "user", "content": f"Summarize this: {text}"}])
    return response["message"]["content"]

@tool
def generate_report(summary: str, additional_sources: str) -> str:
    """Generates a structured research report based on the summary and additional sources."""
    prompt = f"Write a well-structured research report based on this summary: {summary}\nAdditional sources: {additional_sources}"
    response = ollama.chat(model=config["OPENAI_API_MODEL"], messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]
