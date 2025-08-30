from qdrant_client.models import Distance, VectorParams
from neo4j import GraphDatabase
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
from collections import defaultdict
from neo4j_graphrag.retrievers import QdrantNeo4jRetriever
import uuid
import os

load_dotenv()

client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="test_collection",
    vectors_config=VectorParams(size=4, distance=Distance.DOT),
)

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test"))

with driver.session() as session:
    result = session.run("RETURN 'Neo4j connection successful!' AS msg")
    print(result.single()["msg"])
