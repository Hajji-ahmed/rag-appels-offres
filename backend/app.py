from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from backend.rag_pipeline import generate_answer
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
from backend.index_pdf import main as index_pdfs
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(query: Query):
    answer = generate_answer(query.question)
    return {"answer": answer}

@app.post("/upload-and-index")
async def upload_and_index(file: UploadFile = File(...)):
    # Créer le dossier data s'il n'existe pas
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Sauvegarder le PDF
    file_location = data_dir / file.filename
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Lancer l'indexation
    try:
        stats = index_pdfs()
        return {
            "status": "success",
            "filename": file.filename,
            "stats": stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/list-pdfs")
async def list_pdfs():
    data_dir = Path("data")
    pdf_files = [f.name for f in data_dir.glob("*.pdf") if f.is_file()]
    return {"pdfs": pdf_files}