"""
Moduł 5 – tworzy ćwiczeniową bazę SQLite: m05_baza/zgloszenia.db

Uruchomienie (w folderze projektu):  python m05_baza/utworz_baze.py
Ponowne uruchomienie tworzy bazę od nowa (stara jest nadpisywana).

Tabele:
  klienci    – jeden wiersz na klienta (adres e-mail jest unikalny)
  zgloszenia – zgłoszenia powiązane z klientem przez klient_id
  zdarzenia  – dziennik zmian statusu zgłoszeń

Uwaga do ćwiczenia 5.5: import symuluje ponowne wysłanie części zgłoszeń
(np. ponowienie po przekroczeniu czasu) – w tabeli zgloszenia powstają duplikaty.
"""
import csv
import sqlite3
from pathlib import Path

KATALOG = Path(__file__).resolve().parent
BAZA = KATALOG / "zgloszenia.db"
DANE = KATALOG.parents[1] / "asystent-zgloszen" / "dane" / "zgloszenia.csv"

SCHEMAT = """
CREATE TABLE klienci (
    id            INTEGER PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    imie_nazwisko TEXT,
    telefon       TEXT
);

CREATE TABLE zgloszenia (
    id           INTEGER PRIMARY KEY,
    numer        TEXT NOT NULL,              -- np. ZG-0001; celowo bez UNIQUE (ćwiczenie 5.5)
    klient_id    INTEGER REFERENCES klienci(id),
    data_wplywu  TEXT,
    kanal        TEXT,
    temat        TEXT,
    tresc        TEXT,
    status       TEXT NOT NULL DEFAULT 'nowe',  -- nowe / w_toku / zamkniete
    priorytet    TEXT                          -- wysoki / normalny / niski
);

CREATE TABLE zdarzenia (
    id            INTEGER PRIMARY KEY,
    zgloszenie_id INTEGER REFERENCES zgloszenia(id),
    czas          TEXT NOT NULL,
    typ           TEXT NOT NULL,
    opis          TEXT
);
"""

# Stan obsługi – żeby zapytania z filtrowaniem i sortowaniem miały co pokazać
STATUSY = {"ZG-0001": ("w_toku", "normalny"), "ZG-0002": ("w_toku", "wysoki"),
           "ZG-0005": ("zamkniete", "niski"), "ZG-0006": ("zamkniete", "niski"),
           "ZG-0011": ("w_toku", "wysoki"), "ZG-0018": ("zamkniete", "normalny"),
           "ZG-0025": ("zamkniete", "niski"), "ZG-0026": ("nowe", "wysoki")}
PONOWNIE_WYSLANE = ["ZG-0003", "ZG-0015", "ZG-0020"]


def main() -> None:
    if BAZA.exists():
        BAZA.unlink()
    polaczenie = sqlite3.connect(BAZA)
    polaczenie.executescript(SCHEMAT)

    with open(DANE, encoding="utf-8-sig", newline="") as plik:
        wiersze = list(csv.DictReader(plik, delimiter=";"))

    for w in wiersze:
        email = w["email"].strip().lower()
        if email:
            polaczenie.execute(
                "INSERT INTO klienci (email, imie_nazwisko, telefon) VALUES (?, ?, ?) "
                "ON CONFLICT(email) DO NOTHING",
                (email, w["imie_nazwisko"].strip(), w["telefon"].strip()))

    def dodaj_zgloszenie(w: dict) -> None:
        email = w["email"].strip().lower()
        wiersz = polaczenie.execute("SELECT id FROM klienci WHERE email = ?", (email,)).fetchone()
        status, priorytet = STATUSY.get(w["id"], ("nowe", None))
        kursor = polaczenie.execute(
            "INSERT INTO zgloszenia (numer, klient_id, data_wplywu, kanal, temat, tresc, status, priorytet) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (w["id"], wiersz[0] if wiersz else None, w["data_wplywu"], w["kanal"],
             w["temat"], w["tresc"], status, priorytet))
        polaczenie.execute(
            "INSERT INTO zdarzenia (zgloszenie_id, czas, typ, opis) VALUES (?, ?, 'przyjeto', ?)",
            (kursor.lastrowid, w["data_wplywu"], f"Kanał: {w['kanal']}"))

    for w in wiersze:
        dodaj_zgloszenie(w)
    for w in wiersze:                      # symulacja ponowionego wysłania
        if w["id"] in PONOWNIE_WYSLANE:
            dodaj_zgloszenie(w)

    polaczenie.commit()
    liczby = {t: polaczenie.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("klienci", "zgloszenia", "zdarzenia")}
    polaczenie.close()
    print(f"Utworzono bazę {BAZA}")
    print("Liczba wierszy: " + ", ".join(f"{t}: {n}" for t, n in liczby.items()))
    print("Otwórz ją w DB Browser for SQLite (Plik → Otwórz bazę danych) i przejdź do zakładki „Wykonaj SQL”.")


if __name__ == "__main__":
    main()
