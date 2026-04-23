from typing import Optional
import os
import openai
import random
from src import config as cfg

client = openai.OpenAI()

GENERIC_TOPICS = [
    "Warum die meisten in meiner Branche einen wichtigen Fehler machen",
    "Was meine Kunden vor der Zusammenarbeit unterschätzen",
    "Der Unterschied zwischen gut und wirklich gut in meinem Bereich",
    "Was ich in den letzten Jahren gelernt habe, das mich überrascht hat",
    "Warum klare Positionierung wichtiger ist als ein großes Portfolio",
    "3 Fragen, die du stellen solltest, bevor du jemanden in meiner Branche beauftragst",
    "Was unternehmerisches Denken mit meiner Arbeit zu tun hat",
    "Warum Qualität und Schnelligkeit kein Widerspruch sein müssen",
]


def _build_persona() -> str:
    c = cfg.load()
    name = os.environ.get("BUSINESS_NAME") or c.get("business_name", "")
    desc = os.environ.get("BUSINESS_DESCRIPTION") or c.get("business_description", "")
    target = os.environ.get("BUSINESS_TARGET") or c.get("business_target", "")
    tone = os.environ.get("BUSINESS_TONE_HINTS") or c.get("business_tone_hints", "")
    lang = os.environ.get("BUSINESS_LANGUAGE") or c.get("business_language", "Deutsch")

    persona = f"Du bist {name}.\n" if name else "Du bist ein Experte in deinem Bereich.\n"
    if desc:
        persona += f"Dein Business: {desc}\n"
    if target:
        persona += f"Deine Zielgruppe: {target}\n"
    if tone:
        persona += f"Deine Stimme: {tone}\n"
    persona += f"Schreibe immer auf {lang}, authentisch und ohne leere Phrasen."
    return persona


LENGTH_WORDS = {
    "Mini":   {"instagram": "20-40",   "linkedin": "50-100"},
    "Kurz":   {"instagram": "80-120",  "linkedin": "150-200"},
    "Mittel": {"instagram": "150-220", "linkedin": "250-350"},
    "Lang":   {"instagram": "250-320", "linkedin": "400-550"},
}

TONE_INSTRUCTIONS = {
    "Direkt":       "Meinungsstark, auf den Punkt, keine Weichspüler-Formulierungen.",
    "Sachlich":     "Informativ, klar strukturiert, faktenbasiert.",
    "Storytelling": "Erzählerisch, persönliche Anekdote oder Erlebnis als Aufhänger.",
    "Humorvoll":    "Leicht, witzig, Augenzwinkern — aber trotzdem mit Substanz. Keine Flachwitze.",
    "Provokativ":   "Steile These aufstellen, bewusst polarisieren, Diskussion anregen. Mutig formulieren.",
}


def generate_content(
    custom_topic: Optional[str] = None,
    length: str = "Mittel",
    tone: str = "Direkt",
    hashtag_count: int = 10,
    custom_chars: Optional[int] = None,
) -> tuple[dict, dict]:
    if custom_topic:
        topic_title = custom_topic
        topic_hook = custom_topic
    else:
        topic_hook = random.choice(GENERIC_TOPICS)
        topic_title = topic_hook

    persona = _build_persona()
    instagram = _generate_instagram_post(topic_title, topic_hook, length, tone, hashtag_count, persona, custom_chars)
    linkedin = _generate_linkedin_post(topic_title, topic_hook, length, tone, persona, custom_chars)
    return instagram, linkedin


def _chars_to_words(chars: int) -> str:
    return f"ca. {max(40, chars // 5)}"


def _generate_instagram_post(
    topic_title: str, topic_hook: str, length: str, tone: str, hashtag_count: int, persona: str,
    custom_chars: Optional[int] = None,
) -> dict:
    words = _chars_to_words(custom_chars) if custom_chars else LENGTH_WORDS[length]["instagram"]
    tone_hint = TONE_INSTRUCTIONS[tone]
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": f"""{persona}

Schreibe einen Instagram-Post zum Thema: "{topic_hook}"

Ton: {tone_hint}
Länge: {words} Wörter
Hashtags: genau {hashtag_count} Hashtags (Mix Deutsch/Englisch)

Regeln:
- Beginne mit einem starken Hook (erste Zeile = Aufmerksamkeit)
- Keine leeren Phrasen
- Am Ende: 1 Frage an die Follower
- Trenne Hashtags vom Text mit einer Leerzeile

Gib NUR den fertigen Post aus, keine Erklärungen."""
        }]
    )
    caption = response.choices[0].message.content.strip()
    return {"caption": caption, "topic": topic_title, "hook": topic_hook}


def _generate_linkedin_post(
    topic_title: str, topic_hook: str, length: str, tone: str, persona: str,
    custom_chars: Optional[int] = None,
) -> dict:
    words = _chars_to_words(custom_chars) if custom_chars else LENGTH_WORDS[length]["linkedin"]
    tone_hint = TONE_INSTRUCTIONS[tone]
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""{persona}

Schreibe einen LinkedIn-Post zum Thema: "{topic_hook}"

Ton: {tone_hint}
Länge: {words} Wörter

Regeln:
- Beginne mit einer These oder überraschenden Aussage
- 2-3 konkrete Punkte oder Beobachtungen
- Schließe mit Handlungsempfehlung oder Diskussionseinladung
- Keine Emojis außer 1-2 am Anfang wenn es passt
- Keine generischen Phrasen wie "In der heutigen Welt..."

Gib NUR den fertigen Post aus, keine Erklärungen."""
        }]
    )
    text = response.choices[0].message.content.strip()
    return {"text": text, "topic": topic_title}
