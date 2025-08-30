from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Neo4j
from neo4j import GraphDatabase

neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

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

# Run tests
if __name__ == "__main__":
    print("Testing Neo4j connection...")
    test_neo4j()
    
    print("\nTesting Qdrant connection...")
    test_qdrant()
    
    print("\nTesting LangChain setup...")
    test_langchain()
