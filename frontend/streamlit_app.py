import streamlit as st
import requests
from pathlib import Path
import time
import os

# Configuration
st.set_page_config(page_title="Système RAG - Appels d'Offres", layout="wide")
BACKEND_URL = "http://127.0.0.1:8000"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# CSS personnalisé pour thème moderne
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Segoe UI', sans-serif;
            background-color: #f4f6f8;
        }

        .stApp {
            background-color: #f4f6f8;
        }

        .block-container {
            padding: 2rem 2rem 1rem;
            max-width: 900px;
            margin: auto;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }

        .stButton>button {
            background-color: #0052cc;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1.5em;
            border: none;
        }

        .stButton>button:hover {
            background-color: #003d99;
        }

        .stDownloadButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
        }

        .stDownloadButton>button:hover {
            background-color: #45a049;
        }

        .pdf-card {
            padding: 0.75em;
            margin-bottom: 1em;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

st.title("Système RAG pour Appels d'Offres")

# === 1. Upload PDF ===
with st.expander("Importer un nouveau fichier PDF", expanded=True):
    uploaded_file = st.file_uploader("Téléverser un fichier PDF", type="pdf")

    if uploaded_file is not None:
        temp_path = DATA_DIR / uploaded_file.name
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"Fichier {uploaded_file.name} prêt pour indexation")
        with open(temp_path, "rb") as f:
            st.download_button("Télécharger ce fichier", f, file_name=uploaded_file.name)

        if st.button("Indexer le PDF"):
            with st.spinner("Indexation en cours..."):
                try:
                    files = {"file": (uploaded_file.name, open(temp_path, "rb"), "application/pdf")}
                    response = requests.post(f"{BACKEND_URL}/upload-and-index", files=files, timeout=120)
                    if response.status_code == 200 and response.json().get("status") == "success":
                        st.success("Indexation réussie")
                        st.json(response.json().get("stats"))
                    else:
                        st.error(f"Erreur: {response.json().get('message')}")
                except Exception as e:
                    st.error(f"Échec de l'indexation: {str(e)}")
                finally:
                    if 'files' in locals():
                        files['file'][1].close()

# === 2. PDFs Existants ===
with st.expander("Fichiers PDF déjà indexés"):
    try:
        response = requests.get(f"{BACKEND_URL}/list-pdfs")
        if response.status_code == 200:
            pdfs = response.json().get("pdfs", [])
            if pdfs:
                for pdf in pdfs:
                    with st.container():
                        st.markdown(f"""
                            <div class='pdf-card'>
                                <strong>{pdf}</strong>
                                <form action="" method="post">
                                    <input type="hidden" name="filename" value="{pdf}">
                                    <button onclick="window.location.reload();" style="float: right; background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 6px;">Supprimer</button>
                                </form>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Aucun PDF disponible.")
        else:
            st.error("Erreur lors de la récupération des fichiers.")
    except Exception as e:
        st.error(f"Connexion au serveur échouée: {str(e)}")

# === 3. Zone de Question ===
st.markdown("---")
st.subheader("Poser une question ")
question = st.text_area("Entrez votre question ici...", height=100)

if st.button("Envoyer la question"):
    if question.strip():
        with st.spinner("Recherche en cours..."):
            try:
                response = requests.post(f"{BACKEND_URL}/ask", json={"question": question}, timeout=30)
                if response.status_code == 200:
                    st.success("Réponse générée avec succès")
                    st.markdown("#### Réponse :")
                    st.write(response.json().get("answer", "Pas de réponse disponible."))
                else:
                    st.error(f"Erreur serveur: {response.text}")
            except Exception as e:
                st.error(f"Connexion au backend échouée: {str(e)}")
    else:
        st.warning("Veuillez entrer une question avant d’envoyer.")
