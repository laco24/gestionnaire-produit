import streamlit as st
import pandas as pd
import re
import copy
import json
import os
from datetime import datetime

st.set_page_config(page_title="GestionnaireDeProduit", layout="wide")

st.title("Gestionnaire de Produits")

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

# --- FONCTION DE VALIDATION NUMÉRIQUE ---
def est_numerique(valeur, autoriser_etoile=False):
    if not valeur:
        return False
    # On nettoie la valeur (virgule -> point)
    temp = str(valeur).replace(',', '.')
    if autoriser_etoile:
        temp = temp.replace('*', '')
    
    # On vérifie si c'est un nombre (en enlevant le point décimal une fois)
    return temp.replace('.', '', 1).isdigit()

# --- GESTION DU SESSION STATE ---
if "liste_produits_manuels" not in st.session_state:
    st.session_state.liste_produits_manuels = []

if "liste_entreprises" not in st.session_state:
    st.session_state.liste_entreprises = charger_entreprises()

# --- FONCTIONS DE GESTION PRODUITS ---
def ajouter_produit():
    st.session_state.liste_produits_manuels.append({
        "modele": "", "barcode": "", "couleur": "", "matiere": "",
        "prix_achat": "", "prix_ttc": "", "designation": "", "ssfamille": "",
        "stocks": [{"taille": "", "qte": 1}] 
    })

def supprimer_produit():
    if st.session_state.liste_produits_manuels:
        st.session_state.liste_produits_manuels.pop()

def ajouter_taille(index_produit):
    st.session_state.liste_produits_manuels[index_produit]["stocks"].append({"taille": "", "qte": 1})

def supprimer_taille(index_produit):
    if len(st.session_state.liste_produits_manuels[index_produit]["stocks"]) > 1:
        st.session_state.liste_produits_manuels[index_produit]["stocks"].pop()

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
                st.success(f"'{nouveau_nom}' ajouté avec succès.")
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

@st.dialog("Copier un produit existant")
def copier_produit_dialog():
    if not st.session_state.liste_produits_manuels:
        st.write("Aucun produit à copier.")
        return
    options = [f"{idx+1}. {p['modele'] or 'Sans nom'}" for idx, p in enumerate(st.session_state.liste_produits_manuels)]
    choix = st.selectbox("Produit à dupliquer", options)
    index = options.index(choix)
    if st.button("Confirmer la copie", use_container_width=True):
        st.session_state.liste_produits_manuels.append(copy.deepcopy(st.session_state.liste_produits_manuels[index]))
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
    rayon = st.text_input("Rayon :", placeholder = "Entrez le rayon").upper()
    origine = st.text_input("Origine :", placeholder = "Entrez l'origine").upper()
    
    st.divider()
    AR = st.number_input("Indicateur AR (0/1):", min_value=0, max_value=1, value=1)
    Devise = st.text_input("Devise :", value="EUR").upper()
    Poids = st.text_input("Poids :", value="0,7").upper()
    
    # Validation visuelle immédiate pour le poids
    if Poids and not est_numerique(Poids):
        st.error("Le Poids doit être un nombre.")

    VisibleWeb = st.number_input("Visible Web (0/1):", min_value=0, max_value=1, value=1)

# --- SAISIES GÉNÉRALES ---
st.subheader("Liste des produits")

