import streamlit as st
import pandas as pd
from supabase import create_client

# --- POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

st.set_page_config(page_title="Magazyn PRO", layout="wide")
st.title("📦 System Zarządzania Magazynem")

menu = ["Podgląd", "Dodaj Dane", "Usuń"]
choice = st.sidebar.selectbox("Menu", menu)

# --- 1. PODGLĄD ---
if choice == "Podgląd":
    st.header("Aktualny stan")
    # Pobieramy produkty z dołączoną nazwą kategorii (join)
    response = supabase.table("produkty").select("id, nazwa, liczba, cena, kategoria(nazwa)").execute()
    
    if response.data:
        # Spłaszczanie danych, aby nazwa kategorii była w jednej linii
        flat_data = []
        for item in response.data:
            flat_data.append({
                "ID": item["id"],
                "Nazwa": item["nazwa"],
                "Liczba": item["liczba"],
                "Cena": item["cena"],
                "Kategoria": item["kategoria"]["nazwa"] if item["kategoria"] else "Brak"
            })
        st.dataframe(pd.DataFrame(flat_data), use_container_width=True)
    else:
        st.info("Baza jest pusta.")

# --- 2. DODAJ DANE ---
elif choice == "Dodaj Dane":
    tab1, tab2 = st.tabs(["Nowy Produkt", "Nowa Kategoria"])
    
    with tab2:
        with st.form("kat_form"):
            n_kat = st.text_input("Nazwa kategorii")
            o_kat = st.text_area("Opis")
            if st.form_submit_button("Dodaj kategorię"):
                supabase.table("kategoria").insert({"nazwa": n_kat, "opis": o_kat}).execute()
                st.success("Dodano kategorię!")
                st.rerun()

    with tab1:
        # Pobranie listy kategorii do wyboru
        kats = supabase.table("kategoria").select("id, nazwa").execute().data
        if not kats:
            st.warning("Najpierw dodaj kategorię!")
        else:
            kat_map = {k["nazwa"]: k["id"] for k in kats}
            with st.form("prod_form"):
                nazwa = st.text_input("Nazwa produktu")
                liczba = st.number_input("Liczba", min_value=0)
                cena = st.number_input("Cena", min_value=0.0)
                kat_name = st.selectbox("Wybierz kategorię", list(kat_map.keys()))
                if st.form_submit_button("Zapisz produkt"):
                    supabase.table("produkty").insert({
                        "nazwa": nazwa, 
                        "liczba": liczba, 
                        "cena": cena, 
                        "kategoria_id": kat_map[kat_name]
                    }).execute()
                    st.success("Produkt dodany!")
                    st.rerun()

# --- 3. USUŃ ---
elif choice == "Usuń":
    st.subheader("Usuwanie produktów")
    prods = supabase.table("produkty").select("id, nazwa").execute().data
    if prods:
        p_to_del = st.selectbox("Wybierz produkt", prods, format_func=lambda x: x["nazwa"])
        if st.button("Usuń trwale"):
            supabase.table("produkty").delete().eq("id", p_to_del["id"]).execute()
            st.rerun()
