import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import copy
import json
import os
import re
import unicodedata
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="GestionnaireDeProduit", layout="wide")

st.title("Gestionnaire de Produits")

# --- FONCTION DE NETTOYAGE DES CARACTÈRES ---
def nettoyer_texte(texte):
    if not texte or not isinstance(texte, str):
        return texte
    # 1. On retire les accents (Normalisation NFD)
    texte_sans_accents = ''.join(
        c for c in unicodedata.normalize('NFD', texte)
        if unicodedata.category(c) != 'Mn'
    )
    # 2. On retire tout ce qui n'est pas lettre, chiffre ou espace
    texte_propre = re.sub(r'[^a-zA-Z0-9\s]', '', texte_sans_accents)
    return texte_propre.strip()

# --- GESTION GOOGLE SHEETS AVEC CACHE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def charger_entreprises():
    try:
        df = conn.read(worksheet="Feuille1", ttl=0)
        liste = df["Marque"].dropna().unique().tolist()
        liste.sort()
        return liste
    except Exception as e:
        st.error(f"Erreur lecture Sheet: {e}")
        return ["ESSENTIAL", "MEXICANA"]

def sauvegarder_entreprises(liste):
    try:
        new_df = pd.DataFrame({"Marque": liste})
        conn.update(worksheet="Feuille1", data=new_df)
        charger_entreprises.clear()
    except Exception as e:
        st.error(f"Erreur écriture Sheet: {e}")

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

def est_numerique(valeur, autoriser_etoile=False):
    if not valeur: return False
    temp = str(valeur).replace(',', '.')
    if autoriser_etoile: temp = temp.replace('*', '')
    return temp.replace('.', '', 1).isdigit()

# --- INITIALISATION SESSION STATE ---
if "liste_produits_manuels" not in st.session_state:
    st.session_state.liste_produits_manuels = []

st.session_state.liste_entreprises = charger_entreprises()
config_side = charger_sidebar()

