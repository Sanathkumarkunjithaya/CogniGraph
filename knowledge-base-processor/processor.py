import os
import time
import glob
import json
import string # Import the string library for punctuation
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

load_dotenv() 

from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_neo4j import Neo4jGraph


# --- Configuration ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "rootroot123") 

# Directory where the backend server stores uploaded files
UPLOADS_DIR = "../knowledge-base-backend/uploads"
PROCESSED_DIR = os.path.join(UPLOADS_DIR, "processed")

if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)
    print(f"Created directory: {PROCESSED_DIR}")

# --- Graph and LLM Initialization ---

print("Configuring Google Gemini...")
genai.configure(api_key=GOOGLE_API_KEY)

print("Connecting to Neo4j...")
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)
print("Connection to Neo4j successful.")
print("Graph schema fetched. Ready to process documents.")

llm = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

# --- JSON Schemas for Structured Output ---
nodes_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "label": {"type": "string"}
        },
        "required": ["name", "label"]
    }
}

relationships_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "target": {"type": "string"},
            "type": {"type": "string"},
            "properties": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "date": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        },
        "required": ["source", "target", "type"]
    }
}

# --- Two-Step Prompting Logic ---

NODE_EXTRACTION_PROMPT = """
From the text provided, identify all the key entities.
An entity can be a person, organization, project, product, technology, or concept.
For each entity, provide its name and a suitable label from this list:
["Person", "Organization", "Project", "Product", "Technology", "Concept", "Material", "Platform"]

Text:
"{text}"
"""

RELATIONSHIP_EXTRACTION_PROMPT = """
From the text provided, identify the relationships between the entities listed in the "Candidate Entities" section.
A relationship is a triplet of (source_entity_name, relationship_type, target_entity_name).

- The relationship_type MUST be a concise verb phrase in all caps, with words connected by underscores (e.g., "LEADS", "ACQUIRES", "IS_CEO_OF", "COLLABORATES_ON"). IT CANNOT CONTAIN SPACES.
- The source_entity_name is the entity performing the action or being described.
- The target_entity_name is the entity being acted upon or the description.

For example, in "Project Alpha is led by Maria Garcia", the source is "Maria Garcia", the target is "Project Alpha", and the type is "LEADS".
In "The CEO of Global Motors is Elena Petrova", the source is "Elena Petrova", the target is "Global Motors", and the type is "IS_CEO_OF".

Also, identify any properties of the relationship, such as the value or date of a transaction.
The source and target entity names MUST be one of the names from the "Candidate Entities" list.

Candidate Entities:
{entities}

Text:
"{text}"
"""

def extract_and_store_graph(document: Document):
    """
    Extracts entities and relationships from a document and stores them in the Neo4j graph.
    """
    print(f"Processing document: {document.metadata.get('source', 'Unknown')}")
    
    text_content = document.page_content
    
    try:
        # STEP 1: Extract Nodes
        print("  - Step 1: Extracting nodes...")
        node_prompt = NODE_EXTRACTION_PROMPT.format(text=text_content)
        node_config = GenerationConfig(response_mime_type="application/json", response_schema=nodes_schema)
        node_response = llm.generate_content(node_prompt, generation_config=node_config)
        nodes = json.loads(node_response.text)
        
        print(f"    > Found {len(nodes)} nodes.")
        for node in nodes:
            # --- THIS IS THE FIX: Sanitize name by lowercasing and stripping punctuation ---
            sanitized_name = node.get('name', '').lower().strip(string.punctuation + " ")
            if sanitized_name:
                node['name'] = sanitized_name
                graph.query("MERGE (n:`{label}` {{name: $name}})".format(label=node['label']), params=node)

        # STEP 2: Extract Relationships
        print("  - Step 2: Extracting relationships...")
        entity_names = [node['name'] for node in nodes]
        
        relationship_prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(
            text=text_content, 
            entities=json.dumps(entity_names)
        )
        relationship_config = GenerationConfig(response_mime_type="application/json", response_schema=relationships_schema)
        relationship_response = llm.generate_content(relationship_prompt, generation_config=relationship_config)
        relationships = json.loads(relationship_response.text)
        
        print(f"    > Found {len(relationships)} relationships.")
        for rel in relationships:
            # --- THIS IS THE FIX: Sanitize names by lowercasing and stripping punctuation ---
            source_name = rel.get('source', '').lower().strip(string.punctuation + " ")
            target_name = rel.get('target', '').lower().strip(string.punctuation + " ")

            if not source_name or not target_name:
                continue # Skip if source or target is missing

            cypher = """
            MATCH (a), (b)
            WHERE a.name = $source_name AND b.name = $target_name
            MERGE (a)-[r:`{rel_type}`]->(b)
            SET r += $props
            """.format(rel_type=rel['type'])
            
            rel_props = rel.get("properties", {})
            graph.query(cypher, params={
                "source_name": source_name, 
                "target_name": target_name, 
                "props": rel_props
            })

        print("Successfully stored graph data for the document.")

    except Exception as e:
        print(f"An error occurred during LLM invocation or processing: {e}")


def load_document(filepath):
    """
    Loads a document from a file path, supporting .txt, .pdf, and .docx.
    """
    _, extension = os.path.splitext(filepath)
    loader = None
    if extension.lower() == '.txt':
        loader = TextLoader(filepath, encoding='utf-8')
    elif extension.lower() == '.pdf':
        loader = PyPDFLoader(filepath)
    elif extension.lower() == '.docx':
        loader = Docx2txtLoader(filepath)
    
    if loader:
        print(f"Loading document: {os.path.basename(filepath)}")
        return loader.load()
    else:
        print(f"Unsupported file type: {extension}. Skipping.")
        return None

def process_new_documents():
    """
    Continuously scans the uploads directory for new files to process.
    """
    print("Starting document processing service...")
    while True:
        all_files = glob.glob(os.path.join(UPLOADS_DIR, "*.*"))
        processed_files_paths = glob.glob(os.path.join(PROCESSED_DIR, "*.*"))
        processed_files_names = [os.path.basename(p) for p in processed_files_paths]
        
        new_files = [f for f in all_files if os.path.basename(f) not in processed_files_names]

        if not new_files:
            print("No new documents to process. Waiting...")
        else:
            for filepath in new_files:
                documents = load_document(filepath)
                if documents:
                    for doc in documents:
                        extract_and_store_graph(doc)
                    
                    try:
                        base_name = os.path.basename(filepath)
                        os.rename(filepath, os.path.join(PROCESSED_DIR, base_name))
                        print(f"Moved {base_name} to processed directory.")
                    except Exception as e:
                        print(f"Error moving file {filepath}: {e}")

        time.sleep(30)


if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("FATAL ERROR: GOOGLE_API_KEY not found. Make sure it is set in your .env file.")
    else:
        process_new_documents()
