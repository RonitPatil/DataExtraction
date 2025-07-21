import fitz
import tiktoken
import streamlit as st
import os
import hashlib
import json
from local_models import get_local_embeddings

EMBED_DIMENSIONS = 384  # all-MiniLM-L6-v2 dimensions
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def load_uploaded_pdfs():
    if os.path.exists(UPLOADED_PDFS_FILE):
        try:
            with open(UPLOADED_PDFS_FILE, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, FileNotFoundError):
            return set()
    return set()

def save_uploaded_pdfs(uploaded_pdfs):
    with open(UPLOADED_PDFS_FILE, 'w') as f:
        json.dump(list(uploaded_pdfs), f)

def get_pdf_hash(pdf_path):
    with open(pdf_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_faiss_collection():
    from faiss_store import get_faiss_vectorstore, create_faiss_vectorstore
    
    vectorstore = get_faiss_vectorstore()
    if vectorstore is None:
        vectorstore = create_faiss_vectorstore()
        if vectorstore:
            st.success("✅ Faiss index created successfully!")
    
    return vectorstore

def process_pdf(pdf_path, pdf_filename=None):
    doc = fitz.open(pdf_path)
    chunks = []
    metadatas = []
    enc = tiktoken.get_encoding("cl100k_base")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page_num in range(len(doc)):
        progress = (page_num + 1) / len(doc)
        progress_bar.progress(progress)
        status_text.text(f"Processing page {page_num + 1}/{len(doc)} of {pdf_filename or 'PDF'}")
        
        page = doc[page_num]
        text = page.get_text()
        tokens = enc.encode(text)
        i = 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i+CHUNK_SIZE]
            chunk_text = enc.decode(chunk_tokens)
            chunks.append(chunk_text)
            meta = {"page": page_num+1}
            if pdf_filename:
                meta["document_name"] = pdf_filename
            metadatas.append(meta)
            i += CHUNK_SIZE - CHUNK_OVERLAP
    
    progress_bar.empty()
    status_text.empty()
    return chunks, metadatas

def is_pdf_already_uploaded(pdf_path, pdf_filename):
    uploaded_pdfs = load_uploaded_pdfs()
    pdf_hash = get_pdf_hash(pdf_path)
    pdf_id = f"{pdf_filename}_{pdf_hash}"
    return pdf_id in uploaded_pdfs

def mark_pdf_as_uploaded(pdf_path, pdf_filename):
    uploaded_pdfs = load_uploaded_pdfs()
    pdf_hash = get_pdf_hash(pdf_path)
    pdf_id = f"{pdf_filename}_{pdf_hash}"
    uploaded_pdfs.add(pdf_id)
    save_uploaded_pdfs(uploaded_pdfs)

def upload_chunks_to_faiss(chunks, metadatas, pdf_filename=None):
    from faiss_store import upload_chunks_to_faiss as upload_to_faiss
    upload_to_faiss(chunks, metadatas, pdf_filename)

def get_uploaded_pdfs_list():
    uploaded_pdfs = load_uploaded_pdfs()
    return [pdf_id.split('_')[0] for pdf_id in uploaded_pdfs]

def clear_uploaded_pdfs():
    if os.path.exists(UPLOADED_PDFS_FILE):
        os.remove(UPLOADED_PDFS_FILE)
    return True

def clear_faiss_collection():
    from faiss_store import clear_faiss_collection as clear_faiss
    return clear_faiss() 