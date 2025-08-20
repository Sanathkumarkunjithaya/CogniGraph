import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import google.generativeai as genai
from langchain_neo4j import Neo4jGraph

load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "rootroot123") 

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)


# --- Graph and LLM Initialization ---
graph = None
llm = None
graph_schema = ""
try:
    print("Connecting to Neo4j...")
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD
    )
    graph_schema = graph.schema
    
    print("Initializing Google Gemini...")
    genai.configure(api_key=GOOGLE_API_KEY)
    llm = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    
    print("--- SUCCESS: Query Engine is ready. ---")
    print("--- Graph Schema ---")
    print(graph_schema)
    print("--------------------")

except Exception as e:
    print(f"--- FAILED to initialize services: {e} ---")

# --- THIS IS THE FINAL, MOST ROBUST PROMPT ---
CYPHER_GENERATION_PROMPT = """
You are an expert Neo4j developer. Your task is to convert a natural language question into a valid Cypher query based on the provided Neo4j graph schema.

**CRITICAL RULES:**
1.  **Strictly Adhere to Schema:** You MUST use the exact node labels and relationship types provided in the schema. You are FORBIDDEN from using any labels or relationship types not listed in the schema. If the user's question implies a relationship that is not in the schema, you must find the most semantically similar one from the schema and use that.
2.  **Lowercase all Names:** All 'name' properties in the graph are stored in lowercase. When generating a query that filters by a 'name' property, you MUST convert the value from the user's question to lowercase. For example, if the question is about "QuantumLeap", your query's WHERE clause MUST use `p.name = 'quantumleap'`.
3.  **Return ONLY the Cypher Query:** Your entire response must be only the Cypher query. Do not include any explanations, comments, markdown formatting, or any text other than the query itself.

**Schema:**
{schema}

**Question:** {question}
**Cypher Query:**
"""

FINAL_ANSWER_PROMPT = """
You are an expert AI assistant. Your task is to provide a concise, natural language answer to a user's question based on the data returned from a database query.
Do not mention the database or the query. Just provide the answer. If the data is empty, say you could not find an answer.

Question: {question}

Query Result Data:
{context}

Final Answer:
"""


# --- API Routes ---

@app.route('/query', methods=['POST'])
def query_graph():
    if not graph or not llm:
        return jsonify({"error": "Services not initialized. Check server logs."}), 500

    data = request.get_json()
    question = data.get('query')

    if not question:
        return jsonify({"error": "No query provided."}), 400

    print(f"\nReceived query: {question}")

    try:
        # Step 1: Generate Cypher query
        cypher_prompt = CYPHER_GENERATION_PROMPT.format(schema=graph_schema, question=question)
        cypher_response = llm.generate_content(cypher_prompt)
        
        # --- Robust Error Handling ---
        if not cypher_response.parts:
            print("API Safety Block: The model did not return a valid response for the Cypher generation prompt.")
            return jsonify({"answer": "I could not generate a valid query for that question."})
            
        generated_cypher = cypher_response.text.strip().replace('`','').replace('cypher','').strip()
        print(f"Generated Cypher: {generated_cypher}")

        # Step 2: Execute the query
        context = graph.query(generated_cypher)
        context_str = json.dumps(context, indent=2)
        print(f"Query Result: {context_str}")

        # Step 3: Generate a natural language answer
        answer_prompt = FINAL_ANSWER_PROMPT.format(question=question, context=context_str)
        answer_response = llm.generate_content(answer_prompt)
        
        if not answer_response.parts:
            print("API Safety Block: The model did not return a valid response for the final answer prompt.")
            return jsonify({"answer": "I found data, but could not formulate a final answer."})

        final_answer = answer_response.text.strip()
        print(f"Returning answer: {final_answer}")
        return jsonify({"answer": final_answer})

    except Exception as e:
        print(f"An error occurred while processing the query: {e}")
        return jsonify({"error": "An error occurred on the server."}), 500

@app.route('/', methods=['GET'])
def health_check():
    return "Query Engine is running!"

# --- Start the Server ---

if __name__ == '__main__':
    if not GOOGLE_API_KEY:
        print("FATAL ERROR: Make sure GOOGLE_API_KEY is set in your .env file.")
    else:
        app.run(host='0.0.0.0', port=5000)
