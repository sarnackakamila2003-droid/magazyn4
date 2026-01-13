import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Na Streamlit Cloud dodaj te dane w "Settings" -> "Secrets"
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📦 System Zarządzania Produktami")

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["Produkty", "Kategorie"])

# --- SEKCJA KATEGORIE ---
with tab2:
    st.header("Zarządzaj Kategoriami")
    
    # Dodawanie kategorii
    with st.form("add_category"):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        submit_kat = st.form_submit_button("Dodaj Kategorię")
        
        if submit_kat and nazwa_kat:
            data = {"nazwa": nazwa_kat, "opis": opis_kat}
            supabase.table("kategorie").insert(data).execute()
            st.success(f"Dodano kategorię: {nazwa_kat}")

    # Lista i usuwanie kategorii
    st.subheader("Lista kategorii")
    kat_response = supabase.table("kategorie").select("*").execute()
    kategorie = kat_response.data
    
    for k in kategorie:
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{k['nazwa']}** (ID: {k['id']})")
        if col2.button("Usuń", key=f"del_kat_{k['id']}"):
            supabase.table("kategorie").delete().eq("id", k['id']).execute()
            st.rerun()

# --- SEKCJA PRODUKTY ---
with tab1:
    st.header("Zarządzaj Produktami")
    
    # Pobranie kategorii do selectboxa
    kat_options = {k['nazwa']: k['id'] for k in kategorie}
    
    # Dodawanie produktu
    with st.form("add_product"):
        nazwa_prod = st.text_input("Nazwa produktu")
        liczba = st.number_input("Ilość (liczba)", min_value=0, step=1)
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_options.keys()))
        
        submit_prod = st.form_submit_button("Dodaj Produkt")
        
        if submit_prod and nazwa_prod:
            prod_data = {
                "nazwa": nazwa_prod,
                "liczba": liczba,
                "cena": cena,
                "kategoria": kat_options[wybrana_kat]
            }
            supabase.table("produkty").insert(prod_data).execute()
            st.success(f"Dodano produkt: {nazwa_prod}")

    # Lista i usuwanie produktów
    st.subheader("Aktualne produkty")
    prod_response = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    produkty = prod_response.data
    
    for p in produkty:
        col1, col2 = st.columns([3, 1])
        kat_label = p['kategorie']['nazwa'] if p['kategorie'] else "Brak"
        col1.write(f"**{p['nazwa']}** — {p['liczba']} szt. — {p['cena']} zł (Kat: {kat_label})")
        if col2.button("Usuń", key=f"del_prod_{p['id']}"):
            supabase.table("produkty").delete().eq("id", p['id']).execute()
            st.rerun()
