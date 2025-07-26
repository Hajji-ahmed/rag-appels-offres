import streamlit as st
import requests
from pathlib import Path
import os

# Configuration
BACKEND_URL = "http://localhost:8000"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.title("Système RAG - Appels d'Offres")

# Section Upload
with st.expander("📤 Importer un PDF"):
    uploaded_file = st.file_uploader("Choisir un fichier PDF", type="pdf")
    if uploaded_file:
        with st.spinner("Traitement en cours..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                response = requests.post(
                    f"{BACKEND_URL}/upload-and-index",
                    files=files,
                    timeout=120
                )
                if response.status_code == 200:
                    st.success("PDF indexé avec succès!")
                else:
                    st.error(f"Erreur: {response.text}")
            except Exception as e:
                st.error(f"Échec de l'upload: {str(e)}")

# Section Question
st.divider()
question = st.text_area("Posez votre question sur les appels d'offres")

if st.button("Envoyer"):
    if not question.strip():
        st.warning("Veuillez entrer une question")
    else:
        with st.spinner("Recherche de la réponse..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/ask",
                    json={"question": question},
                    timeout=300
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "answer" in data:
                            st.subheader("Réponse:")
                            st.write(data["answer"])
                        else:
                            st.error("Format de réponse inattendu")
                            st.json(data)
                    except ValueError:
                        st.error("Réponse non-JSON reçue:")
                        st.text(response.text)
                else:
                    st.error(f"Erreur {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de connexion: {str(e)}")
            except Exception as e:
                st.error(f"Erreur inattendue: {str(e)}")