for i, produit in enumerate(st.session_state.liste_produits_manuels):
    with st.expander(f"Produit n°{i+1} : {produit['modele'] or 'Nouveau Produit'}", expanded=True):
        c1, c2 = st.columns(2)
        produit["modele"] = c1.text_input("Modèle", value=produit["modele"], key=f"mod_{i}").upper()
        produit["barcode"] = c2.text_input("Code Barre", value=produit["barcode"], key=f"bar_{i}").upper()
        
        c3, c4 = st.columns(2)
        produit["couleur"] = c3.text_input("Couleur", value=produit["couleur"], key=f"coul_{i}").upper()
        produit["matiere"] = c4.text_input("Matière", value=produit["matiere"], key=f"mat_{i}").upper()
        
        c5, c6 = st.columns(2)
        produit["prix_achat"] = c5.text_input("Prix Achat", value=produit["prix_achat"], key=f"p_ach_{i}")
        produit["prix_ttc"] = c6.text_input("Prix TTC ou Coefficient (*)", value=produit["prix_ttc"], key=f"p_ttc_{i}")

        # Alertes visuelles pour les prix
        if produit["prix_achat"] and not est_numerique(produit["prix_achat"]):
            st.error("Le Prix d'Achat doit être un nombre.")
        if produit["prix_ttc"] and not est_numerique(produit["prix_ttc"], autoriser_etoile=True):
            st.error("Le Prix TTC doit être un nombre (ou commencer par *).")

        c7, c8 = st.columns(2)
        produit["designation"] = c7.text_input("Designation (facultatif) :", value = produit["designation"], key=f"desi_{i}").upper()
        produit["ssfamille"] = c8.text_input("Sous Famille :", value = produit["ssfamille"], key=f"ssfam_{i}").upper()

        st.markdown("**Tailles et Quantités**")
        cb1, cb2 = st.columns(2)
        with cb1:
            if st.button(f" + Ajouter une taille", key=f"btn_size_{i}"):
                ajouter_taille(i); st.rerun()
        with cb2:
            if st.button(f" - Supprimer dernière taille", key=f"btn_del_size_{i}"):
                supprimer_taille(i); st.rerun()

        for j, stock in enumerate(produit["stocks"]):
            col_t, col_q = st.columns([2, 1])
            stock["taille"] = col_t.text_input(f"Taille", value=stock["taille"], key=f"size_{i}_{j}")
            stock["qte"] = col_q.number_input(f"Quantité", value=stock["qte"], key=f"qte_{i}_{j}")

st.divider()
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    if st.button("AJOUTER UN NOUVEAU PRODUIT", use_container_width=True):
        ajouter_produit(); st.rerun()
with col_p2:
    if st.button("COPIER UN PRODUIT", use_container_width=True):
        copier_produit_dialog()
with col_p3:
    if st.button("SUPPRIMER LE DERNIER PRODUIT", use_container_width=True):
        supprimer_produit(); st.rerun()

st.divider()

# --- VÉRIFICATION GLOBALE AVANT EXPORT ---
# 1. Vérification des paramètres sidebar + validité numérique du Poids
poids_valide = est_numerique(Poids)
params_remplis = all([Magasin, NOM_COLLECTION, famille, Devise, Poids, date, saison, rayon, origine]) and poids_valide

produits_valides = True
if not st.session_state.liste_produits_manuels:
    produits_valides = False
else:
    for p in st.session_state.liste_produits_manuels:
        champs_p = [p["modele"], p["barcode"], p["couleur"], p["matiere"], p["prix_achat"], p["prix_ttc"], p["ssfamille"]]
        # Vérification champs vides
        if any(v == "" or v is None for v in champs_p):
            produits_valides = False
            break
        # Vérification numérique des prix
        if not est_numerique(p["prix_achat"]) or not est_numerique(p["prix_ttc"], autoriser_etoile=True):
            produits_valides = False
            break
        # Vérification des tailles
        if any(s["taille"] == "" for s in p["stocks"]):
            produits_valides = False
            break

ok = params_remplis and produits_valides

# --- GESTION EXPORT .TXT ---
if st.button("GÉNÉRER LE FICHIER .TXT", disabled=not ok, use_container_width=True):
    lignes_finales = []
    for produit in st.session_state.liste_produits_manuels:
        pa = produit["prix_achat"]
        pttc = produit["prix_ttc"]
        
        if "*" in pttc:
            try:
                pa_entier = float(pa.replace(",", "."))
                coeff = float(pttc.replace("*", "").replace(",", "."))
                valeur_calculee = pa_entier * coeff
                pttc_final = str(int(valeur_calculee))
            except:
                pttc_final = pttc
        else:
            pttc_final = pttc

        designation = produit["designation"] if produit["designation"] else produit["ssfamille"]

        for stock in produit["stocks"]:
            try:
                qte_val = int(stock["qte"])
            except:
                qte_val = 0

            if qte_val > 0:
                for _ in range(qte_val):
                    data_row = [
                        Magasin, NOM_COLLECTION, date, origine, famille, saison, produit["barcode"], designation,
                        produit["matiere"], produit["couleur"], stock["taille"], pa, pttc_final, "1", "",
                        produit["ssfamille"], rayon, produit["modele"], "", "", "", "", "", "", "\t",
                        str(AR), Devise, "", Poids, "", "","","","","","","","","\t", str(VisibleWeb),
                        "","","","","","","","","","","","","","","","\t"
                    ]
                    lignes_finales.append("\t".join(data_row))

    if lignes_finales:
        st.success(f"Export réussi : {len(lignes_finales)} lignes.")
        st.download_button("Télécharger l'export .txt", "\n".join(lignes_finales), f"export_{NOM_COLLECTION}.txt")
    else:
        st.error("Aucune ligne générée.")
