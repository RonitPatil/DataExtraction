import os
import pickle
import json
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
from langchain.schema import Document
from langchain.vectorstores import FAISS
from local_models import get_local_embeddings
import streamlit as st

FAISS_INDEX_DIR = "faiss_index"
FAISS_METADATA_FILE = "faiss_metadata.json"
UPLOADED_PDFS_FILE = "uploaded_pdfs.json"

def ensure_faiss_dir():
    if not os.path.exists(FAISS_INDEX_DIR):
        os.makedirs(FAISS_INDEX_DIR)

def get_faiss_vectorstore():
    ensure_faiss_dir()
    embeddings = get_local_embeddings()
    if not embeddings:
        st.error("Failed to load embedding model")
        return None
    
    index_path = os.path.join(FAISS_INDEX_DIR, "index")
    if os.path.exists(index_path):
        try:
            vectorstore = FAISS.load_local(index_path, embeddings)
            return vectorstore
        except Exception as e:
            st.error(f"Error loading existing Faiss index: {e}")
            return None
    else:
        return None

def create_faiss_vectorstore():
    ensure_faiss_dir()
    embeddings = get_local_embeddings()
    if not embeddings:
        st.error("Failed to load embedding model")
        return None
    
    index_path = os.path.join(FAISS_INDEX_DIR, "index")
    if os.path.exists(index_path):
        try:
            vectorstore = FAISS.load_local(index_path, embeddings)
            return vectorstore
        except Exception:
            pass
    
    return FAISS.from_texts([], embeddings)

def save_faiss_vectorstore(vectorstore):
    ensure_faiss_dir()
    index_path = os.path.join(FAISS_INDEX_DIR, "index")
    vectorstore.save_local(index_path)

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

def is_pdf_already_uploaded(pdf_path, pdf_filename):
    uploaded_pdfs = load_uploaded_pdfs()
    file_hash = hashlib.md5(open(pdf_path, 'rb').read()).hexdigest()
    return file_hash in uploaded_pdfs

def mark_pdf_as_uploaded(pdf_path, pdf_filename):
    uploaded_pdfs = load_uploaded_pdfs()
    file_hash = hashlib.md5(open(pdf_path, 'rb').read()).hexdigest()
    uploaded_pdfs.add(file_hash)
    save_uploaded_pdfs(uploaded_pdfs)

def get_uploaded_pdfs_list():
    uploaded_pdfs = load_uploaded_pdfs()
    return list(uploaded_pdfs)

def clear_uploaded_pdfs():
    if os.path.exists(UPLOADED_PDFS_FILE):
        os.remove(UPLOADED_PDFS_FILE)
    if os.path.exists(FAISS_INDEX_DIR):
        import shutil
        shutil.rmtree(FAISS_INDEX_DIR)

def upload_chunks_to_faiss(chunks, metadatas, pdf_filename=None):
    embeddings_model = get_local_embeddings()
    if not embeddings_model:
        st.error("Failed to load embedding model")
        return
    
    vectorstore = get_faiss_vectorstore()
    if vectorstore is None:
        vectorstore = create_faiss_vectorstore()
    
    if vectorstore is None:
        st.error("Failed to create Faiss vector store")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    documents = []
    for i, chunk in enumerate(chunks):
        progress = (i + 1) / len(chunks)
        progress_bar.progress(progress)
        status_text.text(f"Preparing embedding {i + 1}/{len(chunks)} for {pdf_filename or 'PDF'}")
        
        metadata = metadatas[i].copy()
        if pdf_filename:
            metadata["document_name"] = pdf_filename
        
        doc = Document(
            page_content=chunk,
            metadata=metadata
        )
        documents.append(doc)
    
    status_text.text(f"Adding {len(documents)} documents to Faiss index...")
    
    try:
        vectorstore.add_documents(documents)
        save_faiss_vectorstore(vectorstore)
        progress_bar.empty()
        status_text.empty()
        st.success(f"Successfully added {len(documents)} documents to Faiss index")
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Error adding documents to Faiss: {e}")

def clear_faiss_collection():
    try:
        if os.path.exists(FAISS_INDEX_DIR):
            import shutil
            shutil.rmtree(FAISS_INDEX_DIR)
        return True
    except Exception as e:
        st.error(f"Error clearing Faiss index: {e}")
        return False 