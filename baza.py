import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📦 System Zarządzania Produktami")

tab1, tab2 = st.tabs(["Produkty", "Kategorie"])

# --- SEKCJA KATEGORIE ---
with tab2:
    st.header("Zarządzaj Kategoriami")
    
    with st.form("add_category", clear_on_submit=True):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        submit_kat = st.form_submit_button("Dodaj Kategorię")
        
        if submit_kat and nazwa_kat:
            supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
            st.success(f"Dodano kategorię: {nazwa_kat}")
            st.rerun()

    st.subheader("Lista kategorii")
    kategorie = supabase.table("kategorie").select("*").execute().data
    
    for k in kategorie:
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{k['nazwa']}** (ID: {k['id']})")
        if col2.button("Usuń całkowicie", key=f"del_kat_{k['id']}"):
            supabase.table("kategorie").delete().eq("id", k['id']).execute()
            st.rerun()

# --- SEKCJA PRODUKTY ---
with tab1:
    st.header("Zarządzaj Produktami")
    
    kat_options = {k['nazwa']: k['id'] for k in kategorie}
    
    with st.form("add_product", clear_on_submit=True):
        nazwa_prod = st.text_input("Nazwa produktu")
        liczba = st.number_input("Ilość do dodania", min_value=1, step=1)
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_options.keys()))
        submit_prod = st.form_submit_button("Dodaj do magazynu")
        
        if submit_prod and nazwa_prod:
            prod_data = {"nazwa": nazwa_prod, "liczba": liczba, "cena": cena, "kategoria": kat_options[wybrana_kat]}
            supabase.table("produkty").insert(prod_data).execute()
            st.rerun()

    st.subheader("Aktualny stan magazynowy")
    produkty = supabase.table("produkty").select("*, kategorie(nazwa)").execute().data
    
    for p in produkty:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            kat_label = p['kategorie']['nazwa'] if p['kategorie'] else "Brak"
            col1.write(f"**{p['nazwa']}**")
            col1.caption(f"Cena: {p['cena']} zł | Kat: {kat_label} | Obecnie: {p['liczba']} szt.")
            
            # Formularz do zdejmowania określonej ilości
            ile_usunac = col2.number_input("Ilość", min_value=1, max_value=int(p['liczba']), key=f"num_{p['id']}", step=1)
            if col2.button(f"Zdejmij {ile_usunac} szt.", key=f"btn_sub_{p['id']}"):
                nowa_liczba = p['liczba'] - ile_usunac
                if nowa_liczba <= 0:
                    # Jeśli zostaje 0, możesz albo zostawić produkt z ilością 0, albo go usunąć:
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                else:
                    supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", p['id']).execute()
                st.rerun()
                
            # Przycisk do całkowitego usunięcia pozycji
            if col3.button("Usuń wpis", key=f"del_all_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
            st.divider()
