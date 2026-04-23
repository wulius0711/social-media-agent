import streamlit as st

st.title("📖 Handbuch")
st.caption("Alles was du wissen musst, um den Social Agent zu nutzen.")

# ── Navigation ────────────────────────────────────────────────────────────────

sections = [
    "Überblick",
    "Post erstellen",
    "Genehmigung & Bearbeitung",
    "Automatisches Posten",
    "Einstellungen anpassen",
    "LinkedIn Token erneuern",
    "Häufige Fragen",
]

with st.sidebar:
    st.divider()
    st.caption("Handbuch — Inhalt")
    for s in sections:
        st.markdown(f"→ [{s}](#{s.lower().replace(' ', '-').replace('&', '').replace('ü', 'u').replace('ä', 'a').replace('ö', 'o')})")

# ── 1. Überblick ──────────────────────────────────────────────────────────────

st.header("Überblick")
st.markdown("""
Der **Social Agent** schreibt automatisch LinkedIn- und Instagram-Posts in deiner Stimme —
auf Basis deines Business-Profils und deiner Tonalität.

**Was der Agent macht:**
- Generiert Posts mit GPT-4o (OpenAI)
- Optional: erstellt ein passendes Bild mit DALL-E 3
- Postet automatisch 2x pro Woche (Dienstag + Freitag, 10:00 Uhr)
- Oder: du erstellst und postest manuell, wann du willst

**Was du tun musst:**
- Nichts — wenn du dem automatischen Ablauf vertraust
- Oder: Posts vor dem Veröffentlichen prüfen und freigeben (empfohlen)
""")

st.divider()

# ── 2. Post erstellen ─────────────────────────────────────────────────────────

st.header("Post erstellen")
st.markdown("""
Gehe zu **🏠 Post erstellen** (Hauptseite).

**Thema eingeben (optional)**
Lasse das Feld leer → der Agent wählt automatisch ein Thema aus deiner Branche.
Oder gib ein konkretes Thema ein, z.B. *„Warum Webdesign mehr als Ästhetik ist"*.

**Einstellungen (Sidebar):**

| Einstellung | Optionen | Empfehlung |
|---|---|---|
| Plattformen | LinkedIn, Instagram | LinkedIn aktiv |
| Länge | Kurz / Mittel / Lang | Mittel |
| Ton | Direkt / Sachlich / Storytelling | Direkt |
| Hashtags | 5 – 15 | 10 |
| Bild (DALL-E 3) | An / Aus | Aus (spart Kosten) |

**Dann:**
1. Klicke **✨ Generieren**
2. Lies den generierten Text in den Tabs (LinkedIn, Instagram …)
3. Bearbeite ihn direkt im Textfeld falls gewünscht
4. Optional: **Bild oder Video hochladen** (siehe unten)
5. Wähle:
   - **📋 Zur Genehmigung senden** → Post landet in der Warteschlange (empfohlen)
   - **📤 Direkt posten** → Post geht sofort raus

**Eigene Bilder & Videos hochladen:**

Unterhalb der Textvorschau findest du zwei Upload-Felder:

| Upload | Formate | Plattform |
|---|---|---|
| Bild | JPG, PNG, WEBP | LinkedIn + Instagram |
| Video | MP4, MOV, AVI | LinkedIn (Video-Post) + Instagram (Reel) |

- Kein Upload → DALL-E Bild wird verwendet (wenn aktiviert), oder nur Text
- Bild Upload → ersetzt DALL-E Bild
- Video Upload → wird als Reel (Instagram) und Video-Post (LinkedIn) gepostet

Für Videos wird ein **Cloudinary-Konto** benötigt (kostenlos, cloudinary.com).
→ Schritt-für-Schritt Anleitung und Videoformat-Anforderungen: siehe **„Wie lade ich ein Video hoch?"** in den Häufigen Fragen weiter unten.
""")

st.info("Tipp: 'Zur Genehmigung senden' gibt dir die Möglichkeit, den Text nochmal in Ruhe zu lesen bevor er live geht.")

st.divider()

# ── 3. Genehmigung ────────────────────────────────────────────────────────────

st.header("Genehmigung & Bearbeitung")
st.markdown("""
Gehe zu **✅ Genehmigung**.

Hier siehst du alle Posts die auf deine Freigabe warten.

**Pro Post hast du drei Optionen:**

**✅ Genehmigen** — markiert den Post als freigegeben, postet ihn aber noch nicht.
Nützlich wenn du erst sammeln und dann manuell entscheiden willst wann er rausgeht.

**📤 Genehmigen & Posten** — gibt frei und postet sofort auf die gewählten Plattformen.

**❌ Ablehnen** — verwirft den Post. Optional kannst du einen Grund eingeben
(z.B. *„Ton passt nicht"*) — das hilft dir den Überblick zu behalten.

Du kannst den Text **direkt im Textfeld bearbeiten** bevor du auf Genehmigen klickst —
kein extra Schritt nötig.
""")

st.divider()

# ── 4. Automatisches Posten ───────────────────────────────────────────────────

st.header("Automatisches Posten")
st.markdown("""
Der Agent postet automatisch **jeden Dienstag und Freitag um 10:00 Uhr** (Wien).

**Wie das funktioniert:**
Im Hintergrund läuft ein GitHub Actions Workflow der zu diesen Zeiten automatisch startet,
einen Post generiert und direkt auf LinkedIn (und Instagram, falls verbunden) veröffentlicht —
ganz ohne dass du etwas tun musst.

**Manuell auslösen:**
Du kannst jederzeit einen Extra-Post manuell starten:
1. Gehe zu deinem GitHub Repo → Reiter **Actions**
2. Klicke links auf **„Social Media Post"**
3. Klicke rechts auf **„Run workflow"** → **„Run workflow"**

**Automatik + manuelle Kontrolle kombinieren:**
Wenn du möchtest dass der Agent zwar automatisch generiert aber du jeden Post freigibst,
müsstest du das Workflow-Skript anpassen (sprich dazu deinen Betreuer an).
""")

