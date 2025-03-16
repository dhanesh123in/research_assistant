from langchain_community.llms import Ollama
llm = Ollama(model="llama3.3")
print(llm.invoke("Hello, how are you?"))
