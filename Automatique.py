import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="ExtracteurDeProduit", layout="wide")

st.title("Extracteur de Produits")
st.divider()

# --- GESTION GOOGLE SHEETS AVEC CACHE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def charger_entreprises():
    try:
        # On lit le sheet (l'URL est dans le secrets.toml)
        df = conn.read(worksheet="Feuille1", ttl=0)
        liste = df["Marque"].dropna().unique().tolist()
        liste.sort()
        return liste
    except Exception as e:
        st.error(f"Erreur Google Sheet: {e}")
        return ["ESSENTIAL", "MEXICANA"]

def sauvegarder_entreprises(liste):
    try:
        new_df = pd.DataFrame({"Marque": liste})
        conn.update(worksheet="Feuille1", data=new_df)
        # On vide le cache pour que la liste se mette à jour au prochain appel
        charger_entreprises.clear()
    except Exception as e:
        st.error(f"Erreur sauvegarde Sheet: {e}")

# --- GESTION DES FICHIERS JSON ---
SIDEBAR_FILE = "sidebar.json"

def charger_sidebar():
    if os.path.exists(SIDEBAR_FILE):
        with open(SIDEBAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "magasin": "REIMS", "saison": "", "origine": "", "ar": 1, "devise": "EUR", "poids": "0,7", "visible_web": 1
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
# Utilisation de la fonction cachée
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
        if choix in st.session_state.liste_entreprises:
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

    if st.button("Actualiser la liste", use_container_width=True):
        charger_entreprises.clear()
        st.rerun()

    date = st.text_input("Date (jj/mm/aaaa) :", value=datetime.now().strftime("%d/%m/%Y"))

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
