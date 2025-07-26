import os
from pathlib import Path
from PyPDF2 import PdfReader
import logging
from datetime import datetime
from .rag_pipeline import get_chunks_from_pdf_text, embed_chunks, store_chunks_faiss

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrait le texte brut d'un fichier PDF"""
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text if text.strip() else None
    except Exception as e:
        logger.error(f"Erreur lecture PDF: {str(e)}")
        return None

def clean_old_index():
    """Nettoie les anciens fichiers d'index"""
    index_files = [
        BASE_DIR / "backend" / "faiss_index.index",
        BASE_DIR / "backend" / "docs.pkl"
    ]
    for f in index_files:
        if f.exists():
            f.unlink()

def main() -> dict:
    """Fonction principale d'indexation"""
    start_time = datetime.now()
    stats = {"total_files": 0, "processed_files": 0, "total_pages": 0, "total_chunks": 0}

    # Création dossier data si inexistant
    DATA_DIR.mkdir(exist_ok=True)

    pdf_files = list(DATA_DIR.glob("*.pdf"))
    stats["total_files"] = len(pdf_files)

    if not pdf_files:
        logger.warning("Aucun PDF trouvé dans data/")
        return stats

    clean_old_index()
    all_text = ""
    
    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        if text:
            all_text += text + "\n\n"
            stats["processed_files"] += 1
            stats["total_pages"] += len(text.split("\n")) // 50  # Estimation

    chunks = get_chunks_from_pdf_text(all_text)
    stats["total_chunks"] = len(chunks)
    
    embeddings = embed_chunks(chunks)
    store_chunks_faiss(chunks, embeddings)
    
    stats["duration"] = (datetime.now() - start_time).total_seconds()
    return stats

if __name__ == "__main__":
    main()