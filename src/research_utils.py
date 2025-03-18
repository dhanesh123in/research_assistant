import arxiv
import ollama
from typing import List, Dict, Optional
import re
from .error_utils import retry_with_backoff, ArxivError, OllamaError
import hashlib
import json
from pathlib import Path
import os
from datetime import datetime

# Cache directory
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

@retry_with_backoff(retries=3)
def fetch_arxiv_papers(query: str, max_results: int = 10) -> List[Dict]:
    """
    Fetch papers from ArXiv based on the query with retry mechanism
    """
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        for result in search.results():
            try:
                papers.append({
                    "title": result.title,
                    "abstract": result.summary,
                    "link": result.entry_id,
                    "authors": ", ".join(author.name for author in result.authors),
                    "published": result.published.strftime("%Y-%m-%d")
                })
            except Exception as e:
                # Log the error but continue with other papers
                print(f"Error processing paper: {str(e)}")
                continue
        
        if not papers:
            raise ArxivError(f"No papers found for query: {query}")
            
        return papers
    except Exception as e:
        raise ArxivError(f"Failed to fetch papers: {str(e)}")

@retry_with_backoff(retries=2)
def summarize_papers(papers: List[Dict], model: str = "deepseek-r1:14b") -> str:
    """
    Generate a summary of the papers using Ollama with retry mechanism
    """
    if not papers:
        raise ValueError("No papers provided for summarization")

    try:
        # Create a formatted text of papers for the model to summarize
        papers_text = ""
        for paper in papers:
            papers_text += f"\nTitle: {paper['title']}\nAuthors: {paper['authors']}\nAbstract: {paper['abstract']}\n---\n"
        
        prompt = f"""Please analyze these research papers and provide a comprehensive summary:
        
        {papers_text}
        
        Please structure your response with:
        1. Overall Theme/Trends
        2. Key Findings
        3. Research Implications
        
        Important: Provide your response directly without any <think> tags or internal thought process.
        """
        
        response = ollama.chat(model=model, messages=[
            {"role": "user", "content": prompt}
        ])
        
        # Safely get content from response
        content = response.get("message", {}).get("content", "")
        if not content:
            raise OllamaError("No content received from the model")
        
        # Clean up the content
        cleaned_content = content
        if '<think>' in cleaned_content:
            cleaned_content = re.sub(r'<think>.*?</think>', '', cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content.strip())
        
        return cleaned_content

    except Exception as e:
        raise OllamaError(f"Failed to generate summary: {str(e)}")

def format_paper_details(papers: List[Dict]) -> str:
    """
    Format paper details into a readable markdown string
    """
    try:
        if not papers:
            return "No papers available to display."
            
        formatted_text = "### 📑 Detailed Paper List\n\n"
        for i, paper in enumerate(papers, 1):
            try:
                formatted_text += f"**{i}. {paper['title']}**\n\n"
                formatted_text += f"**Authors:** {paper['authors']}\n\n"
                formatted_text += f"**Published:** {paper['published']}\n\n"
                formatted_text += f"**Abstract:** {paper['abstract']}\n\n"
                formatted_text += f"**Link:** [ArXiv]({paper['link']})\n\n"
                formatted_text += "---\n\n"
            except KeyError as e:
                formatted_text += f"*Error displaying paper {i}: Missing data ({str(e)})*\n\n"
                continue
            
        return formatted_text
    except Exception as e:
        return f"Error formatting paper details: {str(e)}"

def create_cache_key(topic: str, max_results: int, model: str) -> str:
    """Create a unique cache key for the research query"""
    data = f"{topic}-{max_results}-{model}"
    return hashlib.md5(data.encode()).hexdigest()

def get_cached_research(cache_key: str) -> Optional[Dict]:
    """Get cached research results from file"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_to_cache(cache_key: str, results: Dict) -> None:
    """Save research results to cache file"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        with open(cache_file, "w") as f:
            json.dump(results, f)
    except Exception as e:
        print(f"Failed to save to cache: {str(e)}")

def cache_research_results(cache_key: str, results: dict) -> None:
    """Cache research results"""
    save_to_cache(cache_key, results)

def cleanup_old_cache(max_age_days: int = 7) -> None:
    """Remove cache files older than max_age_days"""
    now = datetime.now()
    for cache_file in CACHE_DIR.glob("*.json"):
        file_age = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if (now - file_age).days > max_age_days:
            try:
                os.remove(cache_file)
            except Exception:
                continue 