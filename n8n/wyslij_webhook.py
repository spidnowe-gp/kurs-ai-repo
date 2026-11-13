"""
Moduł 6 i 9 – wysyłanie zgłoszeń testowych do webhooka.

Adres webhooka wpisz w pliku .env (w folderze kurs albo w folderze projektu) jako WEBHOOK_URL, np.:
    WEBHOOK_URL=https://webhook.site/<twój-identyfikator>            (Moduł 6 – podgląd żądania)
    WEBHOOK_URL=https://<adres-n8n>/webhook-test/zgloszenie          (Moduł 9 – tryb testowy n8n)
    WEBHOOK_URL=https://<adres-n8n>/webhook/zgloszenie               (Moduł 9 – przepływ aktywny)

Uruchomienie (w folderze projektu):
    python m06_api/wyslij_webhook.py               – jedno poprawne zgłoszenie
    python m06_api/wyslij_webhook.py --testy       – zestaw przypadków z m09_n8n/dane_testowe.json
    python m06_api/wyslij_webhook.py --testy 3     – tylko przypadek nr 3
"""
import json
import os
import sys
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

KATALOG_PROJEKTU = Path(__file__).resolve().parents[1] / "asystent-zgloszen"
load_dotenv(KATALOG_PROJEKTU / ".env")         # .env w folderze projektu
load_dotenv(KATALOG_PROJEKTU.parent / ".env")  # albo w folderze nadrzędnym (kurs)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()

PRZYKLAD = {
    "imie_nazwisko": "Anna Malinowska",
    "email": "anna.malinowska@poczta.example",
    "telefon": "",
    "numer_zamowienia": "VN-2026-10388",
    "temat": "reklamacja",
    "tresc": "Podczas ładowania bateria w rowerze Urban E28 bardzo się nagrzała. Boję się dalej używać roweru.",
    "zgoda": "tak",
}


def wyslij(dane: dict, opis: str) -> None:
    dane = {**dane}
    dane.setdefault("id_wysylki", str(uuid.uuid4()))   # klucz idempotencji nadawany po stronie formularza
    print(f"\n→ {opis}")
    try:
        odp = requests.post(WEBHOOK_URL, json=dane, timeout=(5, 60))
    except requests.exceptions.Timeout:
        print("  Brak odpowiedzi w 60 s (czy przepływ nie czeka na zatwierdzenie?)")
        return
    except requests.exceptions.ConnectionError:
        print("  Brak połączenia – sprawdź WEBHOOK_URL i czy usługa działa")
        return
    print(f"  HTTP {odp.status_code}")
    print("  " + odp.text[:400].replace("\n", "\n  "))


def main(argumenty: list[str]) -> int:
    if not WEBHOOK_URL.startswith("http"):
        print("Uzupełnij WEBHOOK_URL w pliku .env (np. adres z webhook.site albo z węzła Webhook w n8n).")
        return 1
    if len(argumenty) > 1 and argumenty[1] == "--testy":
        przypadki = json.loads((Path(__file__).resolve().parent / "m09_n8n" / "dane_testowe.json").read_text(encoding="utf-8"))
        wybrane = przypadki
        if len(argumenty) > 2:
            wybrane = [p for p in przypadki if str(p["nr"]) == argumenty[2]]
        for p in wybrane:
            wyslij(p["dane"], f"Przypadek {p['nr']}: {p['opis']} (oczekiwane: {p['oczekiwane']})")
    else:
        wyslij(PRZYKLAD, "Poprawne zgłoszenie przykładowe")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
