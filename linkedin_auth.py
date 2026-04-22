#!/usr/bin/env python3
"""Run once to get LinkedIn access token + person URN and save to .env."""
import http.server
import threading
import urllib.parse
import webbrowser
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = input("LinkedIn Client ID (aus dem Auth-Tab deiner App): ").strip()
CLIENT_SECRET = input("LinkedIn Client Secret: ").strip()

REDIRECT_URI = "http://localhost:8765/callback"
SCOPES = "openid profile w_member_social"
AUTH_URL = (
    f"https://www.linkedin.com/oauth/v2/authorization"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope={urllib.parse.quote(SCOPES)}"
    f"&state=wolfgangagent"
)

auth_code = None

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Fertig! Du kannst diesen Tab schliessen.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Fehler: kein Code erhalten.")

    def log_message(self, *args):
        pass

server = http.server.HTTPServer(("localhost", 8765), CallbackHandler)
thread = threading.Thread(target=server.handle_request)
thread.start()

print("\nBrowser öffnet sich... bitte einloggen und bestätigen.")
webbrowser.open(AUTH_URL)
thread.join(timeout=120)

if not auth_code:
    print("Fehler: kein Auth-Code erhalten.")
    exit(1)

# Token holen
token_resp = requests.post(
    "https://www.linkedin.com/oauth/v2/accessToken",
    data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
)
token_resp.raise_for_status()
access_token = token_resp.json()["access_token"]

# Person-ID holen
userinfo_resp = requests.get(
    "https://api.linkedin.com/v2/userinfo",
    headers={"Authorization": f"Bearer {access_token}"},
)
userinfo_resp.raise_for_status()
person_id = userinfo_resp.json()["sub"]
author_urn = f"urn:li:person:{person_id}"

print(f"\nErfolgreich!")
print(f"Access Token: {access_token[:30]}...")
print(f"Author URN:   {author_urn}")

# In .env schreiben
env_path = os.path.join(os.path.dirname(__file__), ".env")
with open(env_path, "r") as f:
    content = f.read()

content = re.sub(r"LINKEDIN_ACCESS_TOKEN=.*", f"LINKEDIN_ACCESS_TOKEN={access_token}", content)
content = re.sub(r"LINKEDIN_AUTHOR_URN=.*", f"LINKEDIN_AUTHOR_URN={author_urn}", content)

with open(env_path, "w") as f:
    f.write(content)

print("\nBeide Werte wurden automatisch in .env gespeichert.")
