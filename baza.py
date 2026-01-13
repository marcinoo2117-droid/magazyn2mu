
import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Na Streamlit Cloud dodaj te dane w Settings -> Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📦 Zarządzanie Magazynem")

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["Produkty", "Kategorie"])

# --- OBSŁUGA KATEGORII ---
with tab2:
    st.header("Zarządzanie Kategoriami")
    
    # Dodawanie kategorii
    with st.form("add_category"):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        submit_kat = st.form_submit_button("Dodaj kategorię")
        
        if submit_kat and nazwa_kat:
            data = {"nazwa": nazwa_kat, "opis": opis_kat}
            response = supabase.table("kategoria").insert(data).execute()
            st.success(f"Dodano kategorię: {nazwa_kat}")

    # Usuwanie kategorii
    st.subheader("Usuń kategorię")
    kategorie = supabase.table("kategoria").select("id, nazwa").execute()
    kat_options = {item['nazwa']: item['id'] for item in kategorie.data}
    
    selected_kat_del = st.selectbox("Wybierz kategorię do usunięcia", options=list(kat_options.keys()))
    if st.button("Usuń wybraną kategorię"):
        supabase.table("kategoria").delete().eq("id", kat_options[selected_kat_del]).execute()
        st.warning(f"Usunięto kategorię {selected_kat_del}")
        st.rerun()

# --- OBSŁUGA PRODUKTÓW ---
with tab1:
    st.header("Zarządzanie Produktami")
    
    # Pobranie kategorii do selectboxa
    kategorie_data = supabase.table("kategoria").select("id, nazwa").execute()
    kat_map = {item['nazwa']: item['id'] for item in kategorie_data.data}

    # Formularz dodawania produktu
    with st.form("add_product"):
        nazwa_prod = st.text_input("Nazwa produktu")
        liczba = st.number_input("Liczba (szt.)", min_value=0, step=1)
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        kategoria_nazwa = st.selectbox("Kategoria", options=list(kat_map.keys()))
        
        submit_prod = st.form_submit_button("Dodaj produkt")
        
        if submit_prod and nazwa_prod:
            prod_data = {
                "nazwa": nazwa_prod,
                "liczba": liczba,
                "cena": cena,
                "kategoria_id": kat_map[kategoria_nazwa]
            }
            supabase.table("produkty").insert(prod_data).execute()
            st.success(f"Dodano produkt: {nazwa_prod}")

    # Lista i usuwanie produktów
    st.subheader("Aktualna lista produktów")
    produkty = supabase.table("produkty").select("id, nazwa, liczba, cena").execute()
    
    if produkty.data:
        for p in produkty.data:
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{p['nazwa']}** - {p['liczba']} szt. | {p['cena']} zł")
            if col2.button("Usuń", key=f"del_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")
