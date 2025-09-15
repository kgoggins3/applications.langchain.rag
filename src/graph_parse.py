from pydantic import BaseModel
from openai import OpenAI 
from dotenv import load_dotenv
import os

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_key)
#ingest data 

#pydantic models 
#output parser class structure to struture the LLM result into graph components
class single(BaseModel): 
    node: str
    target_node: str
    relationship: str

class GraphComponents(BaseModel):
    graph: list[single]

# class CustomLLMParser:
#     def __init__(self, llm):
#         self.llm = llm

#     def parse(self, prompt: str) -> GraphComponents:
#         # Send prompt to your custom LLM
#         raw_output = self.llm.predict(prompt)
        
#         # Parse JSON string into Pydantic objects
#         return GraphComponents.model_validate_json(raw_output)

def openai_llm_parser(prompt: str) -> GraphComponents:
    completion = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": 
                   
                """ You are a precise graph relationship extractor. Extract all 
                    relationships from the text and format them as a JSON object 
                    with this exact structure:
                    {
                        "graph": [
                            {"node": "Person/Entity", 
                             "target_node": "Related Entity", 
                             "relationship": "Type of Relationship"},
                            ...more relationships...
                        ]
                    }
                    Include ALL relationships mentioned in the text, including 
                    implicit ones. Be thorough and precise. """
                    
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return GraphComponents.model_validate_json(completion.choices[0].message.content)