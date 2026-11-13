"""
Lokalna usługa odbierająca formularz – Moduł 3 i 7.

Uruchomienie (w folderze projektu):
    python m03_formularz/serwer_formularza.py
Następnie w przeglądarce:  http://localhost:8000
Zatrzymanie: Ctrl+C w terminalu.

Co robi:
  GET  /...          – udostępnia pliki z folderu m03_formularz (index.html, style.css…)
  POST /zgloszenie   – przyjmuje dane formularza (application/x-www-form-urlencoded
                       albo JSON), sprawdza je PO STRONIE USŁUGI i odpowiada:
                       201 – przyjęto, 422 – błędy w danych, 400 – nieczytelne dane
Przyjęte zgłoszenia trafiają do wyniki/zgloszenia_z_formularza.jsonl.
W terminalu widać dziennik zdarzeń – adres e-mail jest częściowo ukryty.
"""
import json
import re
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

KATALOG = Path(__file__).resolve().parent
PLIK_WYNIKOW = Path(__file__).resolve().parents[2] / "asystent-zgloszen" / "wyniki" / "zgloszenia_z_formularza.jsonl"
PORT = 8000

WYMAGANE = ["imie_nazwisko", "email", "temat", "tresc", "zgoda"]
TEMATY = ["reklamacja", "zamowienie", "zwrot", "faktura", "pytanie_techniczne", "inne"]
WZOR_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)
WZOR_NUMERU = re.compile(r"^VN-\d{4}-\d{5}$")


def ukryj_email(email: str) -> str:
    """anna.malinowska@poczta.example → a***@poczta.example"""
    nazwa, _, domena = email.partition("@")
    return f"{nazwa[:1]}***@{domena}" if domena else "***"


def sprawdz(dane: dict) -> list[str]:
    bledy = [f"Pole „{pole}” jest wymagane." for pole in WYMAGANE if not dane.get(pole)]
    if dane.get("email") and not WZOR_EMAIL.match(dane["email"]):
        bledy.append("Adres e-mail ma niepoprawny format.")
    if dane.get("temat") and dane["temat"] not in TEMATY:
        bledy.append(f"Nieznana wartość pola temat: „{dane['temat']}”.")
    if dane.get("tresc") and len(dane["tresc"]) < 20:
        bledy.append("Opis sprawy musi mieć co najmniej 20 znaków.")
    if dane.get("numer_zamowienia") and not WZOR_NUMERU.match(dane["numer_zamowienia"]):
        bledy.append("Numer zamówienia powinien mieć format VN-RRRR-NNNNN.")
    return bledy


def kolejny_numer() -> str:
    liczba = 0
    if PLIK_WYNIKOW.exists():
        liczba = sum(1 for _ in PLIK_WYNIKOW.open(encoding="utf-8"))
    return f"ZG-W{liczba + 1:04d}"


class Obsluga(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(KATALOG), **kwargs)

    # Nagłówki CORS – potrzebne w Module 7, gdy strona z innego adresu wysyła dane przez fetch()
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self):
        if self.path != "/zgloszenie":
            self.odpowiedz(HTTPStatus.NOT_FOUND, {"status": "blad", "bledy": [f"Brak adresu {self.path}"]})
            return
        dlugosc = int(self.headers.get("Content-Length", 0))
        surowe = self.rfile.read(dlugosc).decode("utf-8", errors="replace")
        typ = self.headers.get("Content-Type", "")
        try:
            if "application/json" in typ:
                dane = json.loads(surowe)
            else:
                dane = {k: v[0] for k, v in parse_qs(surowe, keep_blank_values=True).items()}
        except json.JSONDecodeError:
            self.odpowiedz(HTTPStatus.BAD_REQUEST, {"status": "blad", "bledy": ["Nieczytelny JSON."]})
            return
        dane = {k: str(v).strip() for k, v in dane.items()}

        print(f"[{datetime.now():%H:%M:%S}] Odebrano pola: {sorted(dane)} "
              f"· e-mail: {ukryj_email(dane.get('email', ''))}")

        bledy = sprawdz(dane)
        if bledy:
            print(f"           Odrzucono: {bledy}")
            self.odpowiedz(HTTPStatus.UNPROCESSABLE_ENTITY, {"status": "blad", "bledy": bledy})
            return

        numer = kolejny_numer()
        PLIK_WYNIKOW.parent.mkdir(exist_ok=True)
        with PLIK_WYNIKOW.open("a", encoding="utf-8") as plik:
            plik.write(json.dumps({"numer": numer, "czas": datetime.now().isoformat(timespec="seconds"),
                                   **dane}, ensure_ascii=False) + "\n")
        print(f"           Przyjęto jako {numer}")
        self.odpowiedz(HTTPStatus.CREATED, {"status": "przyjete", "numer": numer})

    def odpowiedz(self, kod: HTTPStatus, tresc: dict) -> None:
        """JSON dla fetch() (Moduł 7), prosta strona HTML dla zwykłego formularza (Moduł 3)."""
        chce_json = "application/json" in self.headers.get("Accept", "") or \
                    "application/json" in self.headers.get("Content-Type", "")
        if chce_json:
            cialo = json.dumps(tresc, ensure_ascii=False).encode("utf-8")
            typ = "application/json; charset=utf-8"
        else:
            if tresc["status"] == "przyjete":
                html = f'<p class="komunikat sukces">Dziękujemy! Numer zgłoszenia: <b>{tresc["numer"]}</b>.</p>'
            else:
                pozycje = "".join(f"<li>{b}</li>" for b in tresc["bledy"])
                html = f'<div class="komunikat blad"><p>Nie przyjęto zgłoszenia:</p><ul>{pozycje}</ul></div>'
            cialo = (f'<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">'
                     f'<link rel="stylesheet" href="/style.css"><title>Wynik</title></head>'
                     f'<body><main class="tresc-strony">{html}<p><a href="/">Wróć do formularza</a></p>'
                     f'</main></body></html>').encode("utf-8")
            typ = "text/html; charset=utf-8"
        self.send_response(kod)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(cialo)))
        self.end_headers()
        self.wfile.write(cialo)

    def log_message(self, format, *args):  # krótszy dziennik w terminalu
        print(f"[{datetime.now():%H:%M:%S}] {self.command} {self.path} → {args[1] if len(args) > 1 else ''}")


if __name__ == "__main__":
    print(f"Serwer formularza działa: http://localhost:{PORT}  (zatrzymanie: Ctrl+C)")
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), Obsluga).serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymano serwer.")
    except OSError as blad:
        print(f"Nie można uruchomić serwera na porcie {PORT}: {blad}")
        print("Czy serwer nie działa już w innym oknie terminala?")
