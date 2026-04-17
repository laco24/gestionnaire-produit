import streamlit as st
import pandas as pd
import re

# Configuration de la page
st.set_page_config(page_title="GestionnaireDeProduit", layout="wide")

st.title("Gestionnaire de Produits")
st.markdown("""
Saisissez les informations produits ci-dessous.
""")

# --- INITIALISATION DU SESSION STATE ---
if "liste_produits_manuels" not in st.session_state:
    st.session_state.liste_produits_manuels = []

if "liste_entreprises" not in st.session_state:
    initiale = ["ESSENTIAL", "MEXICANA"]
    initiale.sort()
    st.session_state.liste_entreprises = initiale

# --- FONCTIONS DE GESTION ---
def ajouter_produit():
    st.session_state.liste_produits_manuels.append({
        "modele": "", 
        "barcode": "",
        "couleur": "",
        "matiere": "",
        "prix_achat": "",
        "prix_ttc": "",
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

# --- SIDEBAR : PARAMÈTRES GÉNÉRAUX ---
with st.sidebar:
    st.header("Paramètres")
    Magasin = st.text_input("Code Magasin :", value="REIMS").upper()

    NOM_COLLECTION = st.selectbox("Nom de la Marque :", 
                                  options=st.session_state.liste_entreprises, 
                                  index=None, 
                                  placeholder="Choisissez une marque")

    if st.button("+ Ajouter une entreprise"):
        st.session_state.afficher_ajout = True

    if st.session_state.get("afficher_ajout", False):
        nouveau_nom = st.text_input("Nom de la nouvelle entreprise :")
        if st.button("Enregistrer l'entreprise"):
            if nouveau_nom:
                nom_up = nouveau_nom.upper()
                if nom_up not in st.session_state.liste_entreprises:
                    st.session_state.liste_entreprises.append(nom_up)
                    st.session_state.liste_entreprises.sort()
                    st.session_state.afficher_ajout = False
                    st.rerun()

    date = st.text_input("Date (jj/mm/aaaa) :", placeholder = "Entrez la date")
    famille = st.text_input("Famille :", placeholder = "Entrez la famille").upper()
    ssfamille = st.text_input("Sous Famille :", placeholder = "Entrez la sous famille").upper()
    saison = st.text_input("Saison :", placeholder = "Entrez la saison").upper()
    rayon = st.text_input("Rayon :", placeholder = "Entrez la rayon").upper()
    origine = st.text_input("Origine :", placeholder = "Entrez l'origine").upper()
    
    st.divider()
    AR = st.number_input("Indicateur AR (0/1):", min_value=0, max_value=1, value=1)
    Devise = st.text_input("Devise :", value="EUR").upper()
    Poids = st.text_input("Poids :", value="0,7").upper()
    VisibleWeb = st.number_input("Visible Web (0/1):", min_value=0, max_value=1, value=1)

# --- CORPS PRINCIPAL : SAISIE PRODUITS ---
st.subheader("Liste des produits")

for i, produit in enumerate(st.session_state.liste_produits_manuels):
    with st.expander(f"Produit n°{i+1} : {produit['modele'] if produit['modele'] else 'Nouveau Produit'}", expanded=True):
        
        # Infos de base
        c1, c2 = st.columns(2)
        produit["modele"] = c1.text_input("Modèle", value=produit["modele"], key=f"mod_{i}").upper()
        produit["barcode"] = c2.text_input("Code Barre", value=produit["barcode"], key=f"bar_{i}").upper()
        
        c3, c4 = st.columns(2)
        produit["couleur"] = c3.text_input("Couleur", value=produit["couleur"], key=f"coul_{i}").upper()
        produit["matiere"] = c4.text_input("Matière", value=produit["matiere"], key=f"mat_{i}").upper()
        
        c5, c6 = st.columns(2)
        produit["prix_achat"] = c5.text_input("Prix Achat", value=produit["prix_achat"], key=f"p_ach_{i}")
        produit["prix_ttc"] = c6.text_input("Prix TTC", value=produit["prix_ttc"], key=f"p_ttc_{i}")

        st.markdown("**Tailles et Quantités**")
        for j, stock in enumerate(produit["stocks"]):
            col_t, col_q = st.columns([2, 1])
            stock["taille"] = col_t.text_input(f"Taille", value=stock["taille"], key=f"size_{i}_{j}")
            stock["qte"] = col_q.number_input(f"Quantité", value=stock["qte"], key=f"qte_{i}_{j}")

        # Boutons de gestion des tailles
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(f" + Ajouter une taille", key=f"btn_size_{i}"):
                ajouter_taille(i)
                st.rerun()
        with col_btn2:
            if st.button(f" - Supprimer dernière taille", key=f"btn_del_size_{i}"):
                supprimer_taille(i)
                st.rerun()

# Boutons de gestion des produits
st.divider()
col_p1, col_p2 = st.columns(2)
with col_p1:
    if st.button("AJOUTER UN NOUVEAU PRODUIT", use_container_width=True):
        ajouter_produit()
        st.rerun()
with col_p2:
    if st.button("SUPPRIMER LE DERNIER PRODUIT", use_container_width=True):
        supprimer_produit()
        st.rerun()

st.divider()

# --- GÉNÉRATION DU FICHIER TXT ---
ok = False 
if not Magasin or not famille or not ssfamille or not AR or not Devise or not VisibleWeb or not Poids or not date or not saison or not rayon or not origine:
    ok = True 

if st.button("GÉNÉRER LE FICHIER .TXT", disabled = ok):
    if not st.session_state.liste_produits_manuels:
        st.error("Ajoutez au moins un produit avant de générer le fichier.")
    elif not NOM_COLLECTION:
        st.error("Veuillez choisir une Marque dans la barre latérale.")
    else:
        lignes_finales = []
        
        for produit in st.session_state.liste_produits_manuels:
            mod = produit["modele"]
            bar = produit["barcode"]
            coul = produit["couleur"]
            mat = produit["matiere"]
            pa = produit["prix_achat"]
            pttc = produit["prix_ttc"]

            for stock in produit["stocks"]:
                taille = stock["taille"]
                
                try:
                    qte_val = int(stock["qte"]) if stock["qte"] else 0
                except:
                    qte_val = 0

                if qte_val > 0:
                    for _ in range(qte_val):
                        data_row = [
                            Magasin, NOM_COLLECTION, date, origine, famille, saison, bar, ssfamille,
                            mat, coul, taille, pa, pttc, "1", "",
                            ssfamille, rayon, mod, "", "", "", "", "", "", "", "\t",
                            str(AR), Devise, "", Poids, "", "","","","","","","","","","", str(VisibleWeb)
                        ]
                        lignes_finales.append("\t".join(data_row))

        if lignes_finales:
            resultat_txt = "\n".join(lignes_finales)
            st.success(f"Génération réussie : {len(lignes_finales)} lignes créées.")
            
            st.download_button(
                label="Télécharger l'export .txt",
                data=resultat_txt,
                file_name=f"export_{NOM_COLLECTION}_{date.replace('/','-')}.txt",
                mime="text/plain"
            )
        else:
            st.warning("Aucune ligne n'a pu être générée (vérifiez les quantités).")
