import re
from typing import List, Dict

from graph_parse import openai_llm_parser

def chunk_resume_text(text: str, file_id: str) -> List[Dict]:
    """
    Split resume text into chunks by section headings (Experience, Education, Skills).
    Returns list of chunks with ids, section labels, and text.
    """
    sections = re.split(r"(?i)(?=experience|education|skills|projects|summary)", text)
    chunks = []
    
    for idx, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue
        
        # Label section by first word
        label = sec.split("\n", 1)[0].split()[0].capitalize()
        chunk_id = f"{file_id}-chunk-{idx+1}"
        
        chunks.append({
            "id": chunk_id,
            "section": label,
            "text": sec
        })
    
    return chunks

def extract_graph_from_resume(text: str, file_id: str):
    chunks = chunk_resume_text(text, file_id)
    all_relationships = []

    for chunk in chunks:
        prompt = f"""
        FILE_ID: {file_id}
        CHUNK_ID: {chunk['id']}
        SECTION: {chunk['section']}

        TEXT:
        {chunk['text']}
        """

        parsed = openai_llm_parser(prompt)

        # Attach provenance client-side
        for rel in parsed.graph:
            all_relationships.append({
                "node": rel.node,
                "target_node": rel.target_node,
                "relationship": rel.relationship,
                "chunk_id": chunk["id"],
                "file_id": file_id,
                "section": chunk["section"]
            })

    return all_relationships

def relationships_to_cypher(rels: List[Dict]) -> List[str]:
    """
    Convert extracted relationships into Cypher MERGE statements.
    """
    cypher_queries = []
    
    for rel in rels:
        node_a = rel["node"].replace('"', "'")
        node_b = rel["target_node"].replace('"', "'")
        r_type = rel["relationship"].upper().replace(" ", "_")

        # Example MERGE query
        query = f"""
        MERGE (a:Entity {{name: "{node_a}"}})
        MERGE (b:Entity {{name: "{node_b}"}})
        MERGE (a)-[r:{r_type}]->(b)
        SET r.chunk_id = "{rel['chunk_id']}", r.file_id = "{rel['file_id']}", r.section = "{rel['section']}"
        """
        cypher_queries.append(query.strip())
    
    return cypher_queries
