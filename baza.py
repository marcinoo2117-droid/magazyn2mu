import streamlit as st
import pandas as pd
from supabase import create_client

# --- POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn PRO v2", layout="wide", page_icon="📦")

# CSS dla lepszego wyglądu kart
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE POMOCNICZE ---
def get_products_data():
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategoria_id, kategoria(nazwa)").execute()
    return res.data

def get_categories_data():
    res = supabase.table("kategoria").select("id, nazwa").execute()
    return res.data

# --- SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/407/407826.png", width=100)
st.sidebar.title("Panel Zarządzania")
menu = ["📊 Dashboard", "🔎 Podgląd i Szukanie", "➕ Dodaj Dane", "✏️ Edytuj / Usuń"]
choice = st.sidebar.radio("Nawigacja", menu)

# --- 1. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📈 Statystyki Magazynowe")
    data = get_products_data()
    
    if data:
        df = pd.DataFrame(data)
        
        # Metryki
        col1, col2, col3, col4 = st.columns(4)
        total_items = df['liczba'].sum()
        total_value = (df['liczba'] * df['cena']).sum()
        unique_prods = len(df)
        low_stock = len(df[df['liczba'] < 5])
        
        col1.metric("Suma sztuk", total_items)
        col2.metric("Wartość netto", f"{total_value:,.2f} zł")
        col3.metric("Rodzajów produktów", unique_prods)
        col4.metric("Niski stan (<5)", low_stock, delta_color="inverse", delta=f"-{low_stock}" if low_stock > 0 else 0)

        st.divider()
        
        # Wykresy
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Ilość produktów")
            st.bar_chart(df.set_index('nazwa')['liczba'])
        with c2:
            st.subheader("Alerty niskiego stanu")
            if low_stock > 0:
                st.warning(f"Uwaga! {low_stock} produkty wymagają zamówienia.")
                st.table(df[df['liczba'] < 5][['nazwa', 'liczba']])
            else:
                st.success("Wszystkie stany magazynowe są w normie.")
    else:
        st.info("Brak danych do wyświetlenia statystyk.")

# --- 2. PODGLĄD I SZUKANIE ---
elif choice == "🔎 Podgląd i Szukanie":
    st.header("🔎 Przeglądaj zasoby")
    search = st.text_input("Szukaj produktu po nazwie...")
    
    data = get_products_data()
    if data:
        flat_data = [{
            "ID": i["id"], "Nazwa": i["nazwa"], "Sztuk": i["liczba"], 
            "Cena": i["cena"], "Kategoria": i["kategoria"]["nazwa"] if i["kategoria"] else "Brak",
            "Wartość": i["liczba"] * i["cena"]
        } for i in data]
        
        df = pd.DataFrame(flat_data)
        if search:
            df = df[df['Nazwa'].str.contains(search, case=False)]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Eksport do CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Pobierz CSV", csv, "magazyn.csv", "text/csv")

# --- 3. DODAJ DANE ---
elif choice == "➕ Dodaj Dane":
    tab1, tab2 = st.tabs(["🆕 Produkt", "📂 Kategoria"])
    
    with tab2:
        with st.form("kat_form", clear_on_submit=True):
            st.subheader("Nowa kategoria")
            n_kat = st.text_input("Nazwa")
            o_kat = st.text_area("Opis")
            if st.form_submit_button("Zapisz kategorię"):
                if n_kat:
                    supabase.table("kategoria").insert({"nazwa": n_kat, "opis": o_kat}).execute()
                    st.
