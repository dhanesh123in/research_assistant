import streamlit as st
import sys
from pathlib import Path
import base64
from io import BytesIO
import markdown
from weasyprint import HTML
from src.error_utils import ArxivError, OllamaError
import json
from datetime import datetime
import os

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.append(str(src_dir))

from src.research_utils import (
    fetch_arxiv_papers, summarize_papers, format_paper_details,
    create_cache_key, get_cached_research, save_to_cache, CACHE_DIR, cleanup_old_cache
)

# Initialize session state for history, topic, and results
if 'research_history' not in st.session_state:
    st.session_state.research_history = []
if 'topic' not in st.session_state:
    st.session_state.topic = ""
if 'last_results' not in st.session_state:
    st.session_state.last_results = None
if 'force_update' not in st.session_state:
    st.session_state.force_update = False

# Function to load history from file
def load_history():
    history_file = Path("research_history.json")
    if history_file.exists():
        with open(history_file, "r") as f:
            return json.load(f)
    return []

# Function to save history to file
def save_history(history):
    with open("research_history.json", "w") as f:
        json.dump(history, f)

# Function to display research results
def display_research_results(topic: str, summary: str, paper_details: str):
    """Display research results in a consistent format"""
    st.header("📊 Research Results")
    
    # Summary section
    st.subheader("🔍 Summary")
    st.markdown(summary)
    
    # Detailed papers section
    with st.expander("📑 View Detailed Paper List"):
        st.markdown(paper_details)

# Load existing history at startup
if not st.session_state.research_history:
    st.session_state.research_history = load_history()

st.set_page_config(page_title="📚 Research Assistant", layout="wide")

# Sidebar content
with st.sidebar:
    st.header("⚙️ Settings")
    max_papers = st.slider("Maximum number of papers", 5, 20, 10)
    model = st.selectbox(
        "Select AI Model",
        ["deepseek-r1:14b", "llama2", "mistral"],
        index=0
    )
    
    # History section
    st.header("📜 Research History")
    
    # Clear history button in its own container
    with st.container():
        if st.button("🗑️ Clear History"):
            st.session_state.research_history = []
            save_history([])
            st.success("History cleared!")
            st.rerun()
    
    # Display history with timestamps in a scrollable container
    with st.container():
        for item in st.session_state.research_history:
            with st.expander(f"🔍 {item['topic']}", expanded=False):
                st.write(f"📅 {item['timestamp']}")
                st.write(f"📚 Papers: {item['max_papers']}")
                st.write(f"🤖 Model: {item['model']}")
                if st.button("Load Results", key=f"load_{item['timestamp']}_{item['topic']}"):
                    cache_key = create_cache_key(item['topic'], item['max_papers'], item['model'])
                    cached_results = get_cached_research(cache_key)
                    if cached_results:
                        # Update last_results with cached data and include PDF-related info
                        st.session_state.last_results = {
                            'topic': item['topic'],
                            'papers': cached_results['papers'],
                            'summary': cached_results['summary'],
                            'paper_details': cached_results['paper_details'],
                            'show_pdf': True  # Flag to show PDF download
                        }
                        # Update the input field
                        st.session_state.topic = item['topic']
                        st.rerun()  # Needed to update the UI properly
                    else:
                        st.error("Cache not found. Please run the research again.")

    # Add cache cleanup section
    st.header("🗑️ Cache Management")
    if st.button("Clear Cache"):
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                os.remove(cache_file)
            except Exception:
                continue
        st.success("Cache cleared!")

