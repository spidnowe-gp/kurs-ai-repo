"""
Moduł 5 – bezpieczne przekazywanie parametrów do zapytań (ćwiczenie 5.8).

Uruchomienie (w folderze projektu):
    python m05_baza/wyszukaj_klienta.py anna.malinowska@poczta.example
    python m05_baza/wyszukaj_klienta.py "x' OR '1'='1"

Ta sama wyszukiwarka w dwóch wersjach:
  niebezpieczna – wartość wklejona w tekst zapytania (f-string),
  bezpieczna    – wartość przekazana jako parametr (znak ?).
"""
import sqlite3
import sys
from pathlib import Path

BAZA = Path(__file__).resolve().parent / "zgloszenia.db"


def wyszukaj_niebezpiecznie(polaczenie, email: str) -> list:
    zapytanie = f"SELECT id, email, imie_nazwisko FROM klienci WHERE email = '{email}'"
    print(f"  Wysłane zapytanie: {zapytanie}")
    return polaczenie.execute(zapytanie).fetchall()


def wyszukaj_bezpiecznie(polaczenie, email: str) -> list:
    zapytanie = "SELECT id, email, imie_nazwisko FROM klienci WHERE email = ?"
    print(f"  Wysłane zapytanie: {zapytanie}   parametry: ({email!r},)")
    return polaczenie.execute(zapytanie, (email,)).fetchall()


def main() -> int:
    if len(sys.argv) < 2:
        print("Podaj adres e-mail, np.: python m05_baza/wyszukaj_klienta.py anna.malinowska@poczta.example")
        return 1
    if not BAZA.exists():
        print("Brak bazy – najpierw uruchom: python m05_baza/utworz_baze.py")
        return 1
    email = sys.argv[1]
    with sqlite3.connect(BAZA) as polaczenie:
        for nazwa, funkcja in (("NIEBEZPIECZNIE", wyszukaj_niebezpiecznie),
                               ("BEZPIECZNIE", wyszukaj_bezpiecznie)):
            print(f"\n{nazwa}")
            wyniki = funkcja(polaczenie, email)
            print(f"  Znaleziono wierszy: {len(wyniki)}")
            for w in wyniki[:5]:
                print(f"   {w}")
            if len(wyniki) > 5:
                print(f"   … i {len(wyniki) - 5} kolejnych")
    return 0


if __name__ == "__main__":
    sys.exit(main())
