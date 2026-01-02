import pymupdf  # fitz
import os

def extract_text_from_pdf(pdf_path):
    """
    Reads a PDF file and returns the full text content.
    """
    if not os.path.exists(pdf_path):
        return ""
        
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text

def chunk_text(text, chunk_size=2000, overlap=200):
    """
    Splits large text into smaller chunks for the AI.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def process_document(pdf_path):
    """
    Main function to handle a PDF upload.
    """
    raw_text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(raw_text)
    
    return {
        "filename": os.path.basename(pdf_path),
        "full_text": raw_text,
        "chunks": chunks,
        "chunk_count": len(chunks)
    }