st.divider()

# ── 5. Einstellungen ──────────────────────────────────────────────────────────

st.header("Einstellungen anpassen")
st.markdown("""
Gehe zu **⚙️ Einstellungen**.

**Business-Profil** — das Herzstück des Agenten.
Je konkreter du beschreibst was du machst und wie du kommunizierst,
desto besser trifft der Agent deinen Ton.

Gute Beschreibungen enthalten:
- Was du anbietest und für wen
- Wie du dich von anderen abhebst
- Beispielformulierungen deiner Tonalität

**API Keys** — hier trägst du deine Zugangsdaten ein (einmalig).
Diese werden verschlüsselt gespeichert und nie weitergegeben.

**Änderungen speichern** — immer auf **💾 Einstellungen speichern** klicken!
""")

st.divider()

# ── 6. LinkedIn Token ─────────────────────────────────────────────────────────

st.header("LinkedIn Token erneuern")
st.markdown("""
LinkedIn Access Tokens laufen nach **60 Tagen** ab.

Die App zeigt dir rechtzeitig eine Warnung wenn es so weit ist.

**Token erneuern:**
1. Gehe zu **⚙️ Einstellungen** → Abschnitt *„LinkedIn neu verbinden"*
2. Trage deine LinkedIn App Client ID und Client Secret ein
3. Klicke **🔗 LinkedIn verbinden**
4. Ein Browser-Fenster öffnet sich → mit LinkedIn einloggen und bestätigen
5. Fertig — neuer Token ist gespeichert

Du brauchst dafür deine LinkedIn Developer App (Client ID + Secret).
Diese findest du unter: [linkedin.com/developers/apps](https://www.linkedin.com/developers/apps)
""")

st.divider()

# ── 7. FAQ ────────────────────────────────────────────────────────────────────

st.header("Häufige Fragen")

with st.expander("Der generierte Post klingt nicht wie ich — was tun?"):
    st.markdown("""
Gehe zu ⚙️ Einstellungen und verfeinere das Feld **„Deine Stimme / Tonalität"**.
Konkrete Beispiele helfen am meisten, z.B.:
*„Ich sage nie 'innovativ' oder 'nachhaltig'. Ich erkläre lieber an einem konkreten Beispiel was ich meine."*
    """)

with st.expander("Kann ich das Thema für den automatischen Post selbst bestimmen?"):
    st.markdown("""
Noch nicht direkt. Der automatische Workflow wählt ein zufälliges Thema aus einer Liste.
Wenn du ein konkretes Thema möchtest, nutze **🏠 Post erstellen** → Thema eingeben → manuell posten.
    """)

with st.expander("Was kostet ein generierter Post?"):
    st.markdown("""
Ein Post mit GPT-4o kostet ca. **0,01–0,03 €** (je nach Länge).
Ein Bild mit DALL-E 3 kostet ca. **0,04 €** pro Bild.
Bei 2 Posts pro Woche ca. **1–3 € pro Monat** für die OpenAI API.
    """)

with st.expander("Wie lade ich ein Video hoch?"):
    st.markdown("""
Auf der Hauptseite (🏠 Post erstellen) findest du unter den Textvorschauen
zwei Upload-Felder — eines für Bilder, eines für Videos.

**Schritt 1 — Cloudinary einrichten (einmalig, kostenlos):**
1. cloudinary.com → Registrieren
2. Dashboard → Cloud Name, API Key, API Secret kopieren
3. In ⚙️ Einstellungen → Cloudinary eintragen → Speichern

**Schritt 2 — Video vorbereiten:**

| | Instagram Reel | LinkedIn |
|---|---|---|
| Format | MP4, H.264 | MP4 |
| Max. Länge | 90 Sekunden | 10 Minuten |
| Max. Größe | — | 5 GB |
| Empfohlenes Format | 9:16 (Hochformat) | 16:9 oder 1:1 |

**Schritt 3 — Hochladen & posten:**
Video hochladen → **📤 Direkt posten** klicken.
Das Video wird automatisch auf Cloudinary hochgeladen, LinkedIn und Instagram erhalten die URL.

⚠️ LinkedIn verarbeitet Videos nach dem Upload noch **1–3 Minuten** — der Post erscheint danach automatisch.
    """)

with st.expander("Kann ich auch auf Facebook oder TikTok posten?"):
    st.markdown("""
Die Tabs für Facebook und TikTok sind sichtbar, aber noch nicht verbunden.
Das ist für zukünftige Updates geplant.
    """)

with st.expander("Was passiert wenn der automatische Post fehlschlägt?"):
    st.markdown("""
Du bekommst keine automatische E-Mail. Du kannst den Status unter
[github.com → dein Repo → Actions](https://github.com) prüfen.
Ein roter Kreis bedeutet Fehler → klicke drauf für Details.
Häufigste Ursache: LinkedIn Token abgelaufen → einfach erneuern (siehe oben).
    """)

with st.expander("Wie ändere ich die Posting-Tage oder -Uhrzeit?"):
    st.markdown("""
Geh zu **⚙️ Einstellungen** → Abschnitt **Posting-Zeitplan**.
Dort kannst du Wochentage (Mehrfachauswahl) und Uhrzeit (Wiener Zeit) selbst festlegen und mit **Zeitplan speichern** direkt aktivieren — kein Support nötig.
    """)

st.divider()
st.caption("Bei Fragen oder Problemen: werbesan@gmail.com")
