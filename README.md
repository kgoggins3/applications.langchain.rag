# applications.langchain.rag
This application is a Retrieval-Augmented Generation (RAG) chatbot built with LangChain. It consists of a GraphRAG approach to the storing of data, consisting of Neo4j for the graph database and Qdrant for the vector database. This README will guide you through swtting up your environment, installing dependencies, running Qdrant, and launching the app. 

---

## Features

# GraphRAG
Builds knowledge graphs to capture entities and their relationships. This allows for the ability to answer complex queries, as there is a deeper understanding of context.
**Vector Database:** Uses Qdrant to persist and store unique IDs, relationships, and embeddings, for similarity-based retrieval. 
**Graph Database:** Uses Neo4j to create the graph structure and relationships of the retrieved data. 

# LangChain

# LangSmith
Tracks and traces the LangChain functions to follow the output and performance. 

# RAGAS
Anotehr layer of evaluation of the performance of the RAG model. 
