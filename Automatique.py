import streamlit as st
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="ExtracteurDeProduit", layout="wide")

st.title("Extracteur de Produits")
st.divider()

# --- GESTION DES FICHIERS JSON ---
DB_FILE = "marques.json"
SIDEBAR_FILE = "sidebar.json"

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

def charger_sidebar():
    if os.path.exists(SIDEBAR_FILE):
        with open(SIDEBAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "magasin": "REIMS", "date": datetime.now().strftime("%d/%m/%Y"),
        "saison": "", "origine": "", "ar": 1, "devise": "EUR", "poids": "0,7", "visible_web": 1
    }

def sauvegarder_sidebar(cle, valeur):
    config = charger_sidebar()
    config[cle] = valeur
    with open(SIDEBAR_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def est_numerique(valeur):
    if not valeur: return False
    temp = str(valeur).replace(',', '.')
    return temp.replace('.', '', 1).isdigit()

# --- INITIALISATION SESSION STATE ---
if "liste_entreprises" not in st.session_state:
    st.session_state.liste_entreprises = charger_entreprises()

config_side = charger_sidebar()

# --- DIALOGUES ---
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

@st.dialog("Supprimer une entreprise")
def supprimer_entreprise_dialog():
    choix = st.selectbox("Entreprise à supprimer", options=st.session_state.liste_entreprises)
    if st.button("Confirmer la suppression", use_container_width=True):
        st.session_state.liste_entreprises.remove(choix)
        sauvegarder_entreprises(st.session_state.liste_entreprises)
        st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Paramètres")
    
    Magasin = st.text_input("Code Magasin :", value=config_side["magasin"]).upper()
    if Magasin != config_side["magasin"]: sauvegarder_sidebar("magasin", Magasin)

    NOM_COLLECTION = st.selectbox("Nom de la Marque :", 
                                  options=st.session_state.liste_entreprises, 
                                  index=None, placeholder="Choisissez une marque")

    col1, col2 = st.columns(2)
    with col1: 
        if st.button("+ Ajouter", use_container_width=True): ajouter_entreprise_dialog()
    with col2: 
        if st.button("- Supprimer", use_container_width=True): supprimer_entreprise_dialog()

    date = st.text_input("Date (jj/mm/aaaa) :", value=config_side["date"])
    if date != config_side["date"]: sauvegarder_sidebar("date", date)

    saison = st.text_input("Saison :", value=config_side["saison"],placeholder = "Entrez la saison").upper()
    if saison != config_side["saison"]: sauvegarder_sidebar("saison", saison)

    origine = st.text_input("Origine :", value=config_side["origine"], placeholder = "Entrez l'origine").upper()
    if origine != config_side["origine"]: sauvegarder_sidebar("origine", origine)
    
    st.divider()
    AR = st.number_input("Indicateur AR (0/1):", 0, 1, value=int(config_side["ar"]))
    if AR != config_side["ar"]: sauvegarder_sidebar("ar", AR)

    Devise = st.text_input("Devise :", value=config_side["devise"]).upper()
    if Devise != config_side["devise"]: sauvegarder_sidebar("devise", Devise)

    Poids = st.text_input("Poids :", value=config_side["poids"])
    if Poids != config_side["poids"]: sauvegarder_sidebar("poids", Poids)
    
    if Poids and not est_numerique(Poids): st.error("Le Poids doit être un nombre.")

    VisibleWeb = st.number_input("Visible Web (0/1):", 0, 1, value=int(config_side["visible_web"]))
    if VisibleWeb != config_side["visible_web"]: sauvegarder_sidebar("visible_web", VisibleWeb)

# --- ZONE DE TÉLÉCHARGEMENT ---
champs_obligatoires = [Magasin, origine, date, NOM_COLLECTION]
ok = any(v == "" or v is None for v in champs_obligatoires)
uploaded_file = st.file_uploader("Choisissez votre fichier PDF", type="pdf", disabled=ok)

if uploaded_file:
    st.success("Fichier pris en considération")
