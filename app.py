import streamlit as st
from supabase_config import supabase
from ml_model import predict_category
from PIL import Image
import uuid
import io
from datetime import datetime

# ---------------- PAGE CONFIG ----------------

st.set_page_config(page_title="Digitale Fundkiste", layout="centered")

st.title("📦 Digitale Fundkiste")

# Session State Init
if "image" not in st.session_state:
    st.session_state.image = None

# ---------------- NAVIGATION ----------------

page = st.radio("Navigation", [
    "Startseite",
    "Eintrag erstellen",
    "Suchen"
])

# =====================================================
# STARTSEITE
# =====================================================

if page == "Startseite":
    st.subheader("Willkommen bei der digitalen Fundkiste")

    st.info("Wähle eine Funktion im Menü.")

# =====================================================
# EINTRAG ERSTELLEN
# =====================================================

elif page == "Eintrag erstellen":

    st.subheader("Neuen Eintrag erstellen")

    typ = st.selectbox("Typ", ["gefunden", "gesucht"])

    uploaded_file = st.file_uploader(
        "Bild hochladen",
        type=["jpg", "jpeg", "png"]
    )

    beschreibung = st.text_area("Beschreibung")

    kategorie = "Sonstiges"

    if uploaded_file:
        image = Image.open(uploaded_file)

        st.image(image, caption="Vorschau", use_container_width=True)

        try:
            kategorie = predict_category(image)
            st.success(f"Automatisch erkannt: {kategorie}")

        except Exception:
            st.warning("ML Klassifikation nicht möglich.")

    if st.button("Speichern"):

        if uploaded_file is None:
            st.error("Bitte zuerst ein Bild hochladen.")
            st.stop()

        try:
            filename = f"{uuid.uuid4()}.jpg"

            image_bytes = io.BytesIO()
            image.save(image_bytes, format="JPEG")
            image_bytes = image_bytes.getvalue()

            # Upload Bild
            supabase.storage.from_("images").upload(
                path=filename,
                file=image_bytes,
                file_options={
                    "content-type": "image/jpeg",
                    "upsert": "true"
                }
            )

            public_url = supabase.storage.from_("images").get_public_url(filename)

            # Datenbank speichern
            supabase.table("fundkiste").insert({
                "bild_url": public_url,
                "kategorie": kategorie,
                "beschreibung": beschreibung,
                "typ": typ,
                "datum": datetime.now().strftime("%d.%m.%Y")
            }).execute()

            st.success("✅ Eintrag gespeichert!")

        except Exception as e:
            st.error(f"Upload Fehler: {str(e)}")

# =====================================================
# SUCHEN
# =====================================================

elif page == "Suchen":

    st.subheader("Einträge durchsuchen")

    filter_typ = st.selectbox("Typ", ["gefunden", "gesucht"])
    filter_kategorie = st.selectbox(
        "Kategorie",
        ["Alle", "Hose", "Mütze", "Pullover", "Sonstiges"]
    )

    suchtext = st.text_input("Beschreibung suchen")

    try:
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

            if st.button("🗑 Löschen", key=eintrag["id"]):

                supabase.table("fundkiste") \
                    .delete() \
                    .eq("id", eintrag["id"]) \
                    .execute()

                st.warning("Eintrag gelöscht!")

    except Exception as e:
        st.error(f"Datenbank Fehler: {str(e)}")
