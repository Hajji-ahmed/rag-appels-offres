import faiss
import pickle
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import GEMINI_API_KEY, EMBEDDING_MODEL
import numpy as np
import os
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation
model = SentenceTransformer(EMBEDDING_MODEL)
genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

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
    try:
        logger.info(f"Génération des embeddings pour {len(chunks)} chunks")
        return model.encode(chunks).astype("float32")
    except Exception as e:
        logger.error(f"Erreur lors de l'embedding: {str(e)}")
        raise

def store_chunks_faiss(chunks, embeddings):
    """Stocke les chunks et embeddings dans FAISS"""
    try:
        # Création de l'index FAISS
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        # Sauvegarde
        faiss.write_index(index, INDEX_PATH)
        with open(DOCS_PATH, "wb") as f:
            pickle.dump(chunks, f)
        
        logger.info(f"Index sauvegardé avec {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde FAISS: {str(e)}")
        raise

def load_faiss():
    """Charge l'index FAISS et les documents"""
    try:
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(f"Index FAISS introuvable: {INDEX_PATH}")
        if not os.path.exists(DOCS_PATH):
            raise FileNotFoundError(f"Documents introuvables: {DOCS_PATH}")
        
        index = faiss.read_index(INDEX_PATH)
        with open(DOCS_PATH, "rb") as f:
            docs = pickle.load(f)
        
        logger.info(f"Index chargé avec {len(docs)} documents")
        return index, docs
    except Exception as e:
        logger.error(f"Erreur lors du chargement FAISS: {str(e)}")
        raise

def search_similar_chunks(query, top_k=5):
    """Recherche les chunks les plus pertinents"""
    try:
        index, docs = load_faiss()
        query_embedding = model.encode([query]).astype("float32")
        distances, indices = index.search(query_embedding, top_k)
        
        # Filtrage par similarité (seuil optionnel)
        relevant_chunks = [docs[i] for i in indices[0]]
        logger.info(f"Trouvé {len(relevant_chunks)} chunks pertinents")
        return relevant_chunks
    except Exception as e:
        logger.error(f"Erreur de recherche: {str(e)}")
        raise

def generate_answer(question):
    """Génère une réponse à partir des chunks pertinents"""
    try:
        context_chunks = search_similar_chunks(question)
        context = "\n\n".join(context_chunks)
        
        prompt = f"""
        Vous êtes un assistant expert en appels d'offres.
        Contexte pertinent:
        {context}
        
        Question: {question}
        Réponse détaillée:
        """
        
        response = gemini.generate_content(prompt)
        logger.info("Réponse générée avec succès")
        return response.text
    except Exception as e:
        logger.error(f"Erreur de génération: {str(e)}")
        return "Désolé, une erreur s'est produite lors du traitement de votre question."