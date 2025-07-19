import fitz
import tiktoken
from astrapy import DataAPIClient
import streamlit as st
import os
import hashlib
import json
from local_models import get_local_embeddings

EMBED_DIMENSIONS = 384  # all-MiniLM-L6-v2 dimensions
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

UPLOADED_PDFS_FILE = "uploaded_pdfs.json"

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

def get_astra_collection():
    astra_client = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
    database = astra_client.get_database_by_api_endpoint(os.getenv("ASTRA_DB_API_ENDPOINT"))
    
    collection_name = os.getenv("ASTRA_DB_COLLECTION")
    
    try:
        collection = database.get_collection(collection_name)
        return collection
    except Exception:
        st.info(f"Collection '{collection_name}' doesn't exist. Creating it now...")
        collection = database.create_collection(
            collection_name,
            dimension=EMBED_DIMENSIONS,
            metric="cosine"
        )
        st.success(f"✅ Collection '{collection_name}' created successfully!")
        return collection

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

def upload_chunks_to_astradb(chunks, metadatas, pdf_filename=None):
    collection = get_astra_collection()
    embeddings_model = get_local_embeddings()
    
    if not embeddings_model:
        st.error("Failed to load embedding model")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    documents = []
    for i, chunk in enumerate(chunks):
        progress = (i + 1) / len(chunks)
        progress_bar.progress(progress)
        status_text.text(f"Preparing embedding {i + 1}/{len(chunks)} for {pdf_filename or 'PDF'}")
        
        # Generate embedding using local model
        embedding = embeddings_model.embed_query(chunk)
        
        chunk_id = f"{pdf_filename or 'unknown'}_{i}" if pdf_filename else f"chunk-{i}"
        
        metadata = metadatas[i].copy()
        if pdf_filename:
            metadata["document_name"] = pdf_filename
        
        document = {
            "_id": chunk_id,
            "$vector": embedding,
            "content": chunk,
            "page": metadata.get("page"),
            "document_name": metadata.get("document_name", pdf_filename),
            "metadata": metadata
        }
        documents.append(document)
    
    status_text.text(f"Uploading {len(documents)} documents to database...")
    
    batch_size = 20
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        collection.insert_many(batch)
        progress = (i + batch_size) / len(documents)
        progress_bar.progress(min(progress, 1.0))
    
    progress_bar.empty()
    status_text.empty()

def get_uploaded_pdfs_list():
    uploaded_pdfs = load_uploaded_pdfs()
    return [pdf_id.split('_')[0] for pdf_id in uploaded_pdfs]

def clear_uploaded_pdfs():
    if os.path.exists(UPLOADED_PDFS_FILE):
        os.remove(UPLOADED_PDFS_FILE)
    return True

def clear_astra_collection():
    try:
        collection = get_astra_collection()
        collection.delete_many({})
        return True
    except Exception as e:
        st.error(f"Error clearing collection: {e}")
        return False 