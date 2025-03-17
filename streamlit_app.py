import streamlit as st
import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.append(str(src_dir))

from crew import run_research

st.title("📚 AI Research Assistant")

topic = st.text_input("Enter research topic:", "")

if st.button("Run Research"):
    if topic:
        with st.spinner("Gathering information..."):
            result = run_research(topic)
            
        st.subheader(f"🔍 {topic}")
        # Split the results and display them in expandable sections
        sections = result.split("===")
        
        # Prepare content for PDF
        pdf_content = f"# Research on: {topic}\n\n"
        
        for section in sections:
            if section.strip():
                title = section.split("\n")[0].strip()
                content = "\n".join(section.split("\n")[1:]).strip()
                st.markdown(f"### 🔍 {title}")
                st.markdown(content)
                
                # Add to PDF content
                pdf_content += f"## {title}\n\n{content}\n\n"
        
        # Add PDF download button
        try:
            import markdown
            from weasyprint import HTML
            import base64
            from io import BytesIO
            import re
            
            def create_download_link(pdf_bytes, filename):
                b64 = base64.b64encode(pdf_bytes).decode()
                return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF</a>'
            
            def create_pdf(content):
                # Process content to ensure links are properly formatted
                # Convert plain URLs to markdown links
                url_pattern = r'(https?://[^\s]+)'
                def replace_with_md_link(match):
                    url = match.group(1)
                    return f'[{url}]({url})'
                
                processed_content = re.sub(url_pattern, replace_with_md_link, content)
                
                # Convert markdown to HTML with extensions for better list handling
                html = markdown.markdown(processed_content, extensions=['extra', 'smarty'])
                
                # Fix bullet lists - ensure ul elements have proper styling
                html = html.replace('<ul>', '<ul style="list-style-type: disc;">')
                
                # Add some basic styling with specific list styling
                styled_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1 {{ color: #1a5276; }}
                        h2 {{ color: #2874a6; }}
                        a {{ color: #2980b9; text-decoration: underline; }}
                        ul {{ list-style-type: disc !important; padding-left: 20px; }}
                        ol {{ list-style-type: decimal !important; padding-left: 20px; }}
                        li {{ margin-bottom: 5px; }}
                        li::marker {{ font-size: 1em; }}
                    </style>
                </head>
                <body>
                    {html}
                </body>
                </html>
                """
                
                # Convert HTML to PDF
                pdf_bytes = BytesIO()
                HTML(string=styled_html).write_pdf(
                    pdf_bytes,
                    presentational_hints=True
                )
                pdf_bytes.seek(0)
                return pdf_bytes.read()
            
            pdf_bytes = create_pdf(pdf_content)
            pdf_link = create_download_link(pdf_bytes, f"{topic}.pdf")
            st.markdown(pdf_link, unsafe_allow_html=True)
            
        except ImportError:
            st.warning("PDF export requires additional libraries. Install them with: pip install markdown weasyprint")
    else:
        st.warning("Please enter a topic to research.")
