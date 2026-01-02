import os
import json
from dotenv import load_dotenv

# Core LangChain imports
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA 
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

# Global variable to store startup errors for debugging
init_error = None
embeddings = None
llm = None

try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Try to be helpful if the key is missing
        print("⚠️ Warning: OPENAI_API_KEY not found in environment.")
    else:
        # Attempt to start the AI
        embeddings = OpenAIEmbeddings(api_key=api_key)
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, api_key=api_key)

except Exception as e:
    init_error = str(e)
    print(f"DEBUG ERROR: {init_error}")

# --- FUNCTIONS ---

def generate_summary(text_chunk):
    if init_error: return f"⚠️ **AI Startup Error:** {init_error}"
    if not llm: return "⚠️ AI not running."
    
    try:
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
    except Exception as e:
        return f"⚠️ Error during summarization: {str(e)}"

def generate_mind_map(text_chunk):
    if not llm: return {"nodes": [], "edges": []}

    try:
        prompt = f"""
        Analyze the text and identify core concepts and relationships.
        Output ONLY valid JSON with 'nodes' (id, group) and 'edges' (from, to, label).
        Do not use markdown blocks.
        
        TEXT: {text_chunk[:3000]}
        """
        response = llm.invoke(prompt)
        # Clean cleanup
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"Mind Map Error: {e}")
        return {"nodes": [], "edges": []}

def create_vector_db(chunks):
    if not embeddings: return None
    try:
        docs = [Document(page_content=chunk) for chunk in chunks]
        vector_store = FAISS.from_documents(docs, embeddings)
        return vector_store
    except Exception as e:
        print(f"Vector DB Error: {e}")
        return None

def get_chat_response(query, vector_store):
    if init_error: return f"System Error: {init_error}"
    if not llm or not vector_store: return "AI is not ready."

    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever()
        )
        response = qa_chain.invoke(query)
        return response["result"]
    except Exception as e:
        return f"Chat Error: {str(e)}"

def generate_quiz(text_chunk):
    """Generates a 3-question MCQ quiz."""
    if not llm: return "AI not ready."
    
    prompt = f"""
    Create a mini-quiz with 3 multiple-choice questions based on this text.
    Format the output EXACTLY like this:
    
    Q1: [Question]
    A) [Option]
    B) [Option]
    C) [Option]
    D) [Option]
    Answer: [Correct Letter]
    
    (Repeat for Q2 and Q3)
    
    TEXT: {text_chunk[:3000]}
    """
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Quiz Error: {str(e)}"