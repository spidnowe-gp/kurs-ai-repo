"""
Moduł 5 i 10 – kopia zapasowa, odtworzenie i eksport bazy zgłoszeń.

Uruchomienie (w folderze projektu):
    python m05_baza/kopia_zapasowa.py kopia             – kopia do m05_baza/kopie/
    python m05_baza/kopia_zapasowa.py lista             – lista kopii
    python m05_baza/kopia_zapasowa.py przywroc PLIK.db  – odtworzenie (z potwierdzeniem)
    python m05_baza/kopia_zapasowa.py eksport           – zgłoszenia do wyniki/zgloszenia_eksport.csv

Kopia powstaje przez wbudowany mechanizm SQLite (backup) – jest spójna także wtedy,
gdy baza jest w tym czasie otwarta w innym programie.
"""
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

KATALOG = Path(__file__).resolve().parent
BAZA = KATALOG / "zgloszenia.db"
KOPIE = KATALOG / "kopie"
EKSPORT = KATALOG.parents[1] / "asystent-zgloszen" / "wyniki" / "zgloszenia_eksport.csv"


def kopia() -> None:
    KOPIE.mkdir(exist_ok=True)
    cel = KOPIE / f"zgloszenia_{datetime.now():%Y%m%d_%H%M%S}.db"
    with sqlite3.connect(BAZA) as zrodlo, sqlite3.connect(cel) as kopia_db:
        zrodlo.backup(kopia_db)
    liczba = sqlite3.connect(cel).execute("SELECT COUNT(*) FROM zgloszenia").fetchone()[0]
    print(f"Utworzono kopię: {cel.name} (zgłoszeń w kopii: {liczba})")


def lista() -> None:
    pliki = sorted(KOPIE.glob("*.db")) if KOPIE.exists() else []
    if not pliki:
        print("Brak kopii.")
    for p in pliki:
        print(f"{p.name}  {p.stat().st_size / 1024:.0f} KB")


def przywroc(nazwa: str) -> None:
    zrodlo = KOPIE / nazwa
    if not zrodlo.exists():
        print(f"Nie ma kopii {nazwa}. Sprawdź: python m05_baza/kopia_zapasowa.py lista")
        return
    odp = input(f"Bieżąca baza zostanie zastąpiona kopią {nazwa}. Wpisz TAK, aby kontynuować: ")
    if odp.strip() != "TAK":
        print("Anulowano – baza bez zmian.")
        return
    with sqlite3.connect(zrodlo) as z, sqlite3.connect(BAZA) as cel:
        z.backup(cel)
    print(f"Przywrócono bazę z kopii {nazwa}.")


def eksport() -> None:
    EKSPORT.parent.mkdir(exist_ok=True)
    with sqlite3.connect(BAZA) as polaczenie:
        kursor = polaczenie.execute(
            "SELECT z.numer, z.data_wplywu, z.temat, z.status, z.priorytet, k.email "
            "FROM zgloszenia z LEFT JOIN klienci k ON k.id = z.klient_id ORDER BY z.numer")
        kolumny = [opis[0] for opis in kursor.description]
        with open(EKSPORT, "w", encoding="utf-8-sig", newline="") as plik:
            zapis = csv.writer(plik, delimiter=";")
            zapis.writerow(kolumny)
            zapis.writerows(kursor)
    print(f"Wyeksportowano do {EKSPORT} (otwiera się poprawnie w Excelu)")


if __name__ == "__main__":
    if not BAZA.exists():
        sys.exit("Brak bazy – najpierw uruchom: python m05_baza/utworz_baze.py")
    polecenie = sys.argv[1] if len(sys.argv) > 1 else ""
    if polecenie == "kopia":
        kopia()
    elif polecenie == "lista":
        lista()
    elif polecenie == "przywroc" and len(sys.argv) > 2:
        przywroc(sys.argv[2])
    elif polecenie == "eksport":
        eksport()
    else:
        print(__doc__)
