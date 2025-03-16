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
            
        st.subheader("🔍 Research Findings")
        # Split the results and display them in expandable sections
        sections = result.split("===")
        for section in sections:
            if section.strip():
                title = section.split("\n")[0].strip()
                content = "\n".join(section.split("\n")[1:]).strip()
                with st.expander(f"🔍 {title}", expanded=True):
                    st.markdown(content)
    else:
        st.warning("Please enter a topic to research.")
