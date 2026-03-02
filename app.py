import streamlit as st
from supabase_config import supabase
from ml_model import predict_category
from PIL import Image
import uuid
import io
from datetime import datetime

st.set_page_config(page_title="Digitale Fundkiste", layout="centered")

st.title("📦 Digitale Fundkiste")

page = st.radio("Navigation", ["Startseite", "Eintrag erstellen", "Suchen"])

# ---------------- STARTSEITE ----------------

if page == "Startseite":
    st.subheader("Was möchtest du tun?")
    st.write("Wähle eine Option im Menü.")

# ---------------- EINTRAG ERSTELLEN ----------------

elif page == "Eintrag erstellen":

    st.subheader("Neuen Eintrag erstellen")

    typ = st.selectbox("Typ", ["gefunden", "gesucht"])

    uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"])
    beschreibung = st.text_area("Beschreibung")

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Vorschau", use_column_width=True)

        kategorie = predict_category(image)
        st.success(f"Automatisch erkannte Kategorie: {kategorie}")

    if st.button("Speichern") and uploaded_file:

        filename = f"{uuid.uuid4()}.jpg"

        image_bytes = io.BytesIO()
        image.save(image_bytes, format="JPEG")

        supabase.storage.from_("images").upload(
            filename,
            image_bytes.getvalue(),
            {"content-type": "image/jpeg"}
        )

        public_url = supabase.storage.from_("images").get_public_url(filename)

        supabase.table("fundkiste").insert({
            "bild_url": public_url,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "typ": typ,
            "datum": datetime.now().strftime("%d.%m.%Y")
        }).execute()

        st.success("Eintrag gespeichert!")

# ---------------- SUCHEN ----------------

elif page == "Suchen":

    st.subheader("Einträge durchsuchen")

    filter_typ = st.selectbox("Typ", ["gefunden", "gesucht"])
    filter_kategorie = st.selectbox("Kategorie", ["Alle", "Hose", "Mütze", "Pullover", "Sonstiges"])
    suchtext = st.text_input("Beschreibung durchsuchen")

    response = supabase.table("fundkiste").select("*").execute()

    for eintrag in response.data:

        if eintrag["typ"] != filter_typ:
            continue

        if filter_kategorie != "Alle" and eintrag["kategorie"] != filter_kategorie:
            continue

        if suchtext.lower() not in eintrag["beschreibung"].lower():
            continue

        st.image(eintrag["bild_url"], width=200)
        st.write(f"**Kategorie:** {eintrag['kategorie']}")
        st.write(f"**Beschreibung:** {eintrag['beschreibung']}")
        st.write(f"**Datum:** {eintrag['datum']}")

        if st.button("Löschen", key=eintrag["id"]):
            supabase.table("fundkiste").delete().eq("id", eintrag["id"]).execute()
            st.warning("Eintrag gelöscht!")
