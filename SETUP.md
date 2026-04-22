# Setup-Anleitung: Social Media Agent

## 1. Python-Abhängigkeiten installieren

```bash
cd ~/social-media-agent
pip3 install -r requirements.txt
```

---

## 2. .env Datei anlegen

```bash
cp .env.example .env
```

Dann `.env` befüllen (Schritt 3-6 liefern alle Werte).

---

## 3. Anthropic API Key (Claude)

1. Gehe zu https://console.anthropic.com
2. API Keys → Create Key
3. In `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

---

## 4. OpenAI API Key (DALL-E 3)

1. Gehe zu https://platform.openai.com/api-keys
2. Create new secret key
3. In `.env`: `OPENAI_API_KEY=sk-...`

---

## 5. Instagram (Meta Graph API)

### Voraussetzungen
- Instagram Business oder Creator Account
- Verbunden mit einer Facebook-Seite (falls nicht: Instagram → Einstellungen → Account → Zu Professional wechseln)

### App erstellen
1. https://developers.facebook.com → "Meine Apps" → App erstellen
2. Typ: **Business**
3. Produkt hinzufügen: **Instagram Graph API**

### Instagram User ID
1. Graph API Explorer: https://developers.facebook.com/tools/explorer
2. Wähle deine App und deine Facebook-Seite
3. Anfrage: `GET me/accounts` → kopiere die Page ID
4. Anfrage: `GET {page-id}?fields=instagram_business_account`
5. Kopiere die `id` → das ist deine `INSTAGRAM_USER_ID`

### Access Token (long-lived, ~60 Tage)
1. Im Graph API Explorer: Generate Access Token (mit Berechtigung `instagram_basic`, `instagram_content_publish`)
2. Token verlängern via:
   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id={APP_ID}
     &client_secret={APP_SECRET}
     &fb_exchange_token={SHORT_TOKEN}
   ```
3. In `.env`: `INSTAGRAM_ACCESS_TOKEN=EAAxxxxx...`

> **Hinweis:** Token läuft nach ~60 Tagen ab. Dann einfach neu generieren.

---

## 6. LinkedIn API

### App erstellen
1. https://www.linkedin.com/developers/apps → Create App
2. Company Page verknüpfen (eigene LinkedIn-Seite oder persönliches Profil)
3. Products: **Share on LinkedIn** aktivieren lassen (meist sofort genehmigt)

### OAuth Token holen
1. In der App: Auth → OAuth 2.0 Tools
2. Scopes wählen: `w_member_social`, `r_liteprofile`
3. Token generieren
4. In `.env`: `LINKEDIN_ACCESS_TOKEN=AQxxxxx...`

### Author URN
1. Anfrage: `GET https://api.linkedin.com/v2/me` mit deinem Token (z.B. via Postman oder curl)
   ```bash
   curl -H "Authorization: Bearer DEIN_TOKEN" https://api.linkedin.com/v2/me
   ```
2. Kopiere den `id`-Wert aus der Antwort
3. In `.env`: `LINKEDIN_AUTHOR_URN=urn:li:person:{id}`

> **Hinweis:** LinkedIn-Tokens laufen nach 60 Tagen ab.

---

## 7. imgbb (kostenloses Image-Hosting)

Instagram benötigt eine öffentlich erreichbare Bild-URL — imgbb hostet das temporär.

1. https://imgbb.com → Account erstellen (kostenlos)
2. https://api.imgbb.com → API Key generieren
3. In `.env`: `IMGBB_API_KEY=xxxxxxxx`

---

## 8. Manuell testen

```bash
cd ~/social-media-agent
python3 main.py
```

Prüfe danach `logs/agent.log` für Details.

---

## 9. Automatisch ausführen (Di + Fr, 10:00 Uhr)

```bash
# Plist in launchd registrieren
cp ~/social-media-agent/com.wolfgangheis.socialagent.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.wolfgangheis.socialagent.plist
```

**Deaktivieren:**
```bash
launchctl unload ~/Library/LaunchAgents/com.wolfgangheis.socialagent.plist
```

**Sofort manuell triggern (zum Testen):**
```bash
launchctl start com.wolfgangheis.socialagent
```

> **Wichtig:** Der Mac muss zu den Posting-Zeiten eingeschaltet sein. Bei Schlafmodus wird der Job beim nächsten Start nachgeholt (wenn `RunAtLoad` auf `true` gesetzt wird — sonst nicht).

---

## Token-Erneuerung (alle ~60 Tage)

Beide Tokens (Instagram + LinkedIn) laufen nach ~60 Tagen ab. Einfach neu generieren und in `.env` eintragen.
Optional: Erinnerung im Kalender setzen.

---

## Kosten (Schätzung pro Monat bei 2x/Woche)

| Service | Kosten |
|---------|--------|
| Claude Sonnet | ~$0.10 |
| DALL-E 3 (8 Bilder) | ~$0.32 |
| imgbb | kostenlos |
| **Gesamt** | **~$0.42/Monat** |
