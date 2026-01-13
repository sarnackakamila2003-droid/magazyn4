
 import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn", layout="wide")
st.title("📦 System Zarządzania Produktami")

# --- POBIERANIE DANYCH ---
# Pobieramy dane na początku, aby móc wyświetlić alerty i listy
try:
    kategorie_data = supabase.table("kategorie").select("*").execute().data
    produkty_data = supabase.table("produkty").select("*, kategorie(nazwa)").execute().data
except Exception as e:
    st.error(f"Błąd połączenia: {e}")
    kategorie_data, produkty_data = [], []

# --- SEKCJA ALERTÓW ---
st.sidebar.header("⚠️ Powiadomienia")
niskie_stany = [p for p in produkty_data if p['liczba'] < 10]
if niskie_stany:
    for p in niskie_stany:
        st.sidebar.warning(f"Niski stan: **{p['nazwa']}** ({p['liczba']} szt.)")
else:
    st.sidebar.success("Wszystkie stany w normie (>10 szt.)")

tab1, tab2 = st.tabs(["Produkty", "Kategorie"])

# --- SEKCJA KATEGORIE ---
with tab2:
    st.header("Zarządzaj Kategoriami")
    with st.form("add_category", clear_on_submit=True):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        if st.form_submit_button("Dodaj Kategorię") and nazwa_kat:
            supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
            st.rerun()

    st.subheader("Lista kategorii")
    for k in kategorie_data:
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{k['nazwa']}**")
        if c2.button("Usuń", key=f"del_kat_{k['id']}"):
            supabase.table("kategorie").delete().eq("id", k['id']).execute()
            st.rerun()

# --- SEKCJA PRODUKTY ---
with tab1:
    st.header("Zarządzaj Produktami")
    
    kat_options = {k['nazwa']: k['id'] for k in kategorie_data}
    
    # Formularz dodawania NOWEGO produktu
    with st.expander("➕ Dodaj nowy produkt do bazy"):
        with st.form("add_product", clear_on_submit=True):
            col_a, col_b, col_c = st.columns(3)
            nazwa_p = col_a.text_input("Nazwa")
            liczba_p = col_b.number_input("Ilość początkowa", min_value=1, step=1)
            cena_p = col_c.number_input("Cena", min_value=0.0, format="%.2f")
            kat_p = st.selectbox("Kategoria", options=list(kat_options.keys()))
            
            if st.form_submit_button("Dodaj produkt") and nazwa_p:
                supabase.table("produkty").insert({
                    "nazwa": nazwa_p, "liczba": liczba_p, "cena": cena_p, "kategoria": kat_options[kat_p]
                }).execute()
                st.rerun()

    st.subheader("Aktualny stan magazynowy")
    
    for p in produkty_data:
        # Wyróżnienie jeśli stan niski
        if p['liczba'] < 10:
            st.error(f"Wymaga uzupełnienia: {p['nazwa']}")

        with st.container():
            col1, col2, col3 = st.columns([3, 4, 1])
            
            # Kolumna 1: Informacje
            kat_l = p['kategorie']['nazwa'] if p['kategorie'] else "Brak"
            col1.write(f"**{p['nazwa']}**")
            col1.caption(f"Cena: {p['cena']} zł | Kat: {kat_l}")
            col1.markdown(f"Obecny stan: **{p['liczba']}** szt.")
            
            # Kolumna 2: Zarządzanie ilością (Dodaj/Zdejmij)
            with col2:
                v_col1, v_col2, v_col3 = st.columns([2, 2, 2])
                ile = v_col1.number_input("Sztuk", min_value=1, step=1, key=f"val_{p['id']}")
                
                # Przycisk DODAJ
                if v_col2.button(f"➕ Dodaj", key=f"add_btn_{p['id']}", use_container_width=True):
                    nowa_suma = p['liczba'] + ile
                    supabase.table("produkty").update({"liczba": nowa_suma}).eq("id", p['id']).execute()
                    st.rerun()
                
                # Przycisk ZDEJMIJ
                if v_col3.button(f"➖ Zdejmij", key=f"sub_btn_{p['id']}", use_container_width=True):
                    if ile > p['liczba']:
                        st.warning("Nie ma tyle na stanie!")
                    else:
                        nowa_suma = p['liczba'] - ile
                        supabase.table("produkty").update({"liczba": nowa_suma}).eq("id", p['id']).execute()
                        st.rerun()

            # Kolumna 3: Usuwanie całkowite
            if col3.button("🗑️", key=f"del_all_{p['id']}", help="Usuń produkt z bazy"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
                
            st.divider()
