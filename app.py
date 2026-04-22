#!/usr/bin/env python3
import os
import sys
import threading
import platform
import http.server
import urllib.parse
import webbrowser
import customtkinter as ctk
from pathlib import Path

# Config must load before any src imports
from src import config as cfg
cfg.apply_to_env()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

GREEN  = "#16a34a"
RED    = "#dc2626"
GRAY   = "gray60"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _entry_row(parent, label, row, show="", width=380):
    ctk.CTkLabel(parent, text=label, text_color=GRAY, font=ctk.CTkFont(size=12)).grid(
        row=row, column=0, sticky="w", padx=20, pady=(10, 0)
    )
    e = ctk.CTkEntry(parent, width=width, show=show, font=ctk.CTkFont(size=13))
    e.grid(row=row + 1, column=0, sticky="w", padx=20, pady=(2, 0))
    return e


def _section_label(parent, text, row):
    ctk.CTkLabel(
        parent, text=text.upper(),
        text_color=GRAY, font=ctk.CTkFont(size=10, weight="bold")
    ).grid(row=row, column=0, sticky="w", padx=20, pady=(20, 4))


# ── Setup Wizard ───────────────────────────────────────────────────────────────

class SetupWizard(ctk.CTkToplevel):
    def __init__(self, master, on_complete):
        super().__init__(master)
        self.title("Einrichtung · Wolfgang Social Agent")
        self.geometry("560x520")
        self.resizable(False, False)
        self.grab_set()
        self._on_complete = on_complete
        self._step = 0
        self._data = cfg.load()
        self._steps = [
            self._step_welcome,
            self._step_business,
            self._step_openai,
            self._step_imgbb,
            self._step_linkedin,
            self._step_platforms,
            self._step_done,
        ]
        self._frame = None
        self._show_step()

    def _show_step(self):
        if self._frame:
            self._frame.destroy()
        self._frame = ctk.CTkFrame(self, fg_color="transparent")
        self._frame.pack(fill="both", expand=True, padx=32, pady=32)
        self._steps[self._step]()

    def _nav(self, back=True, next_text="Weiter →", next_cmd=None):
        row = ctk.CTkFrame(self._frame, fg_color="transparent")
        row.pack(side="bottom", fill="x", pady=(16, 0))
        if back and self._step > 0:
            ctk.CTkButton(row, text="← Zurück", width=100, fg_color="transparent",
                          border_width=1, command=self._back).pack(side="left")
        ctk.CTkButton(row, text=next_text, width=140,
                      command=next_cmd or self._next).pack(side="right")

    def _next(self):
        self._step += 1
        self._show_step()

    def _back(self):
        self._step -= 1
        self._show_step()

    def _title(self, text):
        ctk.CTkLabel(self._frame, text=text,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(0, 6))

    def _body(self, text):
        ctk.CTkLabel(self._frame, text=text, text_color=GRAY,
                     font=ctk.CTkFont(size=13), wraplength=480, justify="left").pack(anchor="w", pady=(0, 20))

    # Steps ────────────────────────────────────────────────────────────────────

    def _step_welcome(self):
        self._title("Willkommen!")
        self._body(
            "Dieser Assistent richtet deinen Social Media Agenten ein.\n\n"
            "Du brauchst:\n"
            "  • OpenAI API Key (für Texte + Bilder)\n"
            "  • imgbb API Key (kostenloses Bild-Hosting)\n"
            "  • LinkedIn Account\n"
            "  • Optional: Instagram Business Account"
        )
        self._nav(back=False)

    def _step_business(self):
        self._title("Dein Business-Profil")
        self._body("Diese Infos nutzt der Agent um Content in deiner Stimme zu schreiben.")

        fields = [
            ("Dein Name / Unternehmensname", "business_name", False, "z.B. Maria Müller"),
            ("Was du anbietest & dein Hintergrund", "business_description", True,
             "z.B. Ich bin Ernährungsberaterin mit 10 Jahren Erfahrung …"),
            ("Deine Zielgruppe", "business_target", False,
             "z.B. Frauen 30-50 die gesünder leben wollen"),
            ("Deine Stimme / Tonalität", "business_tone_hints", False,
             "z.B. warmherzig, direkt, keine Fachwörter"),
        ]
        self._biz_entries = {}
        for label, key, multiline, placeholder in fields:
            ctk.CTkLabel(self._frame, text=label, text_color=GRAY,
                         font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
            if multiline:
                e = ctk.CTkTextbox(self._frame, width=460, height=72,
                                   font=ctk.CTkFont(size=12))
                v = self._data.get(key, "")
                if v:
                    e.insert("end", v)
                else:
                    e.insert("end", placeholder)
                    e.configure(text_color=GRAY)
            else:
                e = ctk.CTkEntry(self._frame, width=460, placeholder_text=placeholder,
                                 font=ctk.CTkFont(size=12))
                v = self._data.get(key, "")
                if v:
                    e.insert(0, v)
            e.pack(anchor="w")
            self._biz_entries[key] = (e, multiline)

        ctk.CTkLabel(self._frame, text="Sprache", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self._seg_lang = ctk.CTkSegmentedButton(
            self._frame, values=["Deutsch", "Englisch", "Französisch", "Spanisch", "Italienisch"]
        )
        self._seg_lang.set(self._data.get("business_language", "Deutsch"))
        self._seg_lang.pack(anchor="w")

        self._nav(next_cmd=self._save_business)

    def _save_business(self):
        for key, (widget, multiline) in self._biz_entries.items():
            if multiline:
                v = widget.get("1.0", "end").strip()
            else:
                v = widget.get().strip()
            self._data[key] = v
        self._data["business_language"] = self._seg_lang.get()
        cfg.save(self._data)
        self._next()

    def _step_openai(self):
        self._title("OpenAI API Key")
        self._body("Unter platform.openai.com/api-keys → 'Create new secret key'")
        self._e_openai = ctk.CTkEntry(self._frame, width=460, show="•",
                                       placeholder_text="sk-proj-...",
                                       font=ctk.CTkFont(size=13))
        self._e_openai.pack(anchor="w")
        v = self._data.get("openai_api_key", "")
        if v:
            self._e_openai.insert(0, v)
        self._lbl = ctk.CTkLabel(self._frame, text="", text_color=RED)
        self._lbl.pack(anchor="w", pady=(4, 0))
        self._nav(next_cmd=self._save_openai)

    def _save_openai(self):
        v = self._e_openai.get().strip()
        if not v.startswith("sk-"):
            self._lbl.configure(text="Bitte gültigen API Key eingeben.")
            return
        self._data["openai_api_key"] = v
        cfg.save(self._data)
        cfg.apply_to_env()
        self._next()

    def _step_imgbb(self):
        self._title("imgbb API Key")
        self._body("Kostenlos unter imgbb.com registrieren → api.imgbb.com")
        self._e_imgbb = ctk.CTkEntry(self._frame, width=460, show="•",
                                      placeholder_text="xxxxxxxx",
                                      font=ctk.CTkFont(size=13))
        self._e_imgbb.pack(anchor="w")
        v = self._data.get("imgbb_api_key", "")
        if v:
            self._e_imgbb.insert(0, v)
        self._lbl = ctk.CTkLabel(self._frame, text="", text_color=RED)
        self._lbl.pack(anchor="w", pady=(4, 0))
        self._nav(next_cmd=self._save_imgbb)

    def _save_imgbb(self):
        v = self._e_imgbb.get().strip()
        if not v:
            self._lbl.configure(text="Bitte API Key eingeben.")
            return
        self._data["imgbb_api_key"] = v
        cfg.save(self._data)
        cfg.apply_to_env()
        self._next()

    def _step_linkedin(self):
        self._title("LinkedIn verbinden")
        self._body(
            "Klicke auf 'LinkedIn verbinden'. Der Browser öffnet sich — "
            "einloggen und bestätigen. Token wird automatisch gespeichert."
        )
        self._lbl_li = ctk.CTkLabel(self._frame, text="", text_color=GRAY,
                                     font=ctk.CTkFont(size=12), wraplength=460)
        self._lbl_li.pack(anchor="w", pady=(0, 12))

        if self._data.get("linkedin_access_token"):
            self._lbl_li.configure(text="✓ Bereits verbunden", text_color=GREEN)

        self._btn_li = ctk.CTkButton(self._frame, text="LinkedIn verbinden",
                                      command=self._do_linkedin_auth)
        self._btn_li.pack(anchor="w")

        client_frame = ctk.CTkFrame(self._frame, fg_color="transparent")
        client_frame.pack(anchor="w", fill="x", pady=(16, 0))
        ctk.CTkLabel(client_frame, text="Client ID:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w")
        self._e_client_id = ctk.CTkEntry(client_frame, width=200, font=ctk.CTkFont(size=12))
        self._e_client_id.grid(row=0, column=1, padx=(8, 20))
        ctk.CTkLabel(client_frame, text="Client Secret:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).grid(row=0, column=2, sticky="w")
        self._e_client_secret = ctk.CTkEntry(client_frame, width=200, show="•",
                                              font=ctk.CTkFont(size=12))
        self._e_client_secret.grid(row=0, column=3, padx=(8, 0))

        self._nav(next_cmd=self._check_linkedin_done)

    def _do_linkedin_auth(self):
        client_id = self._e_client_id.get().strip()
        client_secret = self._e_client_secret.get().strip()
        if not client_id or not client_secret:
            self._lbl_li.configure(text="Bitte Client ID und Secret eingeben.", text_color=RED)
            return
        self._btn_li.configure(state="disabled", text="Warte auf Browser …")
        self._lbl_li.configure(text="Browser geöffnet — bitte bestätigen …", text_color=GRAY)
        threading.Thread(target=self._linkedin_auth_worker,
                         args=(client_id, client_secret), daemon=True).start()

    def _linkedin_auth_worker(self, client_id, client_secret):
        import requests as req
        redirect = "http://localhost:8765/callback"
        scopes = "openid profile w_member_social"
        auth_url = (
            f"https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code&client_id={client_id}"
            f"&redirect_uri={urllib.parse.quote(redirect)}"
            f"&scope={urllib.parse.quote(scopes)}&state=wsa"
        )
        code_holder = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if "code" in params:
                    code_holder.append(params["code"][0])
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h2>Fertig! Diesen Tab schliessen.</h2>")
            def log_message(self, *a): pass

        server = http.server.HTTPServer(("localhost", 8765), Handler)
        webbrowser.open(auth_url)
        server.handle_request()

        if not code_holder:
            self.after(0, self._lbl_li.configure, {"text": "Fehler: kein Code erhalten.", "text_color": RED})
            self.after(0, self._btn_li.configure, {"state": "normal", "text": "LinkedIn verbinden"})
            return

        try:
            tr = req.post("https://www.linkedin.com/oauth/v2/accessToken", data={
                "grant_type": "authorization_code",
                "code": code_holder[0],
                "redirect_uri": redirect,
                "client_id": client_id,
                "client_secret": client_secret,
            })
            tr.raise_for_status()
            token = tr.json()["access_token"]

            ui = req.get("https://api.linkedin.com/v2/userinfo",
                         headers={"Authorization": f"Bearer {token}"})
            ui.raise_for_status()
            person_id = ui.json()["sub"]
            urn = f"urn:li:person:{person_id}"

            self._data["linkedin_access_token"] = token
            self._data["linkedin_author_urn"] = urn
            cfg.save(self._data)
            cfg.apply_to_env()
            self.after(0, self._lbl_li.configure,
                       {"text": f"✓ Verbunden ({urn})", "text_color": GREEN})
        except Exception as e:
            self.after(0, self._lbl_li.configure,
                       {"text": f"Fehler: {e}", "text_color": RED})
        finally:
            self.after(0, self._btn_li.configure,
                       {"state": "normal", "text": "Erneut verbinden"})

    def _check_linkedin_done(self):
        if not self._data.get("linkedin_access_token"):
            self._lbl_li.configure(text="Bitte zuerst LinkedIn verbinden.", text_color=RED)
            return
        self._next()

    def _step_platforms(self):
        self._title("Plattformen")
        self._body("Instagram ist optional — du kannst es jederzeit in Einstellungen nachrüsten.")

        self._sw_instagram = ctk.BooleanVar(value=self._data.get("post_instagram", False))
        ctk.CTkSwitch(self._frame, text="Instagram aktivieren",
                      variable=self._sw_instagram).pack(anchor="w", pady=4)

        self._insta_frame = ctk.CTkFrame(self._frame, fg_color="transparent")
        self._insta_frame.pack(anchor="w", fill="x", pady=(8, 0))

        ctk.CTkLabel(self._insta_frame, text="Instagram User ID:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w")
        self._e_ig_id = ctk.CTkEntry(self._insta_frame, width=180, font=ctk.CTkFont(size=12))
        self._e_ig_id.grid(row=0, column=1, padx=8)
        v = self._data.get("instagram_user_id", "")
        if v and v != "123456789":
            self._e_ig_id.insert(0, v)

        ctk.CTkLabel(self._insta_frame, text="Access Token:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self._e_ig_token = ctk.CTkEntry(self._insta_frame, width=320, show="•",
                                         font=ctk.CTkFont(size=12))
        self._e_ig_token.grid(row=1, column=1, padx=8, pady=(8, 0))
        v2 = self._data.get("instagram_access_token", "")
        if v2 and v2 != "EAAxxxxx...":
            self._e_ig_token.insert(0, v2)

        self._nav(next_cmd=self._save_platforms)

    def _save_platforms(self):
        self._data["post_instagram"] = self._sw_instagram.get()
        uid = self._e_ig_id.get().strip()
        tok = self._e_ig_token.get().strip()
        if uid:
            self._data["instagram_user_id"] = uid
        if tok:
            self._data["instagram_access_token"] = tok
        cfg.save(self._data)
        cfg.apply_to_env()
        self._next()

    def _step_done(self):
        self._title("Fertig!")
        self._body(
            "Dein Social Media Agent ist eingerichtet.\n\n"
            "Du kannst jetzt Posts generieren, Vorschauen bearbeiten und posten.\n"
            "Den automatischen Zeitplan findest du im Tab 'Einstellungen'."
        )
        self._data["setup_complete"] = True
        cfg.save(self._data)

        def _finish():
            self.destroy()
            self._on_complete()

        ctk.CTkButton(self._frame, text="App öffnen →", width=160,
                      fg_color=GREEN, hover_color="#15803d",
                      command=_finish).pack(anchor="w", pady=(16, 0))
        ctk.CTkButton(self._frame, text="← Zurück", width=100,
                      fg_color="transparent", border_width=1,
                      command=self._back).pack(anchor="w", pady=(8, 0))


# ── Main App ───────────────────────────────────────────────────────────────────

class SocialAgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Wolfgang Social Agent")
        self.geometry("1080x700")
        self.minsize(860, 580)
        self._ig_content = None
        self._li_content = None
        self._build()
        self._load_settings_into_ui()

        if not cfg.get("setup_complete"):
            self.after(500, self._show_wizard)

    def _show_wizard(self):
        self.update()
        SetupWizard(self, on_complete=self._load_settings_into_ui)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._tabs = ctk.CTkTabview(self, anchor="nw")
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        for name in ["Posten", "Einstellungen", "Verlauf"]:
            self._tabs.add(name)
        self._build_posten(self._tabs.tab("Posten"))
        self._build_einstellungen(self._tabs.tab("Einstellungen"))
        self._build_verlauf(self._tabs.tab("Verlauf"))

    # ── Tab: Posten ────────────────────────────────────────────────────────────

    def _build_posten(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Topic row
        topic_row = ctk.CTkFrame(tab, fg_color="transparent")
        topic_row.grid(row=0, column=0, sticky="ew", pady=(8, 0))
        topic_row.grid_columnconfigure(0, weight=1)
        self._e_topic = ctk.CTkEntry(
            topic_row, placeholder_text="Thema eingeben oder leer lassen für zufälliges …",
            height=40, font=ctk.CTkFont(size=13)
        )
        self._e_topic.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self._btn_gen = ctk.CTkButton(
            topic_row, text="Vorschau generieren", width=190, height=40,
            font=ctk.CTkFont(size=13, weight="bold"), command=self._on_generate
        )
        self._btn_gen.grid(row=0, column=1)

        # Controls row — direkt über Preview, kein Gap
        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.grid(row=1, column=0, sticky="ew", pady=(8, 4))

        # Platforms
        ctk.CTkLabel(ctrl, text="Plattformen:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))
        self._sw_li = ctk.BooleanVar(value=True)
        self._sw_ig = ctk.BooleanVar(value=False)
        self._sw_fb = ctk.BooleanVar(value=False)
        self._sw_tt = ctk.BooleanVar(value=False)
        for text, var in [("LinkedIn", self._sw_li), ("Instagram", self._sw_ig),
                           ("Facebook", self._sw_fb), ("TikTok", self._sw_tt)]:
            ctk.CTkCheckBox(ctrl, text=text, variable=var, width=90).pack(side="left", padx=4)

        ctk.CTkFrame(ctrl, width=1, fg_color="gray30").pack(side="left", padx=10, fill="y")

        # Length
        ctk.CTkLabel(ctrl, text="Länge:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))
        self._seg_len = ctk.CTkSegmentedButton(ctrl, values=["Kurz", "Mittel", "Lang"], width=180)
        self._seg_len.set("Mittel")
        self._seg_len.pack(side="left", padx=(0, 10))

        # Tone
        ctk.CTkLabel(ctrl, text="Ton:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))
        self._seg_tone = ctk.CTkSegmentedButton(
            ctrl, values=["Direkt", "Sachlich", "Storytelling"], width=240
        )
        self._seg_tone.set("Direkt")
        self._seg_tone.pack(side="left", padx=(0, 10))

        # Hashtags als Chip
        ctk.CTkLabel(ctrl, text="Hashtags:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))
        self._seg_ht = ctk.CTkSegmentedButton(ctrl, values=["5", "8", "10", "12", "15"], width=200)
        self._seg_ht.set("10")
        self._seg_ht.pack(side="left", padx=(0, 10))

        # Image
        self._sw_img = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ctrl, text="Bild", variable=self._sw_img).pack(side="left")

        # Preview tabs — direkt anschließend
        self._preview = ctk.CTkTabview(tab, height=360)
        self._preview.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        for p in ["LinkedIn", "Instagram", "Facebook", "TikTok"]:
            self._preview.add(p)
        self._txt = {}
        for p in ["LinkedIn", "Instagram", "Facebook", "TikTok"]:
            t = self._preview.tab(p)
            t.grid_rowconfigure(0, weight=1)
            t.grid_columnconfigure(0, weight=1)
            box = ctk.CTkTextbox(t, font=ctk.CTkFont(size=13), wrap="word")
            box.grid(sticky="nsew", padx=4, pady=4)
            box.insert("end", "Hier erscheint die Vorschau …")
            self._txt[p] = box

        # Bottom
        bot = ctk.CTkFrame(tab, fg_color="transparent")
        bot.grid(row=3, column=0, sticky="ew")
        bot.grid_columnconfigure(0, weight=1)

        self._lbl_status = ctk.CTkLabel(bot, text=self._status_text(),
                                         text_color=GRAY, font=ctk.CTkFont(size=12))
        self._lbl_status.grid(row=0, column=0, sticky="w")
        self._btn_post = ctk.CTkButton(
            bot, text="Jetzt posten", width=160, height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=GREEN, hover_color="#15803d",
            command=self._on_post, state="disabled"
        )
        self._btn_post.grid(row=0, column=1)

    # ── Tab: Einstellungen ─────────────────────────────────────────────────────

    def _build_einstellungen(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        # Business Profil
        _section_label(scroll, "Business-Profil", 0)
        biz_fields = [
            ("Name / Unternehmensname", "business_name", False),
            ("Was du anbietest & Hintergrund", "business_description", True),
            ("Zielgruppe", "business_target", False),
            ("Stimme / Tonalität", "business_tone_hints", False),
        ]
        self._biz_settings = {}
        biz_row = 1
        for label, key, multiline in biz_fields:
            ctk.CTkLabel(scroll, text=label, text_color=GRAY,
                         font=ctk.CTkFont(size=12)).grid(
                row=biz_row, column=0, sticky="w", padx=20, pady=(8, 0)
            )
            if multiline:
                w = ctk.CTkTextbox(scroll, width=460, height=72, font=ctk.CTkFont(size=12))
            else:
                w = ctk.CTkEntry(scroll, width=460, font=ctk.CTkFont(size=12))
            w.grid(row=biz_row + 1, column=0, sticky="w", padx=20)
            self._biz_settings[key] = (w, multiline)
            biz_row += 2

        ctk.CTkLabel(scroll, text="Sprache", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).grid(
            row=biz_row, column=0, sticky="w", padx=20, pady=(8, 0)
        )
        self._seg_lang_settings = ctk.CTkSegmentedButton(
            scroll, values=["Deutsch", "Englisch", "Französisch", "Spanisch", "Italienisch"]
        )
        self._seg_lang_settings.set("Deutsch")
        self._seg_lang_settings.grid(row=biz_row + 1, column=0, sticky="w", padx=20)

        # API Keys
        _section_label(scroll, "API Keys", biz_row + 2)

        self._entries = {}
        fields = [
            ("OpenAI API Key", "openai_api_key", "•"),
            ("imgbb API Key", "imgbb_api_key", "•"),
            ("LinkedIn Access Token", "linkedin_access_token", "•"),
            ("LinkedIn Author URN", "linkedin_author_urn", ""),
            ("Instagram User ID", "instagram_user_id", ""),
            ("Instagram Access Token", "instagram_access_token", "•"),
        ]
        for i, (label, key, show) in enumerate(fields):
            row = biz_row + 3 + i * 2
            ctk.CTkLabel(scroll, text=label, text_color=GRAY,
                         font=ctk.CTkFont(size=12)).grid(
                row=row, column=0, sticky="w", padx=20, pady=(8, 0)
            )
            e = ctk.CTkEntry(scroll, width=460, show=show, font=ctk.CTkFont(size=12))
            e.grid(row=row + 1, column=0, sticky="w", padx=20)
            self._entries[key] = e
        api_end_row = biz_row + 3 + len(fields) * 2

        _section_label(scroll, "LinkedIn neu verbinden", api_end_row)
        li_row = ctk.CTkFrame(scroll, fg_color="transparent")
        li_row.grid(row=api_end_row + 1, column=0, sticky="w", padx=20)
        self._e_li_id = ctk.CTkEntry(li_row, width=180, placeholder_text="Client ID",
                                      font=ctk.CTkFont(size=12))
        self._e_li_id.pack(side="left", padx=(0, 8))
        self._e_li_secret = ctk.CTkEntry(li_row, width=200, placeholder_text="Client Secret",
                                          show="•", font=ctk.CTkFont(size=12))
        self._e_li_secret.pack(side="left", padx=(0, 8))
        self._btn_li_reconnect = ctk.CTkButton(
            li_row, text="Verbinden", width=100,
            command=self._do_linkedin_reconnect
        )
        self._btn_li_reconnect.pack(side="left")
        self._lbl_li_status = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=12))
        self._lbl_li_status.grid(row=api_end_row + 2, column=0, sticky="w", padx=20, pady=(4, 0))

        sched_base = api_end_row + 3
        _section_label(scroll, "Automatisch posten", sched_base)
        sched_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        sched_frame.grid(row=sched_base + 1, column=0, sticky="w", padx=20)

        days_label = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        self._day_vars = {}
        for i, (num, lbl) in enumerate(zip(range(1, 8), days_label)):
            v = ctk.BooleanVar(value=num in [2, 5])
            self._day_vars[num] = v
            ctk.CTkCheckBox(sched_frame, text=lbl, variable=v, width=55).grid(
                row=0, column=i, padx=2
            )

        time_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        time_frame.grid(row=sched_base + 2, column=0, sticky="w", padx=20, pady=(8, 0))
        ctk.CTkLabel(time_frame, text="Uhrzeit:", text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))
        self._e_hour = ctk.CTkEntry(time_frame, width=52, placeholder_text="10",
                                     font=ctk.CTkFont(size=13))
        self._e_hour.pack(side="left")
        ctk.CTkLabel(time_frame, text=":", font=ctk.CTkFont(size=16)).pack(side="left", padx=4)
        self._e_minute = ctk.CTkEntry(time_frame, width=52, placeholder_text="00",
                                       font=ctk.CTkFont(size=13))
        self._e_minute.pack(side="left")

        self._sw_autostart = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(scroll, text="Automatisch posten aktivieren",
                      variable=self._sw_autostart).grid(
            row=sched_base + 3, column=0, sticky="w", padx=20, pady=(12, 0)
        )
        self._lbl_sched_status = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=12))
        self._lbl_sched_status.grid(row=sched_base + 4, column=0, sticky="w", padx=20, pady=(4, 0))

        # Save button
        ctk.CTkButton(scroll, text="Einstellungen speichern", width=220,
                      command=self._save_settings).grid(
            row=sched_base + 5, column=0, sticky="w", padx=20, pady=(20, 8)
        )

    # ── Tab: Verlauf ───────────────────────────────────────────────────────────

    def _build_verlauf(self, tab):
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(tab, text="Aktualisieren", width=140,
                      command=self._load_log).grid(row=0, column=0, sticky="w", pady=(8, 4))
        self._log_box = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=12, family="Courier"), wrap="none")
        self._log_box.grid(row=1, column=0, sticky="nsew")
        self._load_log()

    def _load_log(self):
        log_candidates = [
            Path.home() / "Library" / "Logs" / "WolfgangSocialAgent.log",
            Path(__file__).parent / "logs" / "agent.log",
        ]
        for p in log_candidates:
            if p.exists():
                lines = p.read_text().splitlines()[-80:]
                self._log_box.configure(state="normal")
                self._log_box.delete("1.0", "end")
                self._log_box.insert("end", "\n".join(lines))
                self._log_box.configure(state="disabled")
                return
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.insert("end", "Noch keine Einträge.")
        self._log_box.configure(state="disabled")

    # ── Settings load/save ─────────────────────────────────────────────────────

    def _load_settings_into_ui(self):
        c = cfg.load()
        for key, (widget, multiline) in self._biz_settings.items():
            v = c.get(key, "")
            if multiline:
                widget.delete("1.0", "end")
                if v:
                    widget.insert("end", v)
            else:
                widget.delete(0, "end")
                if v:
                    widget.insert(0, v)
        self._seg_lang_settings.set(c.get("business_language", "Deutsch"))

        for key, entry in self._entries.items():
            v = c.get(key, "")
            entry.delete(0, "end")
            if v:
                entry.insert(0, str(v))
        h = c.get("schedule_hour", 10)
        m = c.get("schedule_minute", 0)
        self._e_hour.delete(0, "end")
        self._e_hour.insert(0, str(h))
        self._e_minute.delete(0, "end")
        self._e_minute.insert(0, f"{m:02d}")
        days = c.get("schedule_days", [2, 5])
        for num, var in self._day_vars.items():
            var.set(num in days)

        from src import autostart
        self._sw_autostart.set(autostart.is_enabled())
        self._sw_li.set(c.get("post_linkedin", True))
        self._sw_ig.set(c.get("post_instagram", False))
        self._seg_len.set(c.get("post_length", "Mittel"))
        self._seg_tone.set(c.get("post_tone", "Direkt"))
        self._seg_ht.set(str(c.get("hashtag_count", 10)))
        self._sw_img.set(c.get("generate_image", False))
        self._lbl_status.configure(text=self._status_text())

    def _save_settings(self):
        c = cfg.load()
        for key, (widget, multiline) in self._biz_settings.items():
            if multiline:
                c[key] = widget.get("1.0", "end").strip()
            else:
                c[key] = widget.get().strip()
        c["business_language"] = self._seg_lang_settings.get()

        for key, entry in self._entries.items():
            v = entry.get().strip()
            if v:
                c[key] = v
        try:
            c["schedule_hour"] = int(self._e_hour.get() or 10)
            c["schedule_minute"] = int(self._e_minute.get() or 0)
        except ValueError:
            pass
        c["schedule_days"] = [n for n, v in self._day_vars.items() if v.get()]
        c["post_linkedin"] = self._sw_li.get()
        c["post_instagram"] = self._sw_ig.get()
        c["post_length"] = self._seg_len.get()
        c["post_tone"] = self._seg_tone.get()
        c["hashtag_count"] = int(self._seg_ht.get())
        c["generate_image"] = self._sw_img.get()
        cfg.save(c)
        cfg.apply_to_env()

        from src import autostart
        try:
            if self._sw_autostart.get():
                autostart.enable(c["schedule_days"], c["schedule_hour"], c["schedule_minute"])
                self._lbl_sched_status.configure(text="✓ Automatik aktiviert", text_color=GREEN)
            else:
                autostart.disable()
                self._lbl_sched_status.configure(text="Automatik deaktiviert.", text_color=GRAY)
        except Exception as e:
            self._lbl_sched_status.configure(text=f"Fehler: {e}", text_color=RED)

    # ── LinkedIn reconnect ─────────────────────────────────────────────────────

    def _do_linkedin_reconnect(self):
        cid = self._e_li_id.get().strip()
        secret = self._e_li_secret.get().strip()
        if not cid or not secret:
            self._lbl_li_status.configure(text="Client ID und Secret eingeben.", text_color=RED)
            return
        self._btn_li_reconnect.configure(state="disabled", text="Warte …")
        threading.Thread(target=self._linkedin_reconnect_worker,
                         args=(cid, secret), daemon=True).start()

    def _linkedin_reconnect_worker(self, cid, secret):
        import requests as req
        redirect = "http://localhost:8765/callback"
        scopes = "openid profile w_member_social"
        auth_url = (
            f"https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code&client_id={cid}"
            f"&redirect_uri={urllib.parse.quote(redirect)}"
            f"&scope={urllib.parse.quote(scopes)}&state=wsa"
        )
        code_holder = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if "code" in params:
                    code_holder.append(params["code"][0])
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h2>Fertig!</h2>")
            def log_message(self, *a): pass

        server = http.server.HTTPServer(("localhost", 8765), Handler)
        webbrowser.open(auth_url)
        server.handle_request()
        try:
            tr = req.post("https://www.linkedin.com/oauth/v2/accessToken", data={
                "grant_type": "authorization_code", "code": code_holder[0],
                "redirect_uri": redirect, "client_id": cid, "client_secret": secret,
            })
            token = tr.json()["access_token"]
            ui = req.get("https://api.linkedin.com/v2/userinfo",
                         headers={"Authorization": f"Bearer {token}"})
            urn = f"urn:li:person:{ui.json()['sub']}"
            c = cfg.load()
            c["linkedin_access_token"] = token
            c["linkedin_author_urn"] = urn
            cfg.save(c)
            cfg.apply_to_env()
            self._entries["linkedin_access_token"].delete(0, "end")
            self._entries["linkedin_access_token"].insert(0, token)
            self._entries["linkedin_author_urn"].delete(0, "end")
            self._entries["linkedin_author_urn"].insert(0, urn)
            self.after(0, self._lbl_li_status.configure,
                       {"text": f"✓ Verbunden: {urn}", "text_color": GREEN})
        except Exception as e:
            self.after(0, self._lbl_li_status.configure,
                       {"text": f"Fehler: {e}", "text_color": RED})
        finally:
            self.after(0, self._btn_li_reconnect.configure,
                       {"state": "normal", "text": "Verbinden"})

    # ── Generate & Post ────────────────────────────────────────────────────────

    def _status_text(self) -> str:
        c = cfg.load()
        connected = 0
        if c.get("linkedin_access_token"):
            connected += 1
        if str(c.get("instagram_access_token", "")).startswith("EAA"):
            connected += 1
        total = 2  # nur implementierte Plattformen zählen

        last = self._last_post_time()
        last_str = f" · Letzter Post: {last}" if last else ""
        return f"{connected} von {total} Plattformen verbunden{last_str}"

    def _last_post_time(self) -> str:
        log_candidates = [
            Path.home() / "Library" / "Logs" / "WolfgangSocialAgent.log",
            Path(__file__).parent / "logs" / "agent.log",
        ]
        for p in log_candidates:
            if p.exists():
                for line in reversed(p.read_text().splitlines()):
                    if "Fertig" in line:
                        parts = line.split(" ")
                        if len(parts) >= 2:
                            return f"{parts[0]} {parts[1][:5]}"
        return ""

    def _set_status(self, msg, color=GRAY):
        self._lbl_status.configure(text=msg, text_color=color)

    def _on_generate(self):
        self._btn_gen.configure(state="disabled", text="Generiere …")
        self._btn_post.configure(state="disabled")
        self._set_status("Wird generiert …")
        threading.Thread(target=self._generate_worker, daemon=True).start()

    def _generate_worker(self):
        try:
            from src.content_generator import generate_content
            topic = self._e_topic.get().strip() or None
            ig, li = generate_content(
                custom_topic=topic,
                length=self._seg_len.get(),
                tone=self._seg_tone.get(),
                hashtag_count=int(self._seg_ht.get()),
            )
            self._ig_content = ig
            self._li_content = li
            self.after(0, self._on_generate_done, ig, li)
        except Exception as e:
            self.after(0, self._set_status, f"Fehler: {e}", RED)
            self.after(0, self._btn_gen.configure, {"state": "normal", "text": "Vorschau generieren"})

    def _on_generate_done(self, ig, li):
        texts = {
            "LinkedIn": li["text"],
            "Instagram": ig["caption"],
            "Facebook": li["text"],
            "TikTok": ig["caption"],
        }
        for platform, text in texts.items():
            box = self._txt[platform]
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("end", text)
        self._btn_gen.configure(state="normal", text="Neu generieren")
        self._btn_post.configure(state="normal")
        self._set_status(f"Vorschau bereit · {ig['topic']}", GREEN)

    def _on_post(self):
        self._btn_post.configure(state="disabled", text="Postet …")
        self._set_status("Wird gepostet …")
        threading.Thread(target=self._post_worker, daemon=True).start()

    def _post_worker(self):
        errors = []
        image_path = None
        try:
            if self._sw_img.get():
                from src.image_generator import generate_image
                image_path = generate_image(self._ig_content["topic"])

            if self._sw_li.get():
                from src.linkedin_poster import post_to_linkedin
                post_to_linkedin(self._txt["LinkedIn"].get("1.0", "end").strip(), image_path)

            if self._sw_ig.get():
                token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
                if token.startswith("EAA"):
                    from src.instagram_poster import post_to_instagram
                    post_to_instagram(self._txt["Instagram"].get("1.0", "end").strip(), image_path)
                else:
                    errors.append("Instagram: Token fehlt")

            if self._sw_fb.get():
                errors.append("Facebook: noch nicht eingerichtet (kommt bald)")

            if self._sw_tt.get():
                errors.append("TikTok: noch nicht eingerichtet (kommt bald)")

        except Exception as e:
            errors.append(str(e))
        finally:
            if image_path and os.path.exists(image_path):
                os.unlink(image_path)

        if errors:
            self.after(0, self._set_status, "Fehler: " + " | ".join(errors), RED)
        else:
            self.after(0, self._set_status, "Erfolgreich gepostet!", GREEN)
        self.after(0, self._btn_post.configure, {"state": "normal", "text": "Jetzt posten"})


if __name__ == "__main__":
    app = SocialAgentApp()
    app.mainloop()
