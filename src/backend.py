from dotenv import load_dotenv
import os

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

# Run tests
if __name__ == "__main__":
    print("Testing Neo4j connection...")
    test_neo4j()
    
    print("\nTesting Qdrant connection...")
    test_qdrant()
    
    print("\nTesting LangChain setup...")
    test_langchain()

# ingest data 

# output parser class structure to struture the LLM result into graph components
class single(BaseModel): 
    node: str
    target_node: str
    relationship: str

class GraphComponents(BaseModel):
    graph: list[single]

# chatgpt llm initialize 
llm = LangChainCustom(
    client_id=st.session_state.client_id,
    client_secret=st.session_state.client_secret,
    model=st.session_state.model_name,
    temperature=st.session_state.temperature,
    system_prompt=st.session_state.system_message
)

#next steps is to create the output parser, which is an llm that retrieves text docs and 
# converts it into the graph structure 

#also need function to load documents 

#then , once the llm formats it, it needs to be stored in the databases 

