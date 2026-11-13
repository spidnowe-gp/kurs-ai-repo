# Anonimizacja maili przed AI Agent – węzeł Code w n8n (Mode: Run Once for All Items, Language: Python).
# Stałe, wzorce i funkcje skopiowane z anonimizuj.py – zmieniaj je tam i przenoś tutaj.
# Runner n8n musi zezwalać na moduł re: zmienna N8N_RUNNERS_STDLIB_ALLOW=re.
# Każdy mail dostaje własną mapę zamian w polu "mapa_anonimizacji" ({"[OSOBA_1]": "Jan Kowalski", ...}),
# z której korzysta węzeł „Deanonimizuj odpowiedź” po AI Agent.
import re

# Wzorce muszą działać tak samo w Pythonie (re) i w JavaScript (RegExp z flagami "gu"),
# dlatego zamiast \b i \w używamy jawnych klas znaków z polskimi literami.
DUZE = "A-ZĄĆĘŁŃÓŚŹŻ"
MALE = "a-ząćęłńóśźżčěřšžáéíóúýäöü"
LITERA = "0-9A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż"
POCZATEK = f"(?<![{LITERA}])"   # zamiast \b na początku
KONIEC = f"(?![{LITERA}])"      # zamiast \b na końcu
WYRAZ = f"[{DUZE}][{MALE}]+"    # wyraz pisany wielką literą
NAZWISKO = f"{WYRAZ}(?:-{WYRAZ})?"

FIRST_NAMES = ("Anna|Maria|Katarzyna|Małgorzata|Agnieszka|Barbara|Ewa|Krystyna|Elżbieta|Magdalena|Joanna|Aleksandra|Monika|Zofia|Natalia|Karolina|"
               "Marta|Beata|Dorota|Paulina|Iwona|Renata|Halina|Agata|Julia|Wiktoria|Hanna|Lena|Justyna|Sylwia|Izabela|Weronika|Kinga|Emilia|"
               "Jan|Piotr|Krzysztof|Andrzej|Tomasz|Paweł|Marcin|Michał|Marek|Grzegorz|Józef|Łukasz|Adam|Zbigniew|"
               "Jerzy|Tadeusz|Mateusz|Dariusz|Mariusz|Wojciech|Ryszard|Jakub|Kamil|Maciej|Rafał|Robert|Sebastian|Dawid|Szymon|Bartosz|"
               "Konrad|Przemysław|Damian|Daniel|Artur|Kacper|Filip|Patryk|Hubert|Igor|Oskar|Łucja|"
               "Lukas|Martin|Sean|Giulia|Camille|Andrei|Thomas|Peter|Pavel|Lucie|Hanne")
ZWROTY = "Panie|Pani|Panią|Pana|Panu|Panem|Pan"
POZEGNANIA = "Pozdrawiam serdecznie|Serdecznie pozdrawiam|Pozdrawiam|Pozdrowienia|Z poważaniem|Z wyrazami szacunku|Dziękuję|Dzięki"

