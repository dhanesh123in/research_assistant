import streamlit as st
import sys
from pathlib import Path
import base64
from io import BytesIO
import markdown
from weasyprint import HTML
from src.error_utils import ArxivError, OllamaError, ResearchError

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.append(str(src_dir))

from src.research_utils import fetch_arxiv_papers, summarize_papers, format_paper_details

st.set_page_config(page_title="📚 Research Assistant", layout="wide")
st.title("📚 AI Research Assistant")

# Sidebar configurations
with st.sidebar:
    st.header("⚙️ Settings")
    max_papers = st.slider("Maximum number of papers", 5, 20, 10)
    model = st.selectbox(
        "Select AI Model",
        ["deepseek-r1:14b", "llama2", "mistral"],
        index=0
    )

# Main interface
topic = st.text_input("Enter research topic:", "")

if st.button("Run Research"):
    if topic:
        try:
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

                # Display results
                st.header("📊 Research Results")
                
                # Summary section
                st.subheader("🔍 Summary")
                st.markdown(summary)
                
                # Detailed papers section
                with st.expander("📑 View Detailed Paper List"):
                    st.markdown(paper_details)

                # Prepare PDF export
                def create_pdf_content():
                    content = f"# Research Results: {topic}\n\n"
                    content += "## Summary\n\n"
                    content += summary + "\n\n"
                    content += "## Detailed Papers\n\n"
                    content += paper_details
                    return content

                def create_download_link(pdf_bytes, filename):
                    b64 = base64.b64encode(pdf_bytes).decode()
                    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="button">📥 Download PDF Report</a>'

                def create_pdf(content):
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
                    return pdf_bytes.read()

                # PDF export with error handling
                try:
                    pdf_content = create_pdf_content()
                    pdf_bytes = create_pdf(pdf_content)
                    st.markdown(
                        create_download_link(pdf_bytes, f"research_{topic.replace(' ', '_')}.pdf"),
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.warning("⚠️ PDF export failed. You can still view the results above.")
                    st.error(f"PDF Error: {str(e)}")

        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            st.warning("Please try again with a different topic or contact support if the issue persists.")
    else:
        st.warning("⚠️ Please enter a topic to research.")

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