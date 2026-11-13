#!/usr/bin/env python3
"""Zapytania SQL do bazy kursu (MySQL w hostingu) przez sterownik PyMySQL – bez n8n.

Dane połączenia: zmienne MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE w pliku .env,
a gdy ich nie ma – ~/.config/kurs-sai/mysql.cnf (albo ścieżka w KURS_SAI_MYSQL_CNF).
Hasło zostaje w tych plikach – skrypt go nie wypisuje.
PyMySQL jest w ~/.config/kurs-sai/venv; skrypt sam się tam przełącza.
(Klient `mysql` 9.x nie obsługuje logowania mysql_native_password, którego używa hosting.)

  python3 sql.py "SHOW TABLES"                     odczyt
  python3 sql.py -f zmiany.sql --zapis             zapis (INSERT, UPDATE, CREATE TABLE, ALTER TABLE)
  python3 sql.py --tsv "SELECT * FROM produkty"    wynik rozdzielany tabulatorami

Zablokowane zawsze: DROP, TRUNCATE, DELETE, GRANT, REVOKE, RENAME, LOAD DATA,
INTO OUTFILE/DUMPFILE, CREATE USER/DATABASE, ALTER USER, SET PASSWORD, KILL, SHUTDOWN,
a także UPDATE bez WHERE. Takie operacje wykonuje się ręcznie w phpMyAdmin.
"""
import argparse
import configparser
import os
import re
import stat
import sys
from pathlib import Path

PLIK_POLACZENIA = Path(os.environ.get("KURS_SAI_MYSQL_CNF", "~/.config/kurs-sai/mysql.cnf")).expanduser()
VENV = Path("~/.config/kurs-sai/venv").expanduser()

try:
    import pymysql
    from pymysql.constants import CLIENT
except ImportError:
    if (VENV / "bin/python").exists() and Path(sys.prefix) != VENV:
        os.execv(str(VENV / "bin/python"), [str(VENV / "bin/python"), *sys.argv])
    sys.exit(f"Brak PyMySQL – zainstaluj: python3 -m venv {VENV} && {VENV}/bin/pip install PyMySQL")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / "asystent-zgloszen" / ".env")
except ImportError:
    pass  # bez python-dotenv dane połączenia pochodzą z pliku mysql.cnf

ODCZYT = re.compile(r"^(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN|WITH)\b", re.I)
ZAPIS = re.compile(r"^(INSERT|UPDATE|CREATE\s+TABLE|ALTER\s+TABLE)\b", re.I)
ZABRONIONE = re.compile(
    r"\b(DROP|TRUNCATE|DELETE|GRANT|REVOKE|RENAME|SHUTDOWN|KILL|LOAD\s+DATA|INTO\s+(OUTFILE|DUMPFILE)"
    r"|CREATE\s+(USER|DATABASE|SCHEMA)|ALTER\s+USER|SET\s+PASSWORD)\b",
    re.I,
)


def bez_tekstow(sql):
    """Usuwa komentarze i literały tekstowe, żeby słowa w danych (np. 'Delete') nie blokowały zapytania."""
    sql = re.sub(r"--[^\n]*|#[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"'(?:[^'\\]|\\.|'')*'", "''", sql)
    return re.sub(r'"(?:[^"\\]|\\.)*"', '""', sql)


def sprawdz(sql, zapis):
    polecenia = [p.strip() for p in bez_tekstow(sql).split(";") if p.strip()]
    if not polecenia:
        sys.exit("Brak polecenia SQL.")
    for p in polecenia:
        poczatek = p[:70].replace("\n", " ")
        if ZABRONIONE.search(p):
            sys.exit(f"Zablokowane (operacja usuwająca lub administracyjna): {poczatek}")
        if ZAPIS.match(p):
            if not zapis:
                sys.exit(f"To polecenie zmienia bazę – uruchom z --zapis: {poczatek}")
            if re.match(r"UPDATE\b", p, re.I) and not re.search(r"\bWHERE\b", p, re.I):
                sys.exit(f"UPDATE bez WHERE jest zablokowany: {poczatek}")
        elif not ODCZYT.match(p):
            sys.exit(f"Niedozwolone polecenie: {poczatek}")


