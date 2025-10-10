from dotenv import load_dotenv
import os
import re
from openai import OpenAI 

import streamlit as st
 
from langchain.document_loaders import ConfluenceLoader

load_dotenv()

loader = ConfluenceLoader(
    url="https://wiki.ith.intel.com",
    username="kyaa.goggins@intel.com",
    api_key=os.getenv("CONFLUENCE_API_KEY")
)

def main():
    st.set_page_config(layout="wide")
    st.title("Test Confluence")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Confluence Info Return")
        
        if st.button('Get Page'):
            docs = loader.load(space_key="CASEAMR", limit=25)
            st.write(f"Loaded {len(docs)} pages.")
            st.write(docs[0].page_content[:500])
        

if __name__ == "__main__":
    main()