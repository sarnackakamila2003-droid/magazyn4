
import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn", layout="wide")

# --- GLOBALNY SUWAK W SIDEBARZE ---
st.sidebar.header("⚙️ Ustawienia Globalne")
globalny_limit = st.sidebar.slider(
    "Próg niskiego stanu (dla wszystkich)", 
    min_value=0, 
    max_value=100, 
    value=10,
    help="Produkty z ilością poniżej tej wartości pojawią się w alertach."
)

st.title("📦 System Zarządzania Produktami")

# --- POBIERANIE DANYCH ---
try:
    kategorie_data = supabase.table("kategorie").select("*").execute().data
    produkty_data = supabase.table("produkty").select("*, kategorie(nazwa)").execute().data
except Exception as e:
    st.error(f"Błąd połączenia: {e}")
    kategorie_data, produkty_data = [], []

# --- SEKCJA ALERTÓW (Na podstawie suwaka) ---
st.sidebar.markdown("---")
st.sidebar.header("⚠️ Powiadomienia")
niskie_stany = [p for p in produkty_data if p['liczba'] < globalny_limit]

if niskie_stany:
    for p in niskie_stany:
        st.sidebar.warning(f"**{p['nazwa']}**: tylko {p['liczba']} szt.")
else:
    st.sidebar.success(f"Wszystko powyżej {globalny_limit} szt.")

tab1, tab2 = st.tabs(["Produkty", "Kategorie"])

# --- SEKCJA KATEGORIE ---
with tab2:
    st.header("Zarządzaj Kategoriami")
    with st.form("add_category", clear_on_submit=True):
        nazwa_kat = st.text_input("Nazwa kategorii")
        if st.form_submit_button("Dodaj Kategorię") and nazwa_kat:
            supabase.table("kategorie").insert({"nazwa": nazwa_kat}).execute()
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
    
    with st.expander("➕ Dodaj nowy produkt"):
        with st.form("add_product", clear_on_submit=True):
            col_a, col_b, col_c = st.columns(3)
            nazwa_p = col_a.text_input("Nazwa")
            liczba_p = col_b.number_input("Ilość", min_value=1, step=1)
            cena_p = col_c.number_input("Cena", min_value=0.0, format="%.2f")
            kat_p = st.selectbox("Kategoria", options=list(kat_options.keys()))
            
            if st.form_submit_button("Dodaj produkt") and nazwa_p:
                supabase.table("produkty").insert({
                    "nazwa": nazwa_p, "liczba": liczba_p, "cena": cena_p, 
                    "kategoria": kat_options[kat_p]
                }).execute()
                st.rerun()

    st.subheader("Aktualny stan magazynowy")
    
    # Wyświetlanie listy produktów
    for p in produkty_data:
        # Wizualne ostrzeżenie jeśli stan < suwak
        if p['liczba'] < globalny_limit:
            st.error(f"NISKI STAN: {p['nazwa']} ({p['liczba']} < {globalny_limit})")

        with st.container():
            col1, col2, col3 = st.columns([3, 4, 1])
            
            with col1:
                st.write(f"**{p['nazwa']}**")
                st.caption(f"Cena: {p['cena']} zł | Kat: {p['kategorie']['nazwa'] if p['kategorie'] else 'Brak'}")
                st.markdown(f"Obecnie: **{p['liczba']}** szt.")
            
            with col2:
                v_c1, v_c2, v_c3 = st.columns([2, 2, 2])
                ile = v_c1.number_input("Ilość", min_value=1, key=f"v_{p['id']}", step=1)
                
                if v_c2.button("➕ Dodaj", key=f"a_{p['id']}", use_container_width=True):
                    supabase.table("produkty").update({"liczba": p['liczba'] + ile}).eq("id", p['id']).execute()
                    st.rerun()
                
                if v_c3.button("➖ Zdejmij", key=f"s_{p['id']}", use_container_width=True):
                    if ile <= p['liczba']:
                        nova_liczba = p['liczba'] - ile
                        supabase.table("produkty").update({"liczba": nova_liczba}).eq("id", p['id']).execute()
                        st.rerun()
                    else:
                        st.warning("Brak wystarczającej ilości!")

            with col3:
                if st.button("🗑️", key=f"d_{p['id']}", help="Usuń produkt"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
            st.divider()
