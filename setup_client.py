#!/usr/bin/env python3
"""
Richtet einen neuen Kunden ein:
  - Erstellt ein neues GitHub Repo aus dem Template
  - Setzt alle Secrets automatisch via GitHub API
  - Gibt Anleitung für Streamlit Cloud Deployment aus

Verwendung:
  python setup_client.py

Voraussetzungen:
  pip install requests PyNaCl
  GitHub Personal Access Token mit Scopes: repo, workflow
"""

import sys
import json
import base64
import secrets
import requests

try:
    from nacl import encoding, public
except ImportError:
    print("Fehlende Abhängigkeit: pip install PyNaCl")
    sys.exit(1)


TEMPLATE_REPO = "wulius0711/social-media-agent"
GITHUB_API = "https://api.github.com"


def ask(prompt: str, default: str = "", secret: bool = False) -> str:
    if secret:
        import getpass
        val = getpass.getpass(f"{prompt}: ").strip()
    else:
        val = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return val or default


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    pk = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    box = public.SealedBox(pk)
    encrypted = box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()


def github_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def create_repo_from_template(gh_token: str, owner: str, new_name: str) -> str:
    url = f"{GITHUB_API}/repos/{TEMPLATE_REPO}/generate"
    r = requests.post(url, headers=github_headers(gh_token), json={
        "owner": owner,
        "name": new_name,
        "private": True,
        "description": f"Social Media Agent für {new_name}",
    })
    if r.status_code == 422:
        print(f"  Repo '{owner}/{new_name}' existiert bereits — verwende es.")
        return f"{owner}/{new_name}"
    r.raise_for_status()
    full_name = r.json()["full_name"]
    print(f"  ✅ Repo erstellt: https://github.com/{full_name}")
    return full_name


def set_secret(gh_token: str, repo_full: str, secret_name: str, secret_value: str):
    if not secret_value:
        return
    key_r = requests.get(
        f"{GITHUB_API}/repos/{repo_full}/actions/secrets/public-key",
        headers=github_headers(gh_token),
    )
    key_r.raise_for_status()
    key_data = key_r.json()
    encrypted = encrypt_secret(key_data["key"], secret_value)
    r = requests.put(
        f"{GITHUB_API}/repos/{repo_full}/actions/secrets/{secret_name}",
        headers=github_headers(gh_token),
        json={"encrypted_value": encrypted, "key_id": key_data["key_id"]},
    )
    r.raise_for_status()


