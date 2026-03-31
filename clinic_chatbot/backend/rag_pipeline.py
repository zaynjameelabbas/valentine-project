import os
import re
from docx2pdf import convert
from langchain_community.llms import Ollama
# from langchain_community.document_loaders import PyPDFLoader
# more powerful loader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate

# --- NEW MEMORY IMPORTS ---
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.chains import create_history_aware_retriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
# --------------------------

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain

llm = Ollama(model="llama3.1")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Data
DATA_DIR = "./data"
CHROMA_DIR = "./vector_store"


# import os
# import re
# from docx2pdf import convert
# from langchain_community.document_loaders import PyMuPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import Chroma
# from langchain_core.prompts import PromptTemplate

# # --- NEW MEMORY IMPORTS ---
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.messages import HumanMessage, AIMessage
# from langchain_classic.chains import create_history_aware_retriever
# from langchain_classic.retrievers.multi_query import MultiQueryRetriever
# from langchain_classic.chains.combine_documents import create_stuff_documents_chain
# from langchain_classic.chains import create_retrieval_chain

# # --- NEW CLOUD LLM & EMBEDDINGS ---
# from langchain_groq import ChatGroq
# from langchain_huggingface import HuggingFaceEmbeddings

# # Initialize Groq (Make sure GROQ_API_KEY is in your environment variables)
# llm = ChatGroq(
#     model="llama-3.1-8b-instant", # Matches your local Llama 3.1 choice
#     api_key=os.environ.get("GROQ_API_KEY") 
# )

# # Initialize Hugging Face Embeddings (Runs locally in your HF Space)
# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# # Data
# DATA_DIR = "./data"
# CHROMA_DIR = "./vector_store"

def sanitize_collection_name(name: str) -> str:
    """
    Cleans up filenames to meet ChromaDB's strict collection naming rules.
    Replaces spaces with underscores and removes invalid characters.
    """
    clean_name = name.replace(" ", "_")
    clean_name = re.sub(r'[^a-zA-Z0-9._-]', '', clean_name)
    return clean_name

def auto_convert_docs():
    """Converts any .docx files in the data folder to .pdf"""
    print("Checking for Word documents to convert...")
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".docx"):
            docx_path = os.path.join(DATA_DIR, filename)
            pdf_path = os.path.join(DATA_DIR, filename.replace(".docx", ".pdf"))
            
            # Only convert if the PDF doesn't already exist
            if not os.path.exists(pdf_path):
                print(f"Converting {filename} to PDF. This may open Microsoft Word briefly...")
                try:
                    convert(docx_path, pdf_path)
                    print(f"Successfully converted {filename}")
                except Exception as e:
                    print(f"Error converting {filename}: {e}")

def ingest_documents():
    """
    Converts Word docs to PDFs, then reads ONLY PDFs 
    and creates a separate collection for each protocol.
    """
    # 1. RUN CONVERSION BEFORE INGESTING
    auto_convert_docs()
    
    # 2. PROCEED WITH INGESTION
    print("\nScanning data directory for PDF protocols...")
    
    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        documents = []
        
        # Only process PDFs
        if filename.endswith(".pdf"):
            protocol_name = filename.replace(".pdf", "")
            print(f"Loading PDF: {protocol_name}...")
            
            # UPGRADED PARSER
            loader = PyMuPDFLoader(file_path) 
            documents = loader.load()
        else:
            continue

        if documents:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)

            collection_name = sanitize_collection_name(protocol_name)

            print(f"Saving {protocol_name} to collection: {collection_name}...")
            Chroma.from_documents(
                chunks, 
                embeddings, 
                collection_name=collection_name, 
                persist_directory=CHROMA_DIR
            )
            
    print("All protocols ingested into separate collections!")
    return True

def query_protocol(user_question: str, procedure_id: str, chat_history: list = None):
    """
    Retrieves chunks using MMR + MultiQueryRetriever and factors in conversational history.
    """
    if chat_history is None:
        chat_history = []

    # 1. Convert frontend history into LangChain format
    formatted_history = []
    for msg in chat_history:
        if msg.get("type") == "user-message":
            formatted_history.append(HumanMessage(content=msg.get("text")))
        elif msg.get("type") == "bot-message":
            formatted_history.append(AIMessage(content=msg.get("text")))

    collection_name = sanitize_collection_name(procedure_id)
    
    db = Chroma(
        collection_name=collection_name, 
        persist_directory=CHROMA_DIR, 
        embedding_function=embeddings
    )
    
    # 2. Define the base database search
    base_retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 12, "fetch_k": 30}
    )

    # 3. UPGRADE: Wrap it in the MultiQueryRetriever to catch tables and text
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever, 
        llm=llm
    )

    # 4. History-Aware Question Reformulation Prompt
    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # 5. The Main Q&A Prompt (One-Shot Example)
    qa_system_prompt = """
    You are a highly precise medical assistant for the University of Manitoba Surgery Clinic. You answer patient questions based strictly on the provided context.

    Context: {context}

    CRITICAL RULES:
    1. Answer immediately. Do not use filler, greetings, or introductory phrases.
    2. Extract exact numbers, timelines (weeks/months), and instructions from the text. 
    3. Use plain text and simple bullet points. No bolding, no asterisks.
    4. If the context does not contain the answer, or if the user describes an emergency, reply EXACTLY with: 'This information is outside the scope of the standard protocol. Please contact the clinic directly, or call 911 if you are experiencing a medical emergency.'

    EXAMPLE BEHAVIOR:
    User: When can I start jogging?
    Assistant: You can anticipate returning to jogging at 4 to 5 months post-op. Before you begin, you must pass the physical therapy screening exam and be cleared by your physician. You will start at slow, comfortable speeds for short distances.

    END OF EXAMPLE.

    Answer the patient's question following the exact tone and style of the example above:
    """

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # 6. Invoke with history
    response = rag_chain.invoke({
        "input": user_question,
        "chat_history": formatted_history
    })
    
    return response["answer"]

if __name__ == "__main__":
    ingest_documents()