# (nazwa, wzorzec, rodzaj znacznika). Kolejność ma znaczenie: najpierw e-mail, potem numery, na końcu osoby.
# Jeśli wzorzec ma grupę (...), zamieniana jest tylko ta grupa – reszta dopasowania zostaje (np. słowo "Panie").
PATTERNS = [
    ("E-mail", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "EMAIL"),
    ("Nazwa nadawcy w cudzysłowie", r'"([^"\n]+)"\s*(?=<\[EMAIL_\d+\]>)', "OSOBA"),
    ("Nazwa nadawcy przed adresem", rf"{POCZATEK}{WYRAZ}(?: {NAZWISKO}){{1,2}}(?=\s*<\[EMAIL_\d+\]>)", "OSOBA"),
    ("Numer konta (IBAN PL)", rf"{POCZATEK}PL ?\d{{2}}(?: ?\d{{4}}){{6}}(?!\d)", "KONTO"),
    ("PESEL", r"(?<!\d)\d{11}(?!\d)", "PESEL"),
    ("NIP", r"(?<!\d)\d{3}-?\d{3}-?\d{2}-?\d{2}(?!\d)", "NIP"),
    ("Telefon", r"(?<![\d+])(?:(?:\+|00)48[ -]?)?(?:\(?\d{2}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|\d{3}[ -]?\d{3}[ -]?\d{3})(?!\d)"
                r"|(?<![\d+])\+\d{2,3}[ -]?\d{2,4}(?:[ -]?\d{2,4}){2,3}(?!\d)", "TELEFON"),
    ("Adres (ulica i numer)", rf"{POCZATEK}(?:ul\.|ulica|al\.|aleja|os\.|osiedle|pl\.|plac)\s?[{DUZE}][{LITERA}.\- ]*?\s\d+[A-Za-z]?"
                              rf"(?:\s?/\s?\d+[A-Za-z]?|\s?(?:m\.|lok\.)\s?\d+)?{KONIEC}", "ADRES"),
    ("Kod pocztowy i miasto", rf"{POCZATEK}\d{{2}}-\d{{3}}\s+{WYRAZ}(?:[ -]{WYRAZ})?", "KOD_MIASTO"),
    ("Imię i nazwisko", rf"{POCZATEK}(?:{FIRST_NAMES})\s+{NAZWISKO}", "OSOBA"),
    ("Zwrot grzecznościowy", rf"{POCZATEK}(?:{ZWROTY}) +({WYRAZ}(?: +{NAZWISKO})?)", "OSOBA"),
    ("Podpis pod pożegnaniem", rf"(?:{POZEGNANIA})[,.!]?[ \t]*(?:\r?\n[ \t]*)+({WYRAZ}(?:[ -]{WYRAZ}){{1,2}})(?=[ \t]*(?:\r?\n|$))", "OSOBA"),
]

# Pola maila anonimizowane domyślnie (nazwy jak w workflow n8n). Gdy obiekt nie ma żadnego z nich,
# anonimizowane są wszystkie pola tekstowe.
POLA_MAILA = ["email_from", "email_to", "email_subject", "email_text", "historia"]


def anonimizuj_tekst(tekst, mapa, liczniki):
    for _, wzorzec, rodzaj in PATTERNS:
        def zamien(m):
            ma_grupe = m.re.groups > 0 and m.group(1) is not None
            wartosc = m.group(1) if ma_grupe else m.group(0)
            if wartosc not in mapa:
                liczniki[rodzaj] = liczniki.get(rodzaj, 0) + 1
                mapa[wartosc] = f"[{rodzaj}_{liczniki[rodzaj]}]"
            if not ma_grupe:
                return mapa[wartosc]
            calosc, poczatek = m.group(0), m.start(1) - m.start(0)
            return calosc[:poczatek] + mapa[wartosc] + calosc[poczatek + len(wartosc):]
        tekst = re.sub(wzorzec, zamien, tekst)
    return tekst


def anonimizuj_obiekt(obiekt, mapa, liczniki):
    """Anonimizuje pola maila w słowniku (jak element w n8n)."""
    pola = [p for p in POLA_MAILA if p in obiekt] or [k for k, v in obiekt.items() if isinstance(v, str)]
    wynik = dict(obiekt)
    for pole in pola:
        if isinstance(wynik[pole], str):
            wynik[pole] = anonimizuj_tekst(wynik[pole], mapa, liczniki)
    return wynik


wynik = []
for i, item in enumerate(_items):
    mapa, liczniki = {}, {}
    dane = anonimizuj_obiekt(item["json"], mapa, liczniki)
    dane["mapa_anonimizacji"] = {znacznik: wartosc for wartosc, znacznik in mapa.items()}
    wynik.append({"json": dane, "pairedItem": {"item": i}})
return wynik
