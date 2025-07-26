from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
from .index_pdf import main as index_pdfs
from .rag_pipeline import generate_answer
import logging
from datetime import datetime
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API RAG pour Appels d'Offres",
              description="API pour le système RAG utilisant Mistral via Ollama")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

@app.on_event("startup")
async def startup_event():
    """Vérifications au démarrage"""
    logger.info("Démarrage de l'application")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Vérifier l'accès à Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            logger.warning("Ollama ne semble pas fonctionner correctement")
    except Exception as e:
        logger.error(f"Erreur de connexion à Ollama: {str(e)}")

@app.post("/ask", summary="Poser une question", response_description="La réponse générée")
async def ask_question(query: Query, request: Request):
    """
    Pose une question sur les appels d'offres et retourne une réponse générée par Mistral.
    """
    logger.info(f"Question reçue: {query.question}")
    start_time = datetime.now()
    
    try:
        answer = generate_answer(query.question)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Réponse générée en {processing_time:.2f}s")
        request.app.state.last_processing_time = processing_time
        
        return {
            "answer": answer,
            "processing_time": processing_time,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Erreur lors du traitement de la question",
                "error": str(e),
                "status": "error"
            }
        )

@app.post("/upload-and-index", summary="Uploader et indexer un PDF")
async def upload_and_index(file: UploadFile = File(...)):
    """
    Upload un fichier PDF et lance son indexation dans le système RAG.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Seuls les fichiers PDF sont acceptés"
        )

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    file_location = data_dir / file.filename
    
    try:
        # Sauvegarde du fichier
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Fichier {file.filename} sauvegardé avec succès")

        # Indexation
        stats = index_pdfs()
        
        return {
            "status": "success",
            "filename": file.filename,
            "stats": stats,
            "message": "Fichier uploadé et indexé avec succès"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload/indexation: {str(e)}")
        # Nettoyage en cas d'erreur
        if file_location.exists():
            file_location.unlink()
            
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Erreur lors du traitement du fichier",
                "error": str(e),
                "status": "error"
            }
        )

@app.get("/list-pdfs", summary="Lister les PDFs disponibles")
async def list_pdfs():
    """Retourne la liste des PDFs disponibles dans le système"""
    try:
        pdf_files = sorted([
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "last_modified": f.stat().st_mtime
            }
            for f in Path("data").glob("*.pdf")
        ], key=lambda x: x["last_modified"], reverse=True)
        
        return {
            "status": "success",
            "count": len(pdf_files),
            "pdfs": pdf_files
        }
    except Exception as e:
        logger.error(f"Erreur list_pdfs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Erreur lors de la liste des PDFs",
                "error": str(e),
                "status": "error"
            }
        )

@app.get("/system-status", summary="Statut du système")
async def system_status():
    """Retourne des informations sur l'état du système"""
    try:
        from .rag_pipeline import load_faiss
        index, docs = load_faiss()
        
        return {
            "status": "success",
            "index_size": len(docs),
            "last_processing_time": getattr(app.state, "last_processing_time", None),
            "system_health": "ok"
        }
    except Exception as e:
        logger.warning(f"Erreur système: {str(e)}")
        return {
            "status": "warning",
            "message": "Problème détecté dans le système",
            "error": str(e)
        }

# Gestion des erreurs globales
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Erreur interne du serveur",
            "error": str(exc),
            "status": "error"
        }
    )