# AI Research Assistant

This project uses Arxiv to obtain research papers based on a user's input and creates a summary using an LLM served through Ollama.

## Screenshot

![AI Research Assistant Interface](assets/app_screenshot.png)

The app features:
- 📝 Topic-based research paper search
- 🤖 AI-powered paper summarization
- 📚 Detailed paper listings with abstracts
- 📥 PDF report export
- 💾 Search history and caching
- ⚙️ Configurable paper count and AI model selection

## Getting Started

Ensure Ollama is installed and running. The code has been tested on Python 3.10.12

```
pip install requirements.txt #preferably in a virtual environment
streamlit run streamlit_simple_app.py
```

If the installation fails, following installion command should do it

```
pip install streamlit arxiv ollama markdown weasyprint
```


