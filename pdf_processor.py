import os
from PyPDF2 import PdfReader
import docx

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return None

def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT: {e}")
        return None

def process_document(file_path):
    """
    Determines file type and extracts text accordingly.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        full_text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        full_text = extract_text_from_docx(file_path)
    elif ext == ".txt":
        full_text = extract_text_from_txt(file_path)
    else:
        return None

    if not full_text:
        return None

    # SMARTER SPLITTING (Recursive)
    # This keeps sentences together instead of cutting them in half
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = splitter.split_text(full_text)
    
    return {
        "filename": os.path.basename(file_path),
        "full_text": full_text,
        "chunks": chunks,
        "chunk_count": len(chunks)
    }