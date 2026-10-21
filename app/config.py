"""
Configuration management for the Self-Evaluating Lesson Content Generator.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "prompts"
OUTPUTS_DIR = BASE_DIR / "outputs"
DOCS_DIR = BASE_DIR / "docs"

# Data file paths
REFERENCES_FILE = DATA_DIR / "references.md"
MEMORY_FILE = DATA_DIR / "memory.json"
SQLITE_DB_PATH = DATA_DIR / "history.db"

# Prompts file paths
GENERATION_PROMPT_FILE = PROMPTS_DIR / "generation_prompt.md"
EVALUATION_PROMPT_FILE = PROMPTS_DIR / "evaluation_prompt.md"
REGENERATION_PROMPT_FILE = PROMPTS_DIR / "regeneration_prompt.md"

# System defaults
DEFAULT_TOPIC = "Introduction to RAG (Retrieval-Augmented Generation)"
MAX_RETRIES = 2  # Max retries after initial generation (Initial + Retry 1 + Retry 2 = 3 versions max)
DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# Target learner profile
TARGET_AUDIENCE = {
    "education": "Completed Class 12 in India",
    "language": "English as a second language, limited technical vocabulary",
    "background": "No prior knowledge of AI, ML, or RAG",
    "style": "Short sentences, familiar everyday examples, zero unexplained jargon"
}
