# Walidacja zgłoszenia z formularza WWW (body JSON) – węzeł Code w n8n (Mode: Run Once for All Items, Language: Python).
# Dwa typy: zamówienie (pole "produkt") i zapytanie z zapytanie.html (rodzaj, budżet, opis).
# Błędne dane nie trafiają do AI Agenta. Runner n8n musi zezwalać na moduł re: zmienna N8N_RUNNERS_STDLIB_ALLOW=re.
# Identyfikator wykonania i bieżący czas dostarcza węzeł „Dane żądania” (Python w n8n nie ma $execution ani $now).
import re

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
KOD_POCZTOWY = re.compile(r"^\d{2}-\d{3}$")
PREFIKS_ULICY = re.compile(r"^(ul\.|ulica|al\.|aleja|os\.|osiedle|pl\.|plac)\s", re.IGNORECASE)
# Wartości pola "rodzaj" z zapytanie.html i ich opisy dla AI Agenta
RODZAJE = {
    "hulajnoga_miejska": "Hulajnoga do miasta",
    "hulajnoga_terenowa": "Hulajnoga terenowa",
    "hulajnoga_dziecieca": "Hulajnoga dla dziecka",
    "rower_elektryczny": "Rower elektryczny",
    "czesci_akcesoria": "Części i akcesoria",
}
HISTORIA_WWW = "Brak wcześniejszej korespondencji – nowe zgłoszenie ze strony WWW."


def tekst(wartosc):
    return wartosc.strip() if isinstance(wartosc, str) else ""


def liczba_calkowita(wartosc):
    """Zwraca liczbę całkowitą z int, float bez części ułamkowej albo tekstu z cyframi; w pozostałych przypadkach None."""
    if isinstance(wartosc, bool):
        return None
    if isinstance(wartosc, int):
        return wartosc
    if isinstance(wartosc, float) and wartosc.is_integer():
        return int(wartosc)
    if isinstance(wartosc, str) and wartosc.strip().isdigit():
        return int(wartosc.strip())
    return None


def zgoda_udzielona(wartosc):
    return wartosc is True or (isinstance(wartosc, str) and wartosc.strip().lower() in ("tak", "true", "on", "1"))


def wspolne_pola(dane, imie, email, temat, tresc, typ):
    identyfikator = f"www-{dane.get('execution_id')}"
    return {
        "poprawne": True,
        "bledy": [],
        "zrodlo": "www",
        "typ_zgloszenia": typ,
        "zamowienie_id": identyfikator,
        "thread_id": identyfikator,
        "message_id": identyfikator,
        "nadawca": f"{imie} <{email}>",
        "nadawca_adres": email,
        "email_from": email,
        "email_subject": temat,
        "email_text": tresc,
        "nowa_tresc": tresc,
        "email_date": dane.get("teraz"),
        "historia": HISTORIA_WWW,
    }


