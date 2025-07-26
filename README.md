## 1. Présentation du projet

Ce projet consiste à créer un système de question-réponse intelligent basé sur des documents PDF d'appels d’offres. Il permet de téléverser un fichier PDF, de le traiter via un pipeline RAG (Retrieval-Augmented Generation), et de poser des questions en langage naturel pour obtenir des réponses précises et sourcées.

Le système repose sur :

* L’extraction de texte et découpage en chunks.
* La vectorisation avec Sentence Transformers.
* L’indexation locale avec FAISS.
* La génération de réponses contextuelles via Gemini API.

## 2. Fonctionnalités principales

* Téléversement de fichiers PDF d’appels d’offres.
* Extraction et découpage du contenu des documents.
* Indexation des données sous forme vectorielle.
* Recherche des passages pertinents.
* Génération de réponse via un LLM (Gemini).
* API REST avec FastAPI.
* Interface utilisateur avec Streamlit.
* Suppression dynamique de fichiers.

## 3. Architecture technique

```
[Streamlit] ---> [FastAPI Backend] ---> [FAISS + Embeddings] ---> [Gemini LLM]
                                    ↘
                                 [PDF Loader + Chunker]
```

## 4. Structure du projet

```
projet-rag-tecforge/
├── backend/                 # API FastAPI et logique RAG
│   ├── app.py
│   └── rag_pipeline.py
├── frontend/                # Interface Streamlit
│   └── streamlit_app.py
├── data/                    # Fichiers PDF stockés localement
├── .env                     # Clés et variables secrètes
├── config.py                # Configuration globale
├── requirements.txt         # Dépendances
└── README.md
```

## 5. Installation

### Prérequis

* Python 3.10 ou supérieur
* pip

### Étapes d’installation

```bash
git clone https://github.com/ton-compte/projet-rag-tecforge.git
cd projet-rag-tecforge
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

Créer un fichier `.env` à la racine :

```
GEMINI_API_KEY=your_gemini_api_key_here
```

## 6. Lancement du projet

### Démarrer le backend (FastAPI)

```bash
uvicorn backend.app:app --reload --port 8000
```

### Démarrer le frontend (Streamlit)

```bash
streamlit run frontend/streamlit_app.py
```

## 7. Utilisation

1. Téléverser un PDF via l’interface.
2. Indexer le fichier.
3. Poser une question sur le contenu.
4. Obtenir une réponse générée automatiquement.

## 8. Technologies utilisées

| Technologie           | Rôle                                 |
| --------------------- | ------------------------------------ |
| FastAPI               | API REST                             |
| Streamlit             | Interface utilisateur web            |
| FAISS                 | Indexation vectorielle locale        |
| Sentence Transformers | Génération d’embeddings              |
| Gemini API            | Génération de réponses               |
| LangChain             | Pipeline de question-réponse         |
| PyMuPDF / pdfplumber  | Extraction de texte des fichiers PDF |


