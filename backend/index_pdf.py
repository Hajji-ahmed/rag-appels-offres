import os
from pathlib import Path
from PyPDF2 import PdfReader
from backend.rag_pipeline import get_chunks_from_pdf_text, embed_chunks, store_chunks_faiss
import logging
from datetime import datetime

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
        logger.info(f"Extraction du texte depuis {pdf_path.name}")
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {i+1} ---\n{page_text}\n\n"
        return text if text.strip() else None
    except Exception as e:
        logger.error(f"Erreur lecture {pdf_path.name}: {str(e)}")
        return None

def clean_old_index():
    """Nettoie les anciens fichiers d'index"""
    index_files = [
        BASE_DIR / "backend" / "faiss_index.index",
        BASE_DIR / "backend" / "docs.pkl"
    ]
    for f in index_files:
        if f.exists():
            try:
                f.unlink()
                logger.info(f"Ancien index supprimé: {f.name}")
            except Exception as e:
                logger.error(f"Échec suppression {f.name}: {str(e)}")

def main() -> dict:
    """Fonction principale d'indexation"""
    start_time = datetime.now()
    stats = {
        "total_files": 0,
        "processed_files": 0,
        "total_pages": 0,
        "total_chunks": 0,
        "duration": 0
    }

    try:
        if not DATA_DIR.exists():
            DATA_DIR.mkdir()
            logger.info(f"Création du dossier {DATA_DIR}")

        pdf_files = list(DATA_DIR.glob("*.pdf"))
        stats["total_files"] = len(pdf_files)
        
        if not pdf_files:
            logger.warning("Aucun PDF trouvé dans data/")
            return stats

        # Nettoyage de l'ancien index
        clean_old_index()

        # Traitement des PDFs
        all_text = ""
        for pdf_file in pdf_files:
            text = extract_text_from_pdf(pdf_file)
            if text:
                all_text += text + "\n\n"
                stats["processed_files"] += 1
                stats["total_pages"] += len(text.split("--- Page")) - 1

        if not all_text.strip():
            logger.error("Aucun texte valide extrait - vérifiez les PDFs")
            return stats

        # Indexation
        chunks = get_chunks_from_pdf_text(all_text)
        stats["total_chunks"] = len(chunks)
        
        embeddings = embed_chunks(chunks)
        store_chunks_faiss(chunks, embeddings)
        
        stats["duration"] = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Indexation réussie. {stats['processed_files']}/{stats['total_files']} fichiers, "
            f"{stats['total_pages']} pages, {stats['total_chunks']} chunks, "
            f"temps: {stats['duration']:.2f}s"
        )
        
        return stats

    except Exception as e:
        logger.error(f"Erreur lors de l'indexation: {str(e)}")
        raise

if __name__ == "__main__":
    main()