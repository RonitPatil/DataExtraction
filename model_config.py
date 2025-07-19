"""
Model Configuration for Local Gemma 3 4B Setup

Update the paths below to match your local model locations.
"""

# Update these paths to your actual model locations
GEMMA_MODEL_PATH = "gemma-2-4b"  # Path to your downloaded Gemma model
EMBEDDING_MODEL_PATH = "sentence-transformers/all-MiniLM-L6-v2"  # Lightweight embedding model

# Model settings
MAX_NEW_TOKENS = 512
TEMPERATURE = 0.7
EMBEDDING_DIMENSIONS = 384  # all-MiniLM-L6-v2 dimensions

# Device settings
USE_CUDA = True  # Set to False if you don't have CUDA
DEVICE_MAP = "auto"  # or "cpu" for CPU-only

"""
Example paths:
- Windows: "C:/Users/username/models/gemma-2-4b"
- Linux/Mac: "/home/username/models/gemma-2-4b"
- Relative: "./models/gemma-2-4b"

Make sure the model folder contains:
- config.json
- tokenizer.json
- pytorch_model.bin (or multiple .safetensors files)
- tokenizer_config.json
""" 