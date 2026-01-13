import streamlit as st
import sqlite3
import pandas as pd

# --- KONFIGURACJA BAZY DANYCH ---
def get_connection():
    # check_same_thread=False jest kluczowe dla Streamlit
    return sqlite3.connect('magazyn.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabela Kategorie
    c.execute('''CREATE TABLE IF NOT EXISTS kategorie
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nazwa TEXT NOT NULL,
                  opis TEXT)''')
    
    # Tabela Produkty
    c.execute('''CREATE TABLE IF NOT EXISTS produkty
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nazwa TEXT NOT NULL,
                  liczba INTEGER DEFAULT 0,
                  cena REAL DEFAULT 0.0,
                  kategoria_id INTEGER,
                  FOREIGN KEY(kategoria_id) REFERENCES kategorie(id))''')
    conn.commit()
    conn.close()

init_db()

# --- INTERFEJS STREAMLIT ---
st.set_page_config(page_title="Magazyn PRO", layout="wide", page_icon="📦")

# Sidebar - nawigacja
st.sidebar.title("🎮 Panel Sterowania")
menu = ["📊 Dashboard", "🔍 Przeglądaj i Szukaj", "➕ Dodaj Dane", "✏️ Edytuj / Usuń"]
choice = st.sidebar.radio("Wybierz akcję", menu)

conn = get_connection()
cursor = conn.cursor()

# --- 1. DASHBOARD (STATYSTYKI) ---
if choice == "📊 Dashboard":
    st.title("📈 Statystyki Magazynu")
    
    # Pobranie danych
    df_prod = pd.read_sql_query("SELECT * FROM produkty", conn)
    df_kat = pd.read_sql_query("SELECT * FROM kategorie", conn)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Liczba produktów", len(df_prod))
    with col2:
        total_val = (df_prod['liczba'] * df_prod['cena']).sum()
        st.metric("Wartość magazynu", f"{total_val:,.2f} zł")
    with col3:
        st.metric("Liczba kategorii", len(df_kat))

    st.divider()
    if not df_prod.empty:
        st.subheader("Podsumowanie ilościowe")
        st.bar_chart(df_prod.set_index('nazwa')['liczba'])

# --- 2. PRZEGLĄDAJ I SZUKAJ ---
elif choice == "🔍 Przeglądaj i Szukaj":
    st.header("🧐 Przeglądanie bazy danych")
    
    search_term = st.text_input("Szukaj produktu po nazwie...")
    
    query = '''
        SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria, (p.liczba * p.cena) as wartosc
        FROM produkty p
        LEFT JOIN kategorie k ON p.kategoria_id = k.id
    '''
    df = pd.read_sql_query(query, conn)
    
    if search_term:
        df = df[df['nazwa'].str.contains(search_term, case=False)]
    
    st.dataframe(df, use_container_width=True)
    
    # Eksport danych
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Pobierz raport CSV", csv, "magazyn_raport.csv", "text/csv")

# --- 3. DODAJ DANE ---
elif choice == "➕ Dodaj Dane":
    tab1, tab2 = st.tabs(["Nowy Produkt", "Nowa Kategoria"])
    
    with tab1:
        st.subheader("Dodaj produkt")
        kategorie = cursor.execute("SELECT id, nazwa FROM kategorie").fetchall()
        kat_options = {k[1]: k[0] for k in kategorie}
        
        if not kat_options:
            st.error("Błąd: Najpierw musisz dodać kategorię!")
        else:
            with st.form("form_add_prod"):
                n = st.text_input("Nazwa produktu")
                l = st.number_input("Ilość", min_value=0)
                c = st.number_input("Cena", min_value=0.0)
                k = st.selectbox("Kategoria", list(kat_options.keys()))
                if st.form_submit_button("Dodaj"):
                    cursor.execute("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?,?,?,?)",
                                   (n, l, c, kat_options[k]))
                    conn.commit()
                    st.success("Produkt dodany!")

    with tab2:
        st.subheader("Dodaj kategorię")
        with st.form("form_add_kat"):
            n_kat = st.text_input("Nazwa kategorii")
            o_kat = st.text_area("Opis")
            if st.form_submit_button("Dodaj"):
                cursor.execute("INSERT INTO kategorie (nazwa, opis) VALUES (?,?)", (n_kat, o_kat))
                conn.commit()
                st.success("Kategoria dodana!")
                st.rerun()

# --- 4. EDYTUJ / USUŃ ---
elif choice == "✏️ Edytuj / Usuń":
    st.header("Zarządzanie rekordami")
    
    edit_mode = st.toggle("Tryb Edycji", value=False)
    
    # Produkty
    st.subheader("Produkty")
    prods = cursor.execute("SELECT id, nazwa, liczba, cena FROM produkty").fetchall()
    for p_id, p_nazwa, p_liczba, p_cena in prods:
        cols = st.columns([3, 1, 1, 1, 1])
        cols[0].write(p_nazwa)
        
        if edit_mode:
            new_qty = cols[1].number_input("Ilość", value=p_liczba, key=f"q_{p_id}", label_visibility="collapsed")
            if cols[3].button("Zapisz", key=f"s_{p_id}"):
                cursor.execute("UPDATE produkty SET liczba = ? WHERE id = ?", (new_qty, p_id))
                conn.commit()
                st.rerun()
        else:
            cols[1].write(f"{p_liczba} szt.")
            cols[2].write(f"{p_cena} zł")
            
        if cols[4].button("Usuń", key=f"d_{p_id}"):
            cursor.execute("DELETE FROM produkty WHERE id = ?", (p_id,))
            conn.commit()
            st.rerun()

    st.divider()
    # Kategorie
    st.subheader("Kategorie")
    kats = cursor.execute("SELECT id, nazwa FROM kategorie").fetchall()
    for k_id, k_nazwa in kats:
        c1, c2 = st.columns([4, 1])
        c1.write(k_nazwa)
        if c2.button("Usuń", key=f"dk_{k_id}"):
            # Proste zabezpieczenie przed osieroceniem produktów
            cursor.execute("DELETE FROM kategorie WHERE id = ?", (k_id,))
            conn.commit()
            st.rerun()

conn.close()

