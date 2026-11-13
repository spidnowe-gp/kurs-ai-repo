"""
Lokalna usługa odbierająca formularz – Moduł 3 i 7.

Uruchomienie (w folderze projektu):
    python m03_formularz/serwer_formularza.py
Następnie w przeglądarce:  http://localhost:8000
Zatrzymanie: Ctrl+C w terminalu.

Adres webhooka n8n wpisz w stałej ADRES_WEBHOOKA poniżej, a klucz webhooka (nagłówek api-key)
w pliku .env jako KLUCZ_WEBHOOKA. Uruchom serwer ponownie.
Wtedy http://localhost:8000 otwiera zapytanie.html, a formularz wysyła dane do tego serwera,
który dokłada klucz i przekazuje je do webhooka – klucz nie trafia do przeglądarki.
Pusta stała: strona główna to index.html, a zapytanie.html używa adresu z wyslij_zapytanie.js.

Co robi:
  GET  /...            – udostępnia pliki z folderu m03_formularz (index.html, style.css…)
  POST /zgloszenie     – przyjmuje dane formularza (application/x-www-form-urlencoded
                         albo JSON), sprawdza je PO STRONIE USŁUGI i odpowiada:
                         201 – przyjęto, 422 – błędy w danych, 400 – nieczytelne dane
  POST /zapytanie-n8n  – przekazuje JSON z formularza do ADRES_WEBHOOKA z nagłówkiem api-key
                         i zwraca przeglądarce kod oraz treść odpowiedzi n8n
Przyjęte zgłoszenia trafiają do wyniki/zgloszenia_z_formularza.jsonl.
W terminalu widać dziennik zdarzeń – adres e-mail jest częściowo ukryty.
"""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from dotenv import load_dotenv

KATALOG = Path(__file__).resolve().parent
KATALOG_PROJEKTU = Path(__file__).resolve().parents[1] / "asystent-zgloszen"  # dane, .env, wyniki i logi są w folderze asystent-zgloszen
PLIK_WYNIKOW = KATALOG_PROJEKTU / "wyniki" / "zgloszenia_z_formularza.jsonl"
PORT = 8000
# Adres z węzła Webhook w n8n: Production URL albo w teście Test URL (webhook-test)
ADRES_WEBHOOKA = "https://n8n-kurs.tailf6aa90.ts.net/webhook/zamowienie-www-gp"
# Lokalny adres, pod który strona wysyła formularz; serwer przekazuje go dalej do ADRES_WEBHOOKA
SCIEZKA_PRZEKAZANIA = "/zapytanie-n8n"
LIMIT_CZASU_N8N_S = 120  # przepływ czeka na odpowiedź AI Agenta

load_dotenv(KATALOG_PROJEKTU / ".env")
N8N_API_KEY = os.getenv("KLUCZ_WEBHOOKA", "").strip()

WYMAGANE =["imie_nazwisko", "email", "temat", "tresc", "zgoda"]
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
        self.send_header("Cache-Control", "no-store")  # po zmianie adresu lub pliku przeglądarka pobierze nową wersję
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        sciezka = self.path.partition("?")[0]
        if ADRES_WEBHOOKA and sciezka == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/zapytanie.html")
            self.end_headers()
        elif ADRES_WEBHOOKA and sciezka == "/wyslij_zapytanie.js":
            self.wyslij_skrypt_z_adresem()
        else:
            super().do_GET()

    def wyslij_skrypt_z_adresem(self) -> None:
        """Podstawia w wyslij_zapytanie.js lokalny adres przekazania – do n8n wysyła dane ten serwer."""
        wiersz = f"const ADRES_WEBHOOKA = {json.dumps(SCIEZKA_PRZEKAZANIA)};"
        skrypt = (KATALOG / "wyslij_zapytanie.js").read_text(encoding="utf-8")
        skrypt, zamiany = re.subn(r"^const ADRES_WEBHOOKA = .*$", lambda _: wiersz, skrypt,
                                  count=1, flags=re.MULTILINE)
        if not zamiany:
            print("           Uwaga: w wyslij_zapytanie.js nie ma wiersza „const ADRES_WEBHOOKA = …” – "
                  "nie podstawiono adresu.")
        cialo = skrypt.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Content-Length", str(len(cialo)))
        self.end_headers()
        self.wfile.write(cialo)

    def przekaz_do_n8n(self) -> None:
        """Przekazuje JSON z formularza do webhooka n8n z nagłówkiem api-key i oddaje przeglądarce jego odpowiedź."""
        if not ADRES_WEBHOOKA or not N8N_API_KEY:
            print("           Brak ADRES_WEBHOOKA albo KLUCZ_WEBHOOKA w .env – nie przekazano do n8n.")
            self.odpowiedz(HTTPStatus.INTERNAL_SERVER_ERROR,
                           {"status": "blad", "bledy": ["Serwer formularza nie ma skonfigurowanego połączenia z n8n."]})
            return
        dlugosc = int(self.headers.get("Content-Length", 0))
        surowe = self.rfile.read(dlugosc)
        zadanie = urllib.request.Request(
            ADRES_WEBHOOKA, data=surowe, method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json", "api-key": N8N_API_KEY},
        )
        try:
            with urllib.request.urlopen(zadanie, timeout=LIMIT_CZASU_N8N_S) as odp:
                kod, cialo, typ = odp.status, odp.read(), odp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as blad:  # 4xx/5xx z n8n przekazujemy dalej bez zmian
            kod, cialo, typ = blad.code, blad.read(), blad.headers.get("Content-Type", "application/json")
        except (urllib.error.URLError, TimeoutError) as blad:
            print(f"           Brak połączenia z n8n: {blad}")
            self.odpowiedz(HTTPStatus.BAD_GATEWAY, {"status": "blad", "bledy": ["Brak połączenia z serwerem n8n."]})
            return
        print(f"           n8n odpowiedział kodem {kod}")
        self.send_response(kod)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(cialo)))
        self.end_headers()
        self.wfile.write(cialo)

    def do_POST(self):
        if self.path == SCIEZKA_PRZEKAZANIA:
            self.przekaz_do_n8n()
            return
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
                     f'<body><main class="tresc-strony">{html}<p><a href="/index.html">Wróć do formularza</a></p>'
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
    if ADRES_WEBHOOKA:
        print(f"Formularz: http://localhost:{PORT}/zapytanie.html → {ADRES_WEBHOOKA}")
        if not N8N_API_KEY:
            print("Uwaga: brak KLUCZ_WEBHOOKA w .env – n8n odrzuci formularz (kod 403).")
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), Obsluga).serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymano serwer.")
    except OSError as blad:
        print(f"Nie można uruchomić serwera na porcie {PORT}: {blad}")
        print("Czy serwer nie działa już w innym oknie terminala?")
