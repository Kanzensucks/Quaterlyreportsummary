"""
app/config.py
--------------
Centralised configuration for the Quarterly Report Summariser.
"""

import os

# Ollama server
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# Default model (can override in .env or CLI)
MODEL_DEFAULT = os.getenv("MODEL", "llama3.1:8b")

# Chunking configuration for POINTS
MAX_CHARS_DEFAULT = int(os.getenv("MAX_CHARS", "3000"))
OVERLAP_DEFAULT   = int(os.getenv("OVERLAP", "200"))

# Model behaviour
TEMPERATURE_DEFAULT = float(os.getenv("TEMPERATURE", "0.1"))
TIMEOUT_DEFAULT     = int(os.getenv("TIMEOUT", "60"))

# Prompt paths
PROMPT_PATH = os.getenv("POINTS_PROMPT", os.path.join("prompts", "points_prompt.txt"))
