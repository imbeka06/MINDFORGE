import os
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Load Environment Variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# --- 1. CORE AI SETUP ---
embeddings = OpenAIEmbeddings(api_key=api_key)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, api_key=api_key)

# --- 2. KNOWLEDGE SYNTHESIS FUNCTIONS ---

def generate_summary(text_chunk):
    """Generates a structured summary of the text."""
    prompt = f"""
    You are an expert academic tutor. Summarize the following text clearly.
    Use these sections: 
    1. Core Concept
    2. Key Details (Bullet points)
    3. Practical Implication
    
    TEXT: {text_chunk[:4000]}
    """
    response = llm.invoke(prompt)
    return response.content

def generate_mind_map(text_chunk):
    """Extracts concepts for visualization."""
    prompt = f"""
    Analyze the text and identify core concepts and relationships.
    Output ONLY valid JSON with 'nodes' (id, group) and 'edges' (from, to, label).
    Do not use markdown blocks.
    
    TEXT: {text_chunk[:3000]}
    """
    response = llm.invoke(prompt)
    content = response.content.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(content)
    except:
        return {"nodes": [], "edges": []} # Fallback if JSON fails

# --- 3. CHAT / RAG FUNCTIONS ---

def create_vector_db(chunks):
    """
    Creates a temporary searchable database from PDF chunks.
    Returns the vector store object.
    """
    # Convert string chunks to Document objects
    docs = [Document(page_content=chunk) for chunk in chunks]
    
    # Create Vector Store
    vector_store = FAISS.from_documents(docs, embeddings)
    return vector_store

def get_chat_response(query, vector_store):
    """
    Searches the PDF content and answers the user's question.
    """
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever()
    )
    response = qa_chain.invoke(query)
    return response["result"]