"""Streamlit UI for crawling and displaying wiki and SharePoint content."""
import streamlit as st
from typing import Dict, List, Optional
import os
from crawlers.wiki_crawler import crawl_wiki
from crawlers.sharepoint_crawler import SharePointCrawler
import requests
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Document Crawler",
    page_icon="📄",
    layout="wide"
)

# Sidebar for auth settings
with st.sidebar:
    st.header("Authentication")
    
    # Wiki auth
    st.subheader("Wiki Authentication")
    wiki_cookie = st.text_input("Cookie (if needed)", key="wiki_cookie")
    
    # SharePoint auth
    st.subheader("SharePoint Authentication")
    tenant_id = st.text_input("Tenant ID", key="tenant_id")
    client_id = st.text_input("Client ID", key="client_id")
    auth_type = st.radio(
        "Authentication Type",
        ["App-only", "Delegated"],
        key="auth_type"
    )
    
    if auth_type == "App-only":
        client_secret = st.text_input("Client Secret", type="password")
    else:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

# Main content
st.title("Document Crawler")

# Tabs for different crawlers
tab1, tab2 = st.tabs(["Wiki Crawler", "SharePoint Crawler"])

# Wiki Crawler Tab
with tab1:
    st.header("Wiki Crawler")
    
    wiki_url = st.text_input("Wiki Root URL", "https://wiki.example.com/page")
    wiki_depth = st.number_input("Max Depth", min_value=0, max_value=5, value=1)
    wiki_max = st.number_input("Max Pages", min_value=1, max_value=1000, value=100)
    
    if st.button("Crawl Wiki"):
        with st.spinner("Crawling wiki pages..."):
            try:
                session = requests.Session()
                if wiki_cookie:
                    session.headers.update({"Cookie": wiki_cookie})
                    
                results = crawl_wiki(
                    wiki_url,
                    session=session,
                    max_depth=wiki_depth,
                    max_pages=wiki_max
                )
                
                st.session_state["wiki_results"] = results
                st.success(f"Found {len(results)} pages")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Display wiki results
    if "wiki_results" in st.session_state:
        for i, doc in enumerate(st.session_state["wiki_results"]):
            with st.expander(f"{doc['title']} ({doc['status']})"):
                st.write("URL:", doc["url"])
                
                if doc["status"] == "ok":
                    st.subheader("Headings")
                    for h in doc["headings"]:
                        st.write(f"{'#' * h['level']} {h['text']}")
                        
                    if doc.get("metadata"):
                        st.subheader("Metadata")
                        for k, v in doc["metadata"].items():
                            st.write(f"- {k}: {v}")
                    
                    st.subheader("Preview")
                    if st.button("Load Content", key=f"wiki_{i}"):
                        with st.spinner("Loading page content..."):
                            try:
                                resp = session.get(doc["url"])
                                if resp.ok:
                                    st.markdown(resp.text, unsafe_allow_html=True)
                                else:
                                    st.error(f"Failed to load: HTTP {resp.status_code}")
                            except Exception as e:
                                st.error(f"Error loading content: {str(e)}")
                else:
                    st.warning(doc["snippet"])

# SharePoint Crawler Tab
with tab2:
    st.header("SharePoint Crawler")
    
    site_id = st.text_input("SharePoint Site ID")
    library_id = st.text_input("Document Library ID")
    sp_max = st.number_input("Max Items", min_value=1, max_value=5000, value=1000)
    
    if st.button("Crawl SharePoint"):
        if not (tenant_id and client_id and (
            (auth_type == "App-only" and client_secret) or
            (auth_type == "Delegated" and username and password)
        )):
            st.error("Please provide all required authentication details")
        else:
            with st.spinner("Crawling SharePoint documents..."):
                try:
                    crawler = SharePointCrawler(
                        tenant_id=tenant_id,
                        client_id=client_id,
                        client_secret=client_secret if auth_type == "App-only" else None,
                        username=username if auth_type == "Delegated" else None,
                        password=password if auth_type == "Delegated" else None
                    )
                    
                    results = crawler.crawl_library(
                        site_id=site_id,
                        library_id=library_id,
                        max_items=sp_max
                    )
                    
                    st.session_state["sp_results"] = results
                    st.success(f"Found {len(results)} documents")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Display SharePoint results
    if "sp_results" in st.session_state:
        # Add search/filter
        search = st.text_input("Search documents")
        
        # Column configuration
        cols = st.columns([3, 2, 2, 2, 1])
        cols[0].write("**Name**")
        cols[1].write("**Modified**")
        cols[2].write("**Modified By**")
        cols[3].write("**Type**")
        cols[4].write("**Size**")
        
        for doc in st.session_state["sp_results"]:
            # Simple search filter
            if search and search.lower() not in doc["name"].lower():
                continue
                
            with st.expander(doc["name"]):
                cols = st.columns([3, 2, 2, 2, 1])
                cols[0].write(doc["name"])
                cols[1].write(datetime.fromisoformat(doc["modified"].replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M"))
                cols[2].write(doc["modified_by"] or "Unknown")
                cols[3].write(doc["file_type"] or "Unknown")
                cols[4].write(f"{doc['size']/1024:.1f} KB")
                
                st.write("**URL:**", doc["web_url"])
                
                # Additional metadata
                with st.expander("Full Metadata"):
                    st.json(doc)