import streamlit as st
import sqlite3
import pandas as pd
import os

# --- KONFIGURACJA BAZY ---
DB_FILE = "magazyn.db"

def get_connection():
    """Tworzy bezpieczne połączenie z bazą danych."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    # To pozwala na dostęp do kolumn po nazwach jak w słowniku
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Inicjalizacja tabel jeśli nie istnieją."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS kategoria
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      nazwa TEXT NOT NULL,
                      opis TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS produkty
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      nazwa TEXT NOT NULL,
                      liczba INTEGER DEFAULT 0,
                      cena REAL DEFAULT 0.0,
                      kategoria_id INTEGER,
                      FOREIGN KEY(kategoria_id) REFERENCES kategoria(id))''')
        conn.commit()

# Inicjalizacja przy starcie
init_db()

# --- INTERFEJS ---
st.set_page_config(page_title="Magazyn", layout="wide")

# Funkcja do pobierania danych (z odświeżaniem)
def fetch_data(query):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

st.title("📦 System Zarządzania Magazynem")

# Sidebar
menu = ["Podgląd", "Dodaj Dane", "Usuń"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Podgląd":
    st.header("Aktualny stan")
    
    # Poprawione zapytanie SQL - zczytuje nawet jeśli kategoria nie istnieje (LEFT JOIN)
    query = '''
        SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria_nazwa
        FROM produkty p
        LEFT JOIN kategoria k ON p.kategoria_id = k.id
    '''
    df = fetch_data(query)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Baza jest pusta. Dodaj pierwsze dane w menu bocznym.")

elif choice == "Dodaj Dane":
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dodaj Kategorię")
        with st.form("kat_form"):
            n_kat = st.text_input("Nazwa")
            o_kat = st.text_input("Opis")
            if st.form_submit_button("Zapisz"):
                with get_connection() as conn:
                    conn.execute("INSERT INTO kategoria (nazwa, opis) VALUES (?,?)", (n_kat, o_kat))
                st.success("Dodano!")
                st.rerun()

    with col2:
        st.subheader("Dodaj Produkt")
        # Zczytujemy kategorie do wyboru
        kat_df = fetch_data("SELECT * FROM kategoria")
        if kat_df.empty:
            st.warning("Najpierw dodaj kategorię!")
        else:
            with st.form("prod_form"):
                nazwa = st.text_input("Nazwa produktu")
                ile = st.number_input("Ilość", min_value=0)
                cena = st.number_input("Cena", min_value=0.0)
                # Mapowanie nazwy na ID
                kat_choice = st.selectbox("Kategoria", kat_df['nazwa'].tolist())
                kat_id = int(kat_df[kat_df['nazwa'] == kat_choice]['id'].values[0])
                
                if st.form_submit_button("Dodaj produkt"):
                    with get_connection() as conn:
                        conn.execute("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?,?,?,?)",
                                     (nazwa, ile, cena, kat_id))
                    st.success("Produkt dodany!")
                    st.rerun()

elif choice == "Usuń":
    st.header("Usuwanie rekordów")
    
    # Usuwanie produktu
    prod_df = fetch_data("SELECT id, nazwa FROM produkty")
    if not prod_df.empty:
        p_to_del = st.selectbox("Wybierz produkt do usunięcia", prod_df['nazwa'].tolist())
        p_id = int(prod_df[prod_df['nazwa'] == p_to_del]['id'].values[0])
        if st.button("Usuń Produkt"):
            with get_connection() as conn:
                conn.execute("DELETE FROM produkty WHERE id = ?", (p_id,))
            st.rerun()