def waliduj_zamowienie(dane, body, imie, email):
    telefon = tekst(body.get("telefon"))
    produkt = tekst(body.get("produkt"))
    ilosc = liczba_calkowita(body.get("ilosc"))
    adres = body.get("adres") if isinstance(body.get("adres"), dict) else {}
    ulica = tekst(adres.get("ulica"))
    kod = tekst(adres.get("kod_pocztowy"))
    miasto = tekst(adres.get("miasto"))
    dostawa = tekst(body.get("sposob_dostawy"))
    uwagi = tekst(body.get("uwagi"))

    bledy = []
    if telefon and len(re.sub(r"\D", "", telefon)) < 9:
        bledy.append('Pole "telefon" musi mieć co najmniej 9 cyfr.')
    if not produkt:
        bledy.append('Pole "produkt" (nazwa lub SKU) jest wymagane.')
    if ilosc is None or not 1 <= ilosc <= 100:
        bledy.append('Pole "ilosc" musi być liczbą całkowitą od 1 do 100.')
    if not ulica:
        bledy.append('Pole "adres.ulica" jest wymagane.')
    if not KOD_POCZTOWY.match(kod):
        bledy.append('Pole "adres.kod_pocztowy" musi mieć format NN-NNN.')
    if not miasto:
        bledy.append('Pole "adres.miasto" jest wymagane.')
    if len(uwagi) > 2000:
        bledy.append('Pole "uwagi" może mieć najwyżej 2000 znaków.')
    if bledy:
        return bledy, None

    # Zapis "Imię" <e-mail> i prefiks "ul." pozwalają węzłowi anonimizacji rozpoznać dane osobowe.
    ulica_z_prefiksem = ulica if PREFIKS_ULICY.match(ulica) else f"ul. {ulica}"
    linie = [
        "Zamówienie złożone przez formularz na stronie WWW.",
        f'Zamawiający: "{imie}" <{email}>',
        f"Produkt: {produkt}",
        f"Ilość: {ilosc}",
        f"Sposób dostawy: {dostawa or 'nie wybrano'}",
        f"Adres dostawy: {ulica_z_prefiksem}, {kod} {miasto}",
    ]
    if telefon:
        linie.append(f"Telefon: {telefon}")
    if uwagi:
        linie.append(f"Uwagi klienta: {uwagi}")
    return [], wspolne_pola(dane, imie, email, "Zamówienie ze strony WWW", "\n".join(linie), "zamowienie")


def waliduj_zapytanie(dane, body, imie, email):
    rodzaj = tekst(body.get("rodzaj"))
    budzet_tekst = tekst(body.get("budzet")) if not isinstance(body.get("budzet"), (int, float)) else str(body.get("budzet"))
    budzet = liczba_calkowita(body.get("budzet")) if budzet_tekst else None
    opis = tekst(body.get("tresc"))

    bledy = []
    if rodzaj not in RODZAJE:
        bledy.append('Pole "rodzaj" musi mieć jedną z wartości: ' + ", ".join(RODZAJE) + ".")
    if budzet_tekst and (budzet is None or budzet < 0):
        bledy.append('Pole "budzet" musi być liczbą całkowitą nie mniejszą niż 0.')
    if not 20 <= len(opis) <= 2000:
        bledy.append('Pole "tresc" musi mieć od 20 do 2000 znaków.')
    if not zgoda_udzielona(body.get("zgoda")):
        bledy.append("Wymagana jest zgoda na przetwarzanie danych.")
    if bledy:
        return bledy, None

    linie = [
        "Zapytanie złożone przez formularz na stronie WWW.",
        f'Klient: "{imie}" <{email}>',
        f"Czego szuka: {RODZAJE[rodzaj]}",
        f"Budżet: {budzet} zł brutto" if budzet is not None else "Budżet: nie podano",
        "Opis klienta:",
        opis,
    ]
    return [], wspolne_pola(dane, imie, email, "Zapytanie ze strony WWW", "\n".join(linie), "zapytanie")


def waliduj(dane):
    body = dane.get("body")
    if not isinstance(body, dict):
        return {"poprawne": False, "bledy": ["Treść żądania musi być obiektem JSON."]}

    imie = tekst(body.get("imie_nazwisko"))
    email = tekst(body.get("email"))
    bledy = []
    if len(imie) < 3:
        bledy.append('Pole "imie_nazwisko" jest wymagane.')
    if not EMAIL.match(email):
        bledy.append('Pole "email" musi zawierać poprawny adres e-mail.')

    # Zamówienie rozpoznajemy po polu "produkt"; pozostałe zgłoszenia to zapytania z zapytanie.html
    waliduj_typ = waliduj_zamowienie if "produkt" in body else waliduj_zapytanie
    bledy_typu, wynik = waliduj_typ(dane, body, imie, email)
    bledy += bledy_typu
    if bledy:
        return {"poprawne": False, "bledy": bledy}
    return wynik


return [{"json": waliduj(item["json"]), "pairedItem": {"item": i}} for i, item in enumerate(_items)]
