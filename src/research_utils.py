import arxiv
import ollama
from typing import List, Dict, Optional
import re
from .error_utils import retry_with_backoff, ArxivError, OllamaError

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