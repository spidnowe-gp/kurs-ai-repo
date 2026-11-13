# Walidacja wiadomości z czatu na stronie WWW (Chat Trigger) – węzeł Code w n8n (Mode: Run Once for All Items, Language: Python).
# Błędna wiadomość nie trafia do AI Agenta. Runner n8n musi zezwalać na moduł re: zmienna N8N_RUNNERS_STDLIB_ALLOW=re.
# Pola wyjściowe mają te same nazwy co dla maili, żeby dalej działały wspólne węzły (anonimizacja, AI Agent, log).
import re

SESJA = re.compile(r"^[A-Za-z0-9_-]{8,100}$")


def tekst(wartosc):
    return wartosc.strip() if isinstance(wartosc, str) else ""


def waliduj(dane):
    sesja = tekst(dane.get("sessionId"))
    wiadomosc = tekst(dane.get("chatInput"))

    bledy = []
    if dane.get("action", "sendMessage") != "sendMessage":
        bledy.append("Nieobsługiwana akcja czatu.")
    if not SESJA.match(sesja):
        bledy.append("Brak poprawnego identyfikatora rozmowy.")
    if not wiadomosc:
        bledy.append("Wiadomość jest pusta.")
    elif len(wiadomosc) > 2000:
        bledy.append("Wiadomość może mieć najwyżej 2000 znaków.")
    if bledy:
        return {"poprawne": False, "bledy": bledy}

    identyfikator = f"czat-{sesja}"
    return {
        "poprawne": True,
        "bledy": [],
        "zrodlo": "czat",
        "typ_zgloszenia": "czat",
        "session_id": sesja,
        "thread_id": identyfikator,
        "message_id": identyfikator,
        "nadawca": "Klient czatu WWW",
        "nadawca_adres": "",
        "email_subject": "Rozmowa na czacie WWW",
        "email_text": wiadomosc,
        "nowa_tresc": wiadomosc,
        "historia": "Wcześniejsze wiadomości tej rozmowy są w pamięci rozmowy.",
    }


return [{"json": waliduj(item["json"]), "pairedItem": {"item": i}} for i, item in enumerate(_items)]