# Add this new function near the top with other function definitions
def display_results_and_pdf(topic: str, summary: str, paper_details: str):
    """Display research results and PDF download button"""
    # Display results
    display_research_results(topic, summary, paper_details)

    # Add PDF download button
    try:
        # Create PDF content
        content = f"# Research Results: {topic}\n\n"
        content += "## Summary\n\n"
        content += summary + "\n\n"
        content += "## Detailed Papers\n\n"
        content += paper_details

        # Generate PDF
        html = markdown.markdown(content, extensions=['extra'])
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #1a5276; }}
                h2 {{ color: #2874a6; }}
                h3 {{ color: #2980b9; }}
                a {{ color: #2980b9; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        pdf_bytes = BytesIO()
        HTML(string=styled_html).write_pdf(pdf_bytes)
        pdf_bytes.seek(0)
        
        # Create download link
        b64 = base64.b64encode(pdf_bytes.read()).decode()
        download_link = f'<a href="data:application/pdf;base64,{b64}" download="research_{topic.replace(" ", "_")}.pdf" class="button">📥 Download PDF Report</a>'
        st.markdown(download_link, unsafe_allow_html=True)
    except Exception as e:
        st.warning("⚠️ PDF export failed. You can still view the results above.")
        st.error(f"PDF Error: {str(e)}")

# Main content
st.title("📚 AI Research Assistant")

# Create two main sections: Input and Results
input_section, results_section = st.container(), st.container()

with input_section:
    # Main interface
    topic = st.text_input("Enter research topic:", key="topic")
    run_button = st.button("Run Research", key="run_research")

with results_section:
    if run_button and topic:
        try:
            # Check cache first
            cache_key = create_cache_key(topic, max_papers, model)
            cached_results = get_cached_research(cache_key)
            
            if cached_results:
                st.success("📎 Retrieved from cache!")
                papers = cached_results['papers']
                summary = cached_results['summary']
                paper_details = cached_results['paper_details']
            else:
                # Create columns for progress
                col1, col2, col3 = st.columns(3)
                
                # Fetch papers with error handling
                with col1:
                    with st.status("🔍 Fetching papers...") as status:
                        try:
                            papers = fetch_arxiv_papers(topic, max_papers)
                            status.update(label="✅ Papers fetched!", state="complete")
                        except ArxivError as e:
                            status.update(label="❌ Failed to fetch papers", state="error")
                            st.error(f"ArXiv Error: {str(e)}")
                            papers = []
                
                if papers:
                    # Generate summary with error handling
                    with col2:
                        with st.status("🤖 Generating summary...") as status:
                            try:
                                summary = summarize_papers(papers, model)
                                status.update(label="✅ Summary generated!", state="complete")
                            except OllamaError as e:
                                status.update(label="❌ Failed to generate summary", state="error")
                                st.error(f"Ollama Error: {str(e)}")
                                summary = "Failed to generate summary. Please try again."

                    # Format results with error handling
                    with col3:
                        with st.status("📝 Formatting results...") as status:
                            try:
                                paper_details = format_paper_details(papers)
                                status.update(label="✅ Formatting complete!", state="complete")
                            except Exception as e:
                                status.update(label="❌ Failed to format results", state="error")
                                st.error(f"Formatting Error: {str(e)}")
                                paper_details = "Failed to format paper details."

                    # Cache the results
                    cached_results = {
                        'papers': papers,
                        'summary': summary,
                        'paper_details': paper_details,
                        'timestamp': datetime.now().isoformat()
                    }
                    save_to_cache(cache_key, cached_results)

            # Store results in session state
            st.session_state.last_results = {
                'topic': topic,
                'papers': papers,
                'summary': summary,
                'paper_details': paper_details,
                'show_pdf': True
            }

            # Add to history immediately
            history_item = {
                'topic': topic,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'max_papers': max_papers,
                'model': model
            }
            
            # Update history without rerun
            if topic not in [item['topic'] for item in st.session_state.research_history]:
                st.session_state.research_history.insert(0, history_item)
                st.session_state.research_history = st.session_state.research_history[:20]
                save_history(st.session_state.research_history)

            st.rerun()
            # Display results and PDF
            #display_results_and_pdf(topic, summary, paper_details)

        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            st.warning("Please try again with a different topic or contact support if the issue persists.")
    
    # Display previous results if they exist
    elif st.session_state.last_results:
        display_results_and_pdf(
            st.session_state.last_results['topic'],
            st.session_state.last_results['summary'],
            st.session_state.last_results['paper_details']
        )

# Add some CSS to style the download button
st.markdown("""
<style>
.button {
    display: inline-block;
    padding: 0.5em 1em;
    background-color: #2980b9;
    color: white !important;
    text-decoration: none;
    border-radius: 4px;
    margin-top: 1em;
}
.button:hover {
    background-color: #2874a6;
}
</style>
""", unsafe_allow_html=True) 