def sprawdz_plik_polaczenia():
    if not PLIK_POLACZENIA.exists():
        sys.exit(f"Brak pliku połączenia: {PLIK_POLACZENIA}")
    # Windows nie obsługuje chmod: każdy plik zgłasza tam uprawnienia 666
    if os.name != "nt" and PLIK_POLACZENIA.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        sys.exit(f"Plik {PLIK_POLACZENIA} jest dostępny dla innych kont – ustaw: chmod 600")
    cfg = configparser.ConfigParser(allow_no_value=True, comment_prefixes=("#", ";"))
    cfg.read(PLIK_POLACZENIA, encoding="utf-8")
    brak = [k for k in ("host", "user", "password") if not cfg.get("client", k, fallback="").strip()]
    if brak:
        sys.exit(f"W {PLIK_POLACZENIA} uzupełnij: {', '.join(brak)}")
    return cfg.get("mysql", "database", fallback="").strip().strip("'\"") or None


def dane_polaczenia():
    """Parametry połączenia ze zmiennych MYSQL_* (.env), a gdy ich nie ma – z pliku mysql.cnf."""
    zmienne = {k: os.environ.get(f"MYSQL_{k.upper()}", "").strip() for k in ("host", "user", "password", "database")}
    if zmienne["host"]:
        brak = [f"MYSQL_{k.upper()}" for k, v in zmienne.items() if not v]
        if brak:
            sys.exit(f"W pliku .env uzupełnij: {', '.join(brak)}")
        return {**zmienne, "port": int(os.environ.get("MYSQL_PORT") or 3306)}
    baza = sprawdz_plik_polaczenia()
    return {"read_default_file": str(PLIK_POLACZENIA), "read_default_group": "client", "database": baza}


def wypisz(kursor, tsv):
    if kursor.description is None:
        print(f"OK – zmienione wiersze: {kursor.rowcount}")
        return
    kolumny = [d[0] for d in kursor.description]
    wiersze = [["NULL" if v is None else str(v) for v in w] for w in kursor.fetchall()]
    if tsv:
        print("\t".join(kolumny))
        for w in wiersze:
            print("\t".join(w))
        return
    szer = [max([len(k)] + [len(w[i]) for w in wiersze]) for i, k in enumerate(kolumny)]
    linia = "+" + "+".join("-" * (s + 2) for s in szer) + "+"
    print(linia)
    print("| " + " | ".join(k.ljust(s) for k, s in zip(kolumny, szer)) + " |")
    print(linia)
    for w in wiersze:
        print("| " + " | ".join(v.ljust(s) for v, s in zip(w, szer)) + " |")
    print(linia + f"\n{len(wiersze)} wierszy")


def main():
    ap = argparse.ArgumentParser(description="SQL do bazy kursu przez klienta mysql")
    ap.add_argument("sql", nargs="?", help="polecenie SQL (albo użyj -f)")
    ap.add_argument("-f", "--plik", help="plik .sql z poleceniami")
    ap.add_argument("--zapis", action="store_true", help="zezwól na INSERT, UPDATE, CREATE TABLE, ALTER TABLE")
    ap.add_argument("--tsv", action="store_true", help="wynik rozdzielany tabulatorami zamiast tabeli")
    a = ap.parse_args()

    sql = Path(a.plik).read_text(encoding="utf-8") if a.plik else a.sql
    if not sql:
        ap.error("podaj polecenie SQL albo -f plik.sql")
    sprawdz(sql, a.zapis)
    dane = dane_polaczenia()

    try:
        polaczenie = pymysql.connect(**dane, charset="utf8mb4", connect_timeout=10,
                                     autocommit=False, client_flag=CLIENT.MULTI_STATEMENTS)
    except pymysql.MySQLError as e:
        sys.exit(f"Brak połączenia z bazą: {e}")
    try:
        with polaczenie.cursor() as kursor:
            kursor.execute(sql)
            while True:
                wypisz(kursor, a.tsv)
                if not kursor.nextset():
                    break
        polaczenie.commit()
    except pymysql.MySQLError as e:
        polaczenie.rollback()
        sys.exit(f"Błąd MySQL (zmiany wycofane): {e}")
    finally:
        polaczenie.close()


if __name__ == "__main__":
    main()
