import streamlit as st
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="ExtracteurDeProduit", layout="wide")

st.title("Extracteur de Produits")
st.divider()

# --- GESTION DU FICHIER JSON ---
DB_FILE = "marques.json"

def charger_entreprises():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        initiales = ["ESSENTIAL", "MEXICANA"]
        initiales.sort()
        sauvegarder_entreprises(initiales)
        return initiales

def sauvegarder_entreprises(liste):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

def est_numerique(valeur):
    if not valeur: return False
    temp = str(valeur).replace(',', '.')
    return temp.replace('.', '', 1).isdigit()

# --- INITIALISATION SESSION STATE ---
if "liste_entreprises" not in st.session_state:
    st.session_state.liste_entreprises = charger_entreprises()

# --- DIALOGUES (MODALS) ---
@st.dialog("Ajouter une entreprise")
def ajouter_entreprise_dialog():
    nouveau_nom = st.text_input("Nom de la nouvelle entreprise :").upper()
    if st.button("Enregistrer l'entreprise", use_container_width=True):
        if nouveau_nom:
            if nouveau_nom not in st.session_state.liste_entreprises:
                st.session_state.liste_entreprises.append(nouveau_nom)
                st.session_state.liste_entreprises.sort()
                sauvegarder_entreprises(st.session_state.liste_entreprises)
                st.rerun()
            else:
                st.error("Cette entreprise existe déjà.")

@st.dialog("Supprimer une entreprise")
def supprimer_entreprise_dialog():
    st.write("Choisissez l'entreprise à retirer :")
    choix = st.selectbox("Entreprise à supprimer", options=st.session_state.liste_entreprises)
    st.warning(f"Confirmez-vous la suppression de '{choix}' ?")
    if st.button("Confirmer la suppression", use_container_width=True):
        st.session_state.liste_entreprises.remove(choix)
        sauvegarder_entreprises(st.session_state.liste_entreprises)
        st.rerun()

# --- SIDEBAR : PARAMÈTRES ---
with st.sidebar:
    st.header("Paramètres")
    Magasin = st.text_input("Code Magasin :", value="REIMS").upper()

    NOM_COLLECTION = st.selectbox("Nom de la Marque :", 
                                  options=st.session_state.liste_entreprises, 
                                  index=None, 
                                  placeholder="Choisissez une marque")

    col_ent1, col_ent2 = st.columns(2)
    with col_ent1:
        if st.button("+ Ajouter", use_container_width=True):
            ajouter_entreprise_dialog()
    with col_ent2:
        if st.button("- Supprimer", use_container_width=True):
            supprimer_entreprise_dialog()

    dateAjd = datetime.now().strftime("%d/%m/%Y")
    date = st.text_input("Date (jj/mm/aaaa) :", value = dateAjd)
    famille = st.text_input("Famille :", placeholder = "Entrez la famille").upper()
    saison = st.text_input("Saison :", placeholder = "Entrez la saison").upper()
    origine = st.text_input("Origine :", placeholder = "Entrez l'origine").upper()
    
    st.divider()
    AR = st.number_input("Indicateur AR (0/1):", min_value=0, max_value=1, value=1)
    Devise = st.text_input("Devise :", value="EUR").upper()
    Poids = st.text_input("Poids :", value="0,7").upper()
    
    if Poids and not est_numerique(Poids):
        st.error("Le Poids doit être un nombre.")

    VisibleWeb = st.number_input("Visible Web (0/1):", min_value=0, max_value=1, value=1)

# --- ZONE DE TÉLÉCHARGEMENT ---
ok = False
if not famille or not Magasin or not origine or not AR or not VisibleWeb or not Devise or not Poids or not date or not NOM_COLLECTION:
    ok = True
uploaded_file = st.file_uploader("Choisissez votre fichier PDF", type="pdf", disabled = ok)

if uploaded_file:
    st.success("Fichier prit en considération")
  