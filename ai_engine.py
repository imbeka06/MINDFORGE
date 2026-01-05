import os
import json
import io
import arxiv
from dotenv import load_dotenv
from gtts import gTTS

# Core LangChain imports
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA 
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

embeddings = None
client = None 

# --- INITIALIZATION ---
def get_llm(model_name="gpt-3.5-turbo"):
    """
    Returns the LLM based on user selection.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return None
    return ChatOpenAI(model=model_name, temperature=0.3, api_key=api_key)

try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        embeddings = OpenAIEmbeddings(api_key=api_key)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"Startup Error: {e}")

# --- 1. DEEP ANALYSIS FUNCTIONS ---

def generate_deep_summary(chunks, model_name="gpt-3.5-turbo"):
    """
    Reads the first 3 chunks (approx 15 pages) to create a comprehensive summary.
    """
    llm = get_llm(model_name)
    if not llm: return "⚠️ AI not running."
    
    # We combine the first 3 chunks to get a broader context
    # (Adjust this number if you want it to read even more, but it costs more)
    combined_text = "\n\n".join(chunks[:3])
    
    try:
        prompt = f"""
        You are an expert Research Analyst. Perform a Deep Analysis on the following document text.
        Do not be vague. Extract concrete data, arguments, and findings.
        
        Format the output as:
        # 📑 Executive Report
        
        ## 1. Core Thesis
        (2-3 sentences explaining the main argument)
        
        ## 2. Key Findings & Data
        * (Bullet point with specific details)
        * (Bullet point with specific details)
        * (Bullet point with specific details)
        
        ## 3. Critical Analysis
        (Discuss methodology, strengths, or implications)
        
        ## 4. Conclusion
        (Final takeaway)
        
        TEXT DATA: {combined_text[:12000]}
        """
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def generate_mind_map(text_chunk, model_name="gpt-3.5-turbo"):
    llm = get_llm(model_name)
    if not llm: return {"nodes": [], "edges": []}
    try:
        prompt = f"""
        Analyze the text and identify core concepts.
        Output ONLY valid JSON with 'nodes' (id) and 'edges' (from, to).
        TEXT: {text_chunk[:3000]}
        """
        response = llm.invoke(prompt)
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except:
        return {"nodes": [], "edges": []}

def generate_quiz(text_chunk, model_name="gpt-3.5-turbo"):
    llm = get_llm(model_name)
    if not llm: return []
    try:
        prompt = f"""
        Create 3 multiple-choice questions (JSON format).
        [
            {{
                "question": "...",
                "options": ["A", "B", "C", "D"],
                "answer": "Option A"
            }}
        ]
        TEXT: {text_chunk[:3000]}
        """
        response = llm.invoke(prompt)
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except:
        return []

# --- 2. RESEARCH ENGINE (ARXIV) ---

def search_arxiv_papers(topic):
    """
    Searches ArXiv database for scientific papers.
    """
    try:
        # Search for top 5 results
        search = arxiv.Search(
            query=topic,
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for result in search.results():
            results.append({
                "title": result.title,
                "summary": result.summary,
                "pdf_url": result.pdf_url,
                "published": result.published.strftime("%Y-%m-%d")
            })
        return results
    except Exception as e:
        print(f"ArXiv Error: {e}")
        return []

# --- 3. MEMORY & CHAT ---

def create_vector_db(chunks, save_path=None):
    if not embeddings: return None
    try:
        docs = [Document(page_content=chunk) for chunk in chunks]
        vector_store = FAISS.from_documents(docs, embeddings)
        if save_path:
            vs_path = os.path.join(save_path, "vector_store")
            vector_store.save_local(vs_path)
        return vector_store
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def load_vector_db(load_path):
    if not embeddings: return None
    vs_path = os.path.join(load_path, "vector_store")
    if os.path.exists(vs_path):
        try:
            return FAISS.load_local(vs_path, embeddings, allow_dangerous_deserialization=True)
        except: return None
    return None

def get_chat_response(query, vector_store, model_name="gpt-3.5-turbo"):
    llm = get_llm(model_name)
    if not llm or not vector_store: return "AI not ready."
    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm, chain_type="stuff", retriever=vector_store.as_retriever()
        )
        response = qa_chain.invoke(query)
        return response["result"]
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. AUDIO ---
def transcribe_audio(audio_file):
    if not client: return None
    try:
        return client.audio.transcriptions.create(model="whisper-1", file=audio_file).text
    except: return None

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except: return None