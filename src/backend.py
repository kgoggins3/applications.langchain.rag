from dotenv import load_dotenv
import os

import streamlit as st


# Load environment variables
load_dotenv()

# Neo4j
from neo4j import GraphDatabase

neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

#initialize neo4j database
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def test_neo4j():
    with driver.session() as session:
        result = session.run("RETURN 'Hello Neo4j!' AS message")
        for record in result:
            print(record["message"])

# Qdrant
from qdrant_client import QdrantClient

qdrant_client = QdrantClient(host="localhost", port=6333)

def test_qdrant():
    # Check if Qdrant is alive
    info = qdrant_client.get_collections()
    print("Qdrant collections:", info)

# LangChain placeholder
from langchain.schema import HumanMessage, SystemMessage

def test_langchain():
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Hello LangChain!")
    ]
    for msg in messages:
        print(f"{msg.type}: {msg.content}")

# from langchain_community.document_loaders import PyPDFLoader
# from PyPDF2 import PdfReader

from PyPDF2 import PdfReader
#also need function to load documents from stored file path
def load_documents(folder_path="documents"):
    docs = []
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Handle .txt files
        if filename.lower().endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                docs.append({"filename": filename, "text": text})

        # Handle .pdf files
        elif filename.lower().endswith(".pdf"):
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""  # Extract each page safely
            docs.append({"filename": filename, "text": text})

    return docs


def main():
    st.set_page_config(layout="wide")
    st.title("Test GPT")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Upload Documents")

        uploaded_file = st.file_uploader("Upload your document:")

        if uploaded_file is not None:
            file_path = os.path.join("documents", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            st.success(f"Saved {uploaded_file.name}!")

        docs = load_documents("documents")
        st.write(docs)



# Run tests
if __name__ == "__main__":
    print("Testing Neo4j connection...")
    test_neo4j()
    
    print("\nTesting Qdrant connection...")
    test_qdrant()
    
    print("\nTesting LangChain setup...")
    test_langchain()

    main()


# ingest data 

# output parser class structure to struture the LLM result into graph components
# class single(BaseModel): 
#     node: str
#     target_node: str
#     relationship: str

# class GraphComponents(BaseModel):
#     graph: list[single]


#qdrant collection for data storage
# qdrant_client.recreate_collection(
#         collection_name=documents,
#         vectors_config=VectorParams(size=384, distance=Distance.DOT),
#     )

#next steps is to create the output parser, which is an llm that retrieves text docs and 
# converts it into the graph structure 



#then , once the llm formats it, it needs to be stored in the databases 


        # Display chat history
        # if st.session_state.chat_history:
        #     st.markdown("### Conversation History")
        #     for entry in st.session_state.chat_history:
        #         st.markdown(f"**User:** {entry['query']}")
        #         st.markdown(f"**Assistant:** {entry['answer']}")
        #         st.markdown("---")
        # # Input for new query
        # query = st.text_input("Enter your question", "")
        # if st.button("Get Answer") and query:
        #     # chatgpt llm initialize 
        #     llm = LangChainCustom(
        #         client_id=st.session_state.client_id,
        #         client_secret=st.session_state.client_secret,
        #         model=st.session_state.model_name,
        #         temperature=st.session_state.temperature,
        #         system_prompt=st.session_state.system_message
        #     )
        #     # Build prompt template from custom prompt
        #     prompt_template = PromptTemplate.from_template(st.session_state.custom_prompt)
        #     # Create conversational chain with current settings
        #     qa_chain = create_conversational_chain(
        #         st.session_state.vectorstore,
        #         llm,
        #         prompt_template,
        #         st.session_state.memory,
        #         st.session_state.k_value
        #     )
        #     result = qa_chain({"question": query})
        #     answer = result.get("answer", "No answer returned.")
        #     source_docs = result.get("source_documents", [])
        #     # Append current turn to chat history
        #     st.session_state.chat_history.append({"query": query, "answer": answer})
        #     # Display answer and sources
        #     st.markdown("## Answer:")
        #     st.write(answer)
        #     st.markdown("### Sources Used:")

