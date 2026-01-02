import os
import json
import io
from dotenv import load_dotenv
from gtts import gTTS

# Core LangChain imports
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA 
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

# Global variables
init_error = None
embeddings = None
llm = None
client = None # Direct OpenAI client for Whisper

try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ Warning: OPENAI_API_KEY not found in environment.")
    else:
        # 1. Initialize LangChain Components
        embeddings = OpenAIEmbeddings(api_key=api_key)
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, api_key=api_key)
        
        # 2. Initialize Direct OpenAI Client (For Whisper Audio)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

except Exception as e:
    init_error = str(e)
    print(f"DEBUG ERROR: {init_error}")

# --- TEXT FUNCTIONS ---

def generate_summary(text_chunk):
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
        return f"⚠️ Error: {str(e)}"

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
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except:
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
    if not llm or not vector_store: return "AI is not ready."
    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm, chain_type="stuff", retriever=vector_store.as_retriever()
        )
        response = qa_chain.invoke(query)
        return response["result"]
    except Exception as e:
        return f"Chat Error: {str(e)}"

def generate_quiz(text_chunk):
    if not llm: return "AI not ready."
    try:
        prompt = f"""
        Create a mini-quiz with 3 multiple-choice questions based on this text.
        Format output EXACTLY like this:
        Q1: [Question]
        A) [Option]
        B) [Option]
        C) [Option]
        D) [Option]
        Answer: [Correct Letter]
        (Repeat for Q2, Q3)
        TEXT: {text_chunk[:3000]}
        """
        response = llm.invoke(prompt)
        return response.content
    except:
        return "Quiz generation failed."

# --- NEW: AUDIO FUNCTIONS ---

def transcribe_audio(audio_file):
    """
    Uses OpenAI Whisper to convert Speech -> Text.
    """
    if not client: return None
    try:
        # OpenAI Whisper API expects a file-like object with a name
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        return transcript.text
    except Exception as e:
        print(f"Whisper Error: {e}")
        return None

def text_to_speech(text):
    """
    Uses Google TTS to convert Text -> Audio Bytes.
    """
    try:
        # Generate audio in memory (no file saved)
        tts = gTTS(text=text, lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except Exception as e:
        print(f"TTS Error: {e}")
        return None