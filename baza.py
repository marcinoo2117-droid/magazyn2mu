import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# --- KONFIGURACJA MODELU BAZY DANYCH ---
Base = declarative_base()

class Kategoria(Base):
    __tablename__ = 'kategoria'
    id = Column(Integer, primary_key=True)
    nazwa = Column(String, nullable=False)
    opis = Column(String)
    produkty = relationship("Produkty", back_populates="kategoria", cascade="all, delete-orphan")

class Produkty(Base):
    __tablename__ = 'produkty'
    id = Column(Integer, primary_key=True)
    nazwa = Column(String, nullable=False)
    liczba = Column(Integer)
    cena = Column(Numeric(10, 2))
    kategoria_id = Column(Integer, ForeignKey('kategoria.id'))
    kategoria = relationship("Kategoria", back_populates="produkty")

# Tworzenie bazy danych
engine = create_engine('sqlite:///magazyn.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# --- INTERFEJS STREAMLIT ---
st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")
st.title("📦 System Zarządzania Produktami")

menu = ["Podgląd Bazy", "Dodaj Kategorię", "Dodaj Produkt", "Usuń Elementy"]
choice = st.sidebar.selectbox("Nawigacja", menu)

# --- PODGLĄD BAZY ---
if choice == "Podgląd Bazy":
    st.subheader("Aktualny stan magazynu")
    
    kategorie = session.query(Kategoria).all()
    if not kategorie:
        st.info("Baza danych jest pusta.")
    else:
        for kat in kategorie:
            with st.expander(f"Kategoria: {kat.nazwa} (Opis: {kat.opis})"):
                prod_data = []
                for p in kat.produkty:
                    prod_data.append({
                        "ID": p.id,
                        "Nazwa Produktu": p.name if hasattr(p, 'name') else p.nazwa, # Poprawka na nazewnictwo ze schematu
                        "Liczba": p.liczba,
                        "Cena": f"{p.cena} zł"
                    })
                if prod_data:
                    st.table(prod_data)
                else:
                    st.write("Brak produktów w tej kategorii.")

# --- DODAWANIE KATEGORII ---
elif choice == "Dodaj Kategorię":
    st.subheader("➕ Dodaj nową kategorię")
    with st.form("form_kat"):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis kategorii")
        if st.form_submit_button("Zapisz kategorię"):
            if nazwa_kat:
                nowa_kat = Kategoria(nazwa=nazwa_kat, opis=opis_kat)
                session.add(nowa_kat)
                session.commit()
                st.success(f"Dodano kategorię: {nazwa_kat}")
            else:
                st.error("Nazwa kategorii jest wymagana!")

# --- DODAWANIE PRODUKTU ---
elif choice == "Dodaj Produkt":
    st.subheader("➕ Dodaj nowy produkt")
    kategorie = session.query(Kategoria).all()
    kat_dict = {k.nazwa: k.id for k in kategorie}
    
    if not kat_dict:
        st.warning("Najpierw musisz dodać przynajmniej jedną kategorię.")
    else:
        with st.form("form_prod"):
            nazwa_prod = st.text_input("Nazwa produktu")
            liczba
