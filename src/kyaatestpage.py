import os
import streamlit as st
from dotenv import load_dotenv
from docx import Document
import pdfplumber
import json
import sys
import asyncio
from pathlib import Path
from openai import OpenAI, AzureOpenAI
from ragas.llms import llm_factory


PROJECT_ROOT = Path(__file__).resolve().parent.parent 
sys.path.insert(0, str(PROJECT_ROOT))
from rag_eval.evals import run_evaluation_from_qa

#load environment variables and keys
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
#open ai initialization for the llm for creating the q/a pairs 
azure_endpoint = os.getenv("AZURE_ENDPOINT")
azure_api_key = os.getenv("OPEN_AI_AZURE_KEY")
deployment_name = "rag-pipeline-openai"

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=azure_endpoint,
    api_key=azure_api_key,
    azure_deployment="gpt-4o"
)

#open ai intialization for the llm to evaluate the q/a pairs
# Add the current directory to the path so we can import rag module when run as a script
sys.path.insert(0, str(Path(__file__).parent))
from rag import default_rag_client

openai_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=azure_endpoint,
    api_key=azure_api_key,
    azure_deployment="gpt-4o"
)

rag_client = default_rag_client(llm_client=openai_client)
llm = llm_factory("gpt-4o", client=openai_client)

#function that sends prompt to llm to create the q/a pairs 
#prompt parameter can be used to customize the behavior of the llm and the returned q/a pairs
def openai_qa_parser(text: str, prompt = '') -> dict:
    """
    Generate Q/A pairs from the input text using OpenAI.
    Returns a dict like:
    {
        "qa_pairs": [
            {"question": "...", "answer": "..."},
            ...
        ]
    }
    """
    completion = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": 
                    f"""You are an AI that generates 10 total clear question/answer pairs 
                    based on the given text. Keep these q/a pairs informative and relevant and in order.
                    {prompt}
                    For each meaningful piece of information 
                    in the text, create one question and its answer. 
                    Format the output as a JSON object exactly like this:
                    {{
                        "qa_pairs": [
                            {{"question": "Sample question", "answer": "Sample answer"}},
                            ...more pairs...
                        ]
                    }}"""
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )
    
    return completion.choices[0].message.content

#function to extract text from different file types
#this is to get the text information of the file passed and send this to the llm for q/a pair generation
def extract_text(file_path):
    """Extract text from TXT, PDF, or DOCX files."""
    if file_path.endswith(".txt"):
        return open(file_path, "r", encoding="utf-8").read()
    elif file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

#function to save the uploaded document and update the document index
DOC_INDEX_FILE = "./data/document_index.json"
def save_uploaded_document(file):
    """Save the file and update the document index."""
    os.makedirs("./data", exist_ok=True)
    file_path = os.path.join("./data", file.name)

    # Save the file
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())

    # Load or initialize document index
    if os.path.exists(DOC_INDEX_FILE):
        with open(DOC_INDEX_FILE, "r", encoding="utf-8") as f:
            doc_index = json.load(f)
    else:
        doc_index = {}

    with open(DOC_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(doc_index, f, indent=2)

    return file_path

#function to output the q/a pairs in the streamlit app
#designed to ouput the document and its corresponding q/a pairs in a readable format
def output_qa_pairs(qa_results):
    for doc in qa_results:
        st.markdown(f"### Document: {doc['document_name']}")
        try:
            qa_data = json.loads(doc['qa_pairs'])
            for i, pair in enumerate(qa_data.get("qa_pairs", []), 1):
                st.markdown(f"**Q{i}:** {pair['question']}")
                st.markdown(f"**A{i}:** {pair['answer']}")
                st.markdown("---")
        except Exception as e:
            st.warning(f"Failed to parse Q/A for document {doc['document_name']}: {e}")

def main():
    st.set_page_config(layout="wide")
    st.title("RAG Evaluation Script")

    # ---------------- Session State ----------------
    if "qa_results" not in st.session_state:
        st.session_state.qa_results = []
    if "eval_results" not in st.session_state:
        st.session_state.eval_results = None

    # ---------------- Sidebar: Upload & Prompt ----------------
    st.sidebar.subheader("Upload Documents for Q/A Pairs")
    uploaded_files = st.sidebar.file_uploader(
        'Upload a File', accept_multiple_files=True
    )

    qa_type_prompt = st.sidebar.selectbox(
        "Select Q/A Type",
        ["Default","Factoid", "Multiple Choice", "True/False", "Custom"]
    )

    if qa_type_prompt == "Custom":
        qa_type_prompt_text = st.sidebar.text_area(
            "Enter Custom Q/A Prompt",
            value="Generate Q/A pairs based on the content",
            height=150
        )
    else:
        qa_type_prompt_text = f"Generate {qa_type_prompt} Q/A pairs from the content."

    if st.sidebar.button("Upload and Generate Q/A"):
        if not uploaded_files:
            st.sidebar.warning("No files selected")
        else:
            upload_dir = './data'
            os.makedirs(upload_dir, exist_ok=True)
            st.session_state.qa_results = []

            for file in uploaded_files:
                file_path = save_uploaded_document(file)
                with open(file_path, 'wb') as f:
                    f.write(file.getbuffer())

                with st.spinner(f"Extracting text from {file.name}..."):
                    text = extract_text(file_path)

                if not text.strip():
                    st.warning(f"No text found in {file.name}")
                    continue

                with st.spinner(f"Generating Q/A pairs for {file.name}..."):
                    qa_json = openai_qa_parser(text, prompt=qa_type_prompt_text)

                st.session_state.qa_results.append({
                    "document_name": file.name,
                    "qa_type": qa_type_prompt,  # Store type for display
                    "qa_pairs": qa_json,
                    "text": text
                })

            st.success("Q/A generation completed!")

    # ---------------- Main Area: Display Q/A Pairs ----------------
    st.subheader("Q/A Pairs from Uploaded Documents")
    if st.session_state.qa_results:
        for doc in st.session_state.qa_results:
            st.markdown(f"### {doc['document_name']} ({doc['qa_type']} Q/A)")
            output_qa_pairs([doc])
    else:
        st.info("Upload documents to see Q/A pairs here.")

    # ---------------- Evaluation ----------------
    if st.button('Run Evaluation'):
        if not st.session_state.qa_results:
            st.warning("No Q/A pairs to evaluate")
        else:
            with st.spinner("Running Evaluation..."):
                uploaded_texts = [doc["text"] for doc in st.session_state.qa_results if doc.get("text")]
                rag_client.set_documents(uploaded_texts)

                st.session_state.eval_results = asyncio.run(
                    run_evaluation_from_qa(st.session_state.qa_results, documents=uploaded_texts)
                )
            st.success("Evaluation completed!")

    # ---------------- Display Evaluation Table ----------------
    if st.session_state.eval_results is not None:
        st.subheader("Evaluation Results")
        st.dataframe(st.session_state.eval_results, use_container_width=True)


if __name__ == "__main__":
    main()