# --- FONCTIONS DE GESTION PRODUITS ---
def ajouter_produit():
    st.session_state.liste_produits_manuels.append({
        "modele": "", "couleur": "", "matiere": "",
        "prix_achat": "", "prix_ttc": "", "designation": "", 
        "ssfamille": "", "rayon": "", "famille": "",
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
                st.success(f"'{nouveau_nom}' ajouté.")
                st.rerun()
            else: st.error("Existe déjà.")

@st.dialog("Supprimer une entreprise")
def supprimer_entreprise_dialog():
    choix = st.selectbox("Entreprise à supprimer", options=st.session_state.liste_entreprises)
    if st.button("Confirmer la suppression", use_container_width=True):
        if choix in st.session_state.liste_entreprises:
            st.session_state.liste_entreprises.remove(choix)
            sauvegarder_entreprises(st.session_state.liste_entreprises)
            st.rerun()

@st.dialog("Copier un produit existant")
def copier_produit_dialog():
    if not st.session_state.liste_produits_manuels:
        st.write("Aucun produit à copier."); return
    options = [f"{idx+1}. {p['modele'] or 'Sans nom'}" for idx, p in enumerate(st.session_state.liste_produits_manuels)]
    choix = st.selectbox("Produit à dupliquer", options)
    index = options.index(choix)
    if st.button("Confirmer la copie", use_container_width=True):
        st.session_state.liste_produits_manuels.append(copy.deepcopy(st.session_state.liste_produits_manuels[index]))
        st.rerun()

@st.dialog("Vider la liste")
def vider_liste_dialog():
    st.warning("Êtes-vous sûr de vouloir supprimer tous les produits ?")
    col1, col2 = st.columns(2)
    if col1.button("Oui, tout supprimer", use_container_width=True, type="primary"):
        st.session_state.liste_produits_manuels = []
        st.rerun()
    if col2.button("Annuler", use_container_width=True):
        st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Mode de traitement")
    MODE_TRAITEMENT = st.radio(
        "Choisissez l'opération :",
        ["Réception de marchandise", "Commande"],
        index=0
    )
    st.divider()

    st.header("Paramètres")
    Magasin = st.text_input("Code Magasin :", value=config_side["magasin"]).upper()
    if Magasin != config_side["magasin"]: sauvegarder_sidebar("magasin", Magasin)

    NOM_COLLECTION = st.selectbox("Nom de la Marque :", 
                                  options=st.session_state.liste_entreprises, 
                                  index=None, placeholder="Choisissez une marque")

    col_ent1, col_ent2 = st.columns(2)
    with col_ent1:
        if st.button("+ Ajouter", use_container_width=True): ajouter_entreprise_dialog()
    with col_ent2:
        if st.button("- Supprimer", use_container_width=True): supprimer_entreprise_dialog()

    if st.button("Actualiser la liste", use_container_width=True):
        charger_entreprises.clear()
        st.rerun()

    date_final = st.text_input("Date (jj/mm/aaaa) :", value=datetime.now().strftime("%d/%m/%Y"))

    saison = st.text_input("Saison :", value=config_side["saison"], placeholder = "Entrez la saison").upper()
    if saison != config_side["saison"]: sauvegarder_sidebar("saison", saison)

    origine = st.text_input("Origine :", value=config_side["origine"], placeholder = "Entrez l'origine").upper()
    if origine != config_side["origine"]: sauvegarder_sidebar("origine", origine)

    # Initialisation des variables pour éviter les erreurs de définition hors bloc
    AR, Devise, Poids, VisibleWeb = 1, "EUR", "0,7", 1

    if MODE_TRAITEMENT == "Réception de marchandise":
        st.divider()
        AR = st.number_input("Indicateur AR (0/1):", min_value=0, max_value=1, value=int(config_side["ar"]))
        if AR != config_side["ar"]: sauvegarder_sidebar("ar", AR)

        Devise = st.text_input("Devise :", value=config_side["devise"]).upper()
        if Devise != config_side["devise"]: sauvegarder_sidebar("devise", Devise)

        Poids = st.text_input("Poids :", value=config_side["poids"])
        if Poids != config_side["poids"]: sauvegarder_sidebar("poids", Poids)
        if Poids and not est_numerique(Poids): st.error("Le Poids doit être un nombre.")

        VisibleWeb = st.number_input("Visible Web (0/1):", min_value=0, max_value=1, value=int(config_side["visible_web"]))
        if VisibleWeb != config_side["visible_web"]: sauvegarder_sidebar("visible_web", VisibleWeb)

# --- CORPS DE L'APPLICATION ---
@st.fragment
def afficher_zone_produits():
    st.subheader(f"Liste des produits ({MODE_TRAITEMENT})")

    for i, produit in enumerate(st.session_state.liste_produits_manuels):
        with st.expander(f"Produit n°{i+1} : {produit.get('modele', '') or 'Nouveau'}", expanded=True):
            c1, c2 = st.columns(2)
            produit["modele"] = c1.text_input("Modèle", value=produit.get("modele", ""), key=f"mod_{i}").upper()
            produit["designation"] = c2.text_input("Designation :", value = produit.get("designation", ""), key=f"desi_{i}").upper()
            
            c3, c4 = st.columns(2)
            produit["couleur"] = c3.text_input("Couleur", value=produit.get("couleur", ""), key=f"coul_{i}").upper()
            produit["matiere"] = c4.text_input("Matière", value=produit.get("matiere", ""), key=f"mat_{i}").upper()
            
            c5, c6 = st.columns(2)
            produit["prix_achat"] = c5.text_input("Prix Achat", value=produit.get("prix_achat", ""), key=f"p_ach_{i}")
            produit["prix_ttc"] = c6.text_input("Prix TTC ou Coefficient (*)", value=produit.get("prix_ttc", ""), key=f"p_ttc_{i}")

            if produit.get("prix_achat") and not est_numerique(produit["prix_achat"]):
                st.error("Le Prix d'Achat doit être un nombre.")
            if produit.get("prix_ttc") and not est_numerique(produit["prix_ttc"], autoriser_etoile=True):
                st.error("Le Prix TTC doit être un nombre.")

            if MODE_TRAITEMENT == "Réception de marchandise":
                c7, c8 = st.columns(2)
                produit["famille"] = c7.text_input("Famille :", value = produit.get("famille", ""),key=f"fami_{i}").upper()
                produit["ssfamille"] = c8.text_input("Sous Famille :", value = produit.get("ssfamille", ""), key=f"ssfam_{i}").upper()
                produit["rayon"] = st.text_input("Rayon :", value = produit.get("rayon", ""), key=f"ray_{i}").upper()
            else:
                produit["famille"] = st.text_input("Famille :", value = produit.get("famille", ""),key=f"fami_{i}").upper()

            st.markdown("**Tailles et Quantités**")
            cb1, cb2 = st.columns(2)
            with cb1:
                if st.button(f" + Ajouter une taille", key=f"btn_size_{i}"):
                    ajouter_taille(i)
                    st.rerun(scope="fragment")
            with cb2:
                if st.button(f" - Supprimer dernière taille", key=f"btn_del_size_{i}"):
                    supprimer_taille(i)
                    st.rerun(scope="fragment")

            for j, stock in enumerate(produit["stocks"]):
                col_t, col_q = st.columns([2, 1])
                stock["taille"] = col_t.text_input(f"Taille", value=stock["taille"], key=f"size_{i}_{j}")
                stock["qte"] = col_q.number_input(f"Quantité", value=stock["qte"], key=f"qte_{i}_{j}")

    st.divider()
    col_p1, col_p2 = st.columns(2)
    col_p3, col_p4 = st.columns(2)
    with col_p1:
        if st.button("AJOUTER UN NOUVEAU PRODUIT", use_container_width=True):
            ajouter_produit()
            st.rerun(scope="fragment")
    with col_p2:
        if st.button("COPIER UN PRODUIT", use_container_width=True):
            copier_produit_dialog()
    with col_p3:
        if st.button("SUPPRIMER LE DERNIER PRODUIT", use_container_width=True):
            supprimer_produit()
            st.rerun(scope="fragment")
    with col_p4:
        if st.button("VIDER TOUTE LA LISTE", use_container_width=True, type="secondary"):
            vider_liste_dialog()

    st.divider()
    total_modeles = len(st.session_state.liste_produits_manuels)
    total_pieces = sum(int(s["qte"]) for p in st.session_state.liste_produits_manuels for s in p["stocks"] if str(s["qte"]).isdigit())
    
    col_compteur1, col_compteur2 = st.columns(2)
    col_compteur1.metric("Nombre de modèles", total_modeles)
    col_compteur2.metric("Quantité totale", total_pieces)

afficher_zone_produits()
st.divider()

# --- VÉRIFICATION GLOBALE ---
produits_valides = len(st.session_state.liste_produits_manuels) > 0
if produits_valides:
    for p in st.session_state.liste_produits_manuels:
        champs = [p.get("modele"), p.get("prix_achat"), p.get("prix_ttc"), p.get("famille")]
        if MODE_TRAITEMENT == "Réception de marchandise":
            champs.extend([p.get("ssfamille"), p.get("rayon")])
        if any(v == "" or v is None for v in champs) or any(s["taille"] == "" for s in p["stocks"]):
            produits_valides = False; break

params_ok = all([Magasin, NOM_COLLECTION, date_final, saison, origine])
ok = params_ok and produits_valides

# --- GÉNÉRATION ---
if st.button("GÉNÉRER LE FICHIER .TXT", disabled=not ok, use_container_width=True):
    lignes_finales = []
    for produit in st.session_state.liste_produits_manuels:
        pa = str(produit["prix_achat"]).replace(',', '.')
        pttc_raw = str(produit["prix_ttc"]).replace(',', '.')
        
        if "*" in pttc_raw:
            try: pttc_final = str(int(float(pa) * float(pttc_raw.replace("*", ""))))
            except: pttc_final = pttc_raw
        else: pttc_final = pttc_raw

        designation_raw = produit["designation"] if produit["designation"] else (produit["ssfamille"] if MODE_TRAITEMENT == "Réception de marchandise" else produit["famille"])
        
        for stock in produit["stocks"]:
            if MODE_TRAITEMENT == "Réception de marchandise":
                data_row = [
                    nettoyer_texte(Magasin), nettoyer_texte(NOM_COLLECTION), date_final, nettoyer_texte(origine),
                    nettoyer_texte(produit["famille"]), nettoyer_texte(saison), produit["modele"],
                    nettoyer_texte(designation_raw), nettoyer_texte(produit["matiere"]), nettoyer_texte(produit["couleur"]),
                    nettoyer_texte(str(stock["taille"]).upper()), pa, pttc_final, str(stock["qte"]), "",
                    nettoyer_texte(produit["ssfamille"]), nettoyer_texte(produit.get("rayon", "")), nettoyer_texte(produit["modele"]),
                    "", "", "", "", "", "", "\t", str(AR), nettoyer_texte(Devise), "", str(Poids).replace(',', '.'), 
                    "", "","","","","","","","","\t", str(VisibleWeb), "","","","","","","","","","","","","","","","\t"
                ]
            else:
                data_row = [
                    nettoyer_texte(Magasin), nettoyer_texte(NOM_COLLECTION), date_final, nettoyer_texte(origine),
                    nettoyer_texte(produit["famille"]), nettoyer_texte(saison), produit["modele"],
                    nettoyer_texte(designation_raw), nettoyer_texte(produit["matiere"]), nettoyer_texte(produit["couleur"]),
                    nettoyer_texte(str(stock["taille"]).upper()), pa, pttc_final, str(stock["qte"])
                ]
            
            lignes_finales.append("\t".join([str(x).strip() for x in data_row]))

    if lignes_finales:
        st.success("Export réussi.")
        st.download_button(
            label="Télécharger l'export .txt", 
            data="\r\n".join(lignes_finales), 
            file_name=f"{origine}_{NOM_COLLECTION}_{date_final}.txt",
            mime="text/plain"
        )
