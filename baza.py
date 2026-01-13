import streamlit as st
from supabase import create_client

# 1. Połączenie z bazą
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

st.set_page_config(page_title="Zarządzanie Bazą", layout="wide")
st.title("📊 Obsługa Bazy Produktów i Kategorii")

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    res = supabase.table("kategoria").select("*").execute()
    return res.data

def get_products():
    # Pobieramy produkty wraz z nazwą kategorii (join)
    res = supabase.table("produkty").select("*, kategoria(nazwa)").execute()
    return res.data

# --- SEKCA 1: KATEGORIE ---
st.header("📂 Kategorie")
col1, col2 = st.columns(2)

with col1:
    with st.form("dodaj_kat", clear_on_submit=True):
        st.subheader("Dodaj kategorię")
        n_kat = st.text_input("Nazwa kategorii")
        o_kat = st.text_area("Opis")
        if st.form_submit_button("Zapisz"):
            supabase.table("kategoria").insert({"nazwa": n_kat, "opis": o_kat}).execute()
            st.rerun()

with col2:
    st.subheader("Usuń kategorię")
    kats = get_categories()
    if kats:
        kat_to_del = st.selectbox("Wybierz kategorię", kats, format_func=lambda x: x['nazwa'])
        if st.button("❌ Usuń wybraną"):
            supabase.table("kategoria").delete().eq("id", kat_to_del['id']).execute()
            st.rerun()

st.divider()

# --- SEKCJA 2: PRODUKTY ---
st.header("📦 Produkty")
c1, c2 = st.columns([1, 2])

with c1:
    with st.form("dodaj_prod", clear_on_submit=True):
        st.subheader("Nowy produkt")
        p_nazwa = st.text_input("Nazwa")
        p_liczba = st.number_input("Liczba", step=1, format="%d")
        p_cena = st.number_input("Cena", step=0.01)
        
        # Wybór kategorii z listy (Klucz Obcy)
        p_kat = st.selectbox("Kategoria", kats, format_func=lambda x: x['nazwa']) if kats else None
        
        if st.form_submit_button("Dodaj produkt") and p_kat:
            payload = {
                "nazwa": p_nazwa,
                "liczba": p_liczba,
                "cena": p_cena,
                "kategoria_id": p_kat['id']
            }
            supabase.table("produkty").insert(payload).execute()
            st.rerun()

with c2:
    st.subheader("Lista produktów")
    prods = get_products()
    if prods:
        for p in prods:
            with st.expander(f"{p['nazwa']} ({p['kategoria']['nazwa'] if p['kategoria'] else 'Brak'})"):
                st.write(f"Cena: {p['cena']} | Ilość: {p['liczba']}")
                if st.button(f"Usuń {p['nazwa']}", key=f"p_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
    else:
        st.info("Brak produktów.")
