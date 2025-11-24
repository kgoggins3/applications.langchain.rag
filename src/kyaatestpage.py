import os
import streamlit as st
from dotenv import load_dotenv
from docx import Document
import pdfplumber
import json
# from langchain_sdk.Langchain_sdk import LangChainCustom, LangChainCustomEmbeddings
from openai import OpenAI, AzureOpenAI
# from langchain.chat_models import ChatOpenAI

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

azure_endpoint = os.getenv("AZURE_ENDPOINT")
azure_api_key = os.getenv("OPEN_AI_AZURE_KEY")
deployment_name = "rag-pipeline-openai"

client = OpenAI(api_key=openai_key)

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=azure_endpoint,
    api_key=azure_api_key,
    azure_deployment="gpt-4o"
)

def openai_qa_parser(text: str) -> dict:
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
                    """You are an AI that generates clear question/answer pairs 
                    based on the given text. For each meaningful piece of information 
                    in the text, create one question and its answer. 
                    Format the output as a JSON object exactly like this:
                    {
                        "qa_pairs": [
                            {"question": "Sample question", "answer": "Sample answer"},
                            ...more pairs...
                        ]
                    }"""
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )
    
    return completion.choices[0].message.content

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

def main():
    st.set_page_config(layout="wide")
    st.title("CASE GPT - Test")

    st.subheader("Upload Docs for Q/A Pairs")
    uploaded_files = st.file_uploader('Upload a File', accept_multiple_files=True)

    if st.button("Enter"):
        if not uploaded_files:
            st.warning("No files selected")
            return

        upload_dir = './data'
        os.makedirs(upload_dir, exist_ok=True)
        qa_results = []

        for file in uploaded_files:
            file_path = os.path.join(upload_dir, file.name)
            with open(file_path, 'wb') as f:
                f.write(file.getbuffer())

            text = extract_text(file_path)
            if not text.strip():
                continue

            qa_json = openai_qa_parser(text)
            qa_results.append({
                "document_name": file.name,
                "qa_pairs": qa_json  
            })

        # Display all Q/A pairs
        for doc in qa_results:
            st.markdown(f"### Document: {doc['document_name']}")
            try:
                qa_data = json.loads(doc['qa_pairs'])
                for i, pair in enumerate(qa_data.get("qa_pairs", []), 1):
                    st.markdown(f"**Q{i}:** {pair['question']}")
                    st.markdown(f"**A{i}:** {pair['answer']}")
                    st.markdown("---")
            except json.JSONDecodeError:
                st.warning(f"Failed to parse Q/A for document {doc['document_name']}")

if __name__ == "__main__":
    main()