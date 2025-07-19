import os
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
import torch
from langchain.llms import HuggingFacePipeline
from langchain.embeddings import HuggingFaceEmbeddings
import streamlit as st

from model_config import (
    GEMMA_MODEL_PATH, 
    EMBEDDING_MODEL_PATH, 
    MAX_NEW_TOKENS, 
    TEMPERATURE, 
    USE_CUDA, 
    DEVICE_MAP
)

@st.cache_resource
def load_gemma_model():
    """Load the Gemma model for text generation"""
    try:
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(GEMMA_MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(
            GEMMA_MODEL_PATH,
            torch_dtype=torch.float16,
            device_map=DEVICE_MAP,
            trust_remote_code=True
        )
        
        # Create pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        return HuggingFacePipeline(pipeline=pipe)
    except Exception as e:
        st.error(f"Error loading Gemma model: {e}")
        st.info("Please ensure the model path is correct and the model is properly downloaded.")
        return None

@st.cache_resource
def load_embedding_model():
    """Load the embedding model"""
    try:
        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_PATH,
            model_kwargs={'device': 'cuda' if USE_CUDA and torch.cuda.is_available() else 'cpu'}
        )
    except Exception as e:
        st.error(f"Error loading embedding model: {e}")
        return None

def get_local_llm():
    """Get the local LLM instance"""
    return load_gemma_model()

def get_local_embeddings():
    """Get the local embeddings instance"""
    return load_embedding_model() 