def main():
    print("=" * 60)
    print("  Social Agent — Kunden-Einrichtung")
    print("=" * 60)
    print()

    # ── GitHub Auth ───────────────────────────────────────────────
    print("[ GitHub ]")
    gh_token = ask("Dein GitHub Personal Access Token (repo + workflow Scopes)", secret=True)
    me_r = requests.get(f"{GITHUB_API}/user", headers=github_headers(gh_token))
    me_r.raise_for_status()
    gh_user = me_r.json()["login"]
    print(f"  Eingeloggt als: {gh_user}")
    print()

    # ── Kundendaten ───────────────────────────────────────────────
    print("[ Kunde ]")
    client_slug = ask("Repo-Name (nur Buchstaben/Bindestriche, z.B. mustermann-social)")
    repo_owner = ask("GitHub Owner (dein Username oder Org)", default=gh_user)
    print()

    print("[ Business-Profil ]")
    business_name = ask("Name / Unternehmensname")
    business_desc = ask("Was der Kunde anbietet (1-2 Sätze)")
    business_target = ask("Zielgruppe", default="")
    business_tone = ask("Tonalität", default="direkt, authentisch")
    business_lang = ask("Sprache", default="Deutsch")
    print()

    print("[ API Keys — Enter überspringen wenn nicht vorhanden ]")
    openai_key = ask("OpenAI API Key", secret=True)
    li_token = ask("LinkedIn Access Token", secret=True)
    li_urn = ask("LinkedIn Author URN (urn:li:person:…)", default="")
    ig_user_id = ask("Instagram User ID", default="")
    ig_token = ask("Instagram Access Token", secret=True)
    imgbb_key = ask("imgbb API Key", secret=True)
    print()

    print("[ Post-Einstellungen ]")
    post_length = ask("Post-Länge (Kurz / Mittel / Lang)", default="Mittel")
    post_tone = ask("Ton (Direkt / Sachlich / Storytelling)", default="Direkt")
    hashtag_count = ask("Hashtag-Anzahl", default="10")
    post_li = ask("LinkedIn posten? (true/false)", default="true")
    post_ig = ask("Instagram posten? (true/false)", default="false")
    generate_image = ask("Bilder mit DALL-E 3? (true/false)", default="false")
    print()

    print("[ Posting-Zeitplan ]")
    print("  Tage: 0=So 1=Mo 2=Di 3=Mi 4=Do 5=Fr 6=Sa")
    days_input = ask("Posting-Tage (kommagetrennt)", default="2,5")
    schedule_hour = int(ask("Uhrzeit Wien (Stunde, 6-20)", default="10"))
    schedule_days = [int(d.strip()) for d in days_input.split(",")]
    print()

    # ── Repo erstellen ────────────────────────────────────────────
    print("[ Erstelle GitHub Repo … ]")
    repo_full = create_repo_from_template(gh_token, repo_owner, client_slug)
    print()

    # ── Secrets setzen ────────────────────────────────────────────
    print("[ Setze GitHub Secrets … ]")
    secrets_map = {
        "OPENAI_API_KEY": openai_key,
        "LINKEDIN_ACCESS_TOKEN": li_token,
        "LINKEDIN_AUTHOR_URN": li_urn,
        "INSTAGRAM_USER_ID": ig_user_id,
        "INSTAGRAM_ACCESS_TOKEN": ig_token,
        "IMGBB_API_KEY": imgbb_key,
        "BUSINESS_NAME": business_name,
        "BUSINESS_DESCRIPTION": business_desc,
        "BUSINESS_TARGET": business_target,
        "BUSINESS_TONE_HINTS": business_tone,
        "BUSINESS_LANGUAGE": business_lang,
        "POST_LENGTH": post_length,
        "POST_TONE": post_tone,
        "HASHTAG_COUNT": hashtag_count,
        "POST_LINKEDIN": post_li,
        "POST_INSTAGRAM": post_ig,
        "GENERATE_IMAGE": generate_image,
    }
    for name, value in secrets_map.items():
        if value:
            set_secret(gh_token, repo_full, name, value)
            print(f"  ✅ {name}")
    print()

    # ── Zeitplan im Workflow setzen ───────────────────────────────
    print("[ Aktualisiere Posting-Zeitplan … ]")
    from src.schedule_updater import update_github_schedule
    import time as _time
    _time.sleep(3)  # wait for repo to be ready
    try:
        update_github_schedule(gh_token, repo_full, schedule_days, schedule_hour)
        print(f"  ✅ Zeitplan gesetzt")
    except Exception as e:
        print(f"  ⚠️  Zeitplan konnte nicht gesetzt werden: {e}")
        print("     → Manuell in GitHub Actions → post.yml anpassen")
    print()

    # ── Abschluss ─────────────────────────────────────────────────
    print("=" * 60)
    print("  FERTIG!")
    print("=" * 60)
    print()
    print(f"  GitHub Repo:  https://github.com/{repo_full}")
    print()
    print("  Nächste Schritte:")
    print("  1. Gehe zu https://share.streamlit.io")
    print("  2. 'New app' → wähle das Repo aus")
    print(f"     Repo: {repo_full}")
    print("     Branch: main")
    print("     Main file: streamlit_app.py")
    print("  3. App deployen → Link an Kunden schicken")
    print("  4. Kunde verbindet LinkedIn selbst über die App (Onboarding)")
    print()
    print("  GitHub Actions (automatisches Posten):")
    print(f"  https://github.com/{repo_full}/actions")
    print()


if __name__ == "__main__":
    main()
