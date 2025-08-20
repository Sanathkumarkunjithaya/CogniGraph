# CogniGraph: AI-Powered Knowledge Base Engine

**Turn scattered documents into a centralized, queryable knowledge graph.**

CogniGraph is a full-stack prototype that ingests unstructured text from documents, uses a Large Language Model (LLM) to understand the content, and builds a connected knowledge graph. It provides a simple web interface where users can ask complex questions in plain English and receive precise, AI-generated answers.

---

### **Problem Statement**

In many organizations, valuable information is locked away in various unstructured documents like reports, articles, and updates. It's difficult and time-consuming for users to find specific insights or understand the complex relationships between different pieces of information scattered across these files. CogniGraph was built to solve this by creating a system that can:

1.  **Ingest** multiple documents automatically.
2.  **Understand** the content using an AI model.
3.  **Structure** this understanding into a connected knowledge graph.
4.  **Provide** a simple interface for users to ask questions in plain English and get answers from the combined knowledge of all documents.

---

### **Features**

* **Drag-and-Drop File Upload:** A seamless web interface for uploading `.txt`, `.pdf`, and `.docx` files.
* **Automated Processing Pipeline:** A background service that runs at a set interval to process new documents.
* **AI-Powered Knowledge Extraction:** Uses the Google Gemini API to perform a reliable two-step process:
    1.  **Node Extraction:** Identifies key entities (people, organizations, projects, etc.).
    2.  **Relationship Extraction:** Determines how these entities are connected.
* **Graph Database Storage:** Stores the extracted information in a Neo4j graph database, preserving complex relationships.
* **Natural Language Query Engine:** Allows users to ask questions in plain English. The engine uses an LLM to:
    1.  Convert the question into a Cypher query.
    2.  Fetch data from the graph.
    3.  Formulate a human-readable answer.

---

### **Architecture & Tech Stack**

CogniGraph is built with a microservices-style architecture, with four distinct components that communicate with each other.


| Component                 | Folder                          | Technology / Frameworks                               | Purpose                                                              |
| ------------------------- | ------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------- |
| **Frontend (Web Interface)** | `knowledge-base-ui`             | **React.js** | Provides the user interface for file uploads and querying.           |
| **Backend (CMS)** | `knowledge-base-backend`        | **Node.js**, **Express.js**, Multer                   | A simple API to receive and store uploaded documents.                |
| **Processing Pipeline** | `knowledge-base-processor`      | **Python**, Google Gemini API, **Neo4j** | Reads documents, extracts knowledge, and builds the graph.           |
| **Query Engine** | `knowledge-base-query-engine`   | **Python**, **Flask**, Google Gemini API              | Translates natural language questions into answers from the graph.   |

---

### **Local Setup & Installation**

To run this project locally, you will need Node.js, Python, and Neo4j Desktop installed.

**1. Clone the repository:**
```bash
git clone https://github.com/Sanathkumarkunjithaya/CogniGraph.git
cd CogniGraph
```

**2. Set up the Database:**
1. Install and open Neo4j Desktop.
2. Create a new database.
3. Set the password to rootroot123 (or update it in the Python .env files).
4. Install the APOC plugin from the "Plugins" tab.
5. In the database settings, add the line dbms.security.procedures.unrestricted=apoc.* to allow the plugin to run.
6. Start the database.


**3. Set up the Backend CMS:**
```bash
cd knowledge-base-backend
npm install
node server.js
# The server will be running on http://localhost:3001
```

**4. Set up the Python Services (Processor & Query Engine):**
For both the `knowledge-base-processor` and `knowledge-base-query-engine` folders, follow these steps:
```bash
cd <folder-name>
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
```

**5. Set up the Frontend:**
```bash
cd knowledge-base-ui
npm install
npm start
# The web app will open on http://localhost:3000
```


**6. Run the Python Services:**
In a new terminal, run the processor:
```bash
cd knowledge-base-processor
.\venv\Scripts\activate
python processor.py
```

In another new terminal, run the query engine:
```bash
cd knowledge-base-query-engine
.\venv\Scripts\activate
python app.py
```

You should now have all four services and the database running.

---

### **Environment Variables**
Both the `knowledge-base-processor` and `knowledge-base-query-engine require` a `.env` file in their root directories.

Create a file named `.env` in each folder with the following content:
```bash
# Your secret API key from Google AI Studio
GOOGLE_API_KEY="your_google_api_key_here"
```

---

### **How to Use**
1. Navigate to `http://localhost:3000` in your browser.
2. Drag and drop a `.txt`, `.pdf`, or `.docx` file into the upload area.
3. Click "Upload Files."
4. Wait for the processor terminal to show that it has processed the document.
5. **Important:** After a new document is processed, restart the query engine server (`app.py`) to ensure it loads the latest database schema.
6. Ask a question about the content of your document(s) in the query box and click "Get Insights."










