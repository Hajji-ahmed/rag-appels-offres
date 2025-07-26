import faiss
import pickle
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import os
from pathlib import Path
import logging
import requests

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation
model = SentenceTransformer("all-MiniLM-L6-v2")
OLLAMA_URL = "http://localhost:11434"

# Chemins
CURRENT_DIR = Path(__file__).parent
INDEX_PATH = str(CURRENT_DIR / "faiss_index.index")
DOCS_PATH = str(CURRENT_DIR / "docs.pkl")

def get_chunks_from_pdf_text(text):
    """Découpe le texte en chunks optimisés pour RAG"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    return splitter.split_text(text)

def embed_chunks(chunks):
    """Génère les embeddings des chunks de texte"""
    return model.encode(chunks).astype("float32")

def store_chunks_faiss(chunks, embeddings):
    """Stocke les chunks et embeddings dans FAISS"""
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, INDEX_PATH)
    with open(DOCS_PATH, "wb") as f:
        pickle.dump(chunks, f)

def load_faiss():
    """Charge l'index FAISS et les documents"""
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(f"Fichier d'index FAISS introuvable: {INDEX_PATH}")
    index = faiss.read_index(INDEX_PATH)
    with open(DOCS_PATH, "rb") as f:
        docs = pickle.load(f)
    return index, docs

def search_similar_chunks(query, top_k=5):
    """Recherche les chunks les plus pertinents"""
    index, docs = load_faiss()
    query_vector = model.encode([query]).astype("float32")
    _, indices = index.search(query_vector, top_k)
    return [docs[i] for i in indices[0]]

def query_mistral(prompt):
    """Envoie une requête à Mistral via Ollama"""
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "mistral:instruct",
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    return response.json().get("response")

def generate_answer(question):
    """Génère une réponse avec Mistral"""
    context_chunks = search_similar_chunks(question)
    context = "\n".join(context_chunks)
    
    prompt = f"""
    [INST] Vous êtes un assistant expert en appels d'offres.
    Contexte pertinent:
    {context}

    Question: {question}
    Réponse détaillée: [/INST]
    """
    
    return query_mistral(prompt)