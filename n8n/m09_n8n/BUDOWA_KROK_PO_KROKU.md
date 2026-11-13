# Moduł 9 – przepływ „Obsługa zgłoszeń” w n8n krok po kroku

Wersja dla n8n 2.x (serwer kursu). Część 1 – sobota 24.10 (kroki 0–9), część 2 – sobota 21.11 (kroki 10–14).
Kod węzłów Code: `kod_wezlow.md`. Instrukcja dla modelu: `instrukcja_dla_modelu.md`. Przypadki testowe: `dane_testowe.json`.
Tabele utworzysz importując i uruchamiając raz `przeplyw_0_utworz_tabele.json`. Atrapa modelu do testów bez kosztów: `atrapa_modelu.py`.

> Ścieżka webhooka musi być unikalna w całym serwerze n8n – każdy uczestnik używa `zgloszenie-<imie>`.

```
Webhook ─► Walidacja ─► Kompletne? ──nie──► Odpowiedź 422
                              │tak
                              ▼
                 Czy już przyjęte? (tabela) ─► Nowe? ──nie──► Odpowiedź 200 (powtórzone)
                                                 │tak
                                                 ▼
          Numer zgłoszenia ─► Zapisz zgłoszenie ─► Odpowiedź 201 ─► Model ─► Kontrola odpowiedzi
                                                                            │
                                         Poprawna? ──nie──► status „blad_klasyfikacji” + dziennik
                                             │tak
                                             ▼
                     Zapisz klasyfikację ─► Zatwierdzenie (Wait – formularz) ─► Zapisz decyzję ─► Dziennik
```

---

## Krok 0. Przygotowanie (prowadzący – przed zajęciami)

- Konto każdego uczestnika na serwerze n8n kursu (rola: Member). Adres serwera – na tablicy.
- Klucz API kursu (osobny klucz z limitem wydatków) – uczestnicy dodają go jako dane uwierzytelniające,
  nie wpisują go w węzłach.
- Każdy uczestnik tworzy w swoim projekcie dwie tabele – ręcznie (**Overview → Data tables → Create**)
  albo importując i uruchamiając raz `przeplyw_0_utworz_tabele.json`:

| Tabela `zgloszenia` – kolumna | Typ     |   | Tabela `zdarzenia` – kolumna | Typ    |
|-------------------------------|---------|---|------------------------------|--------|
| numer                         | string  |   | czas                         | string |
| id_wysylki                    | string  |   | numer                        | string |
| przyjeto                      | string  |   | zdarzenie                    | string |
| temat                         | string  |   | opis                         | string |
| tresc                         | string  |   | wykonanie                    | string |
| email                         | string  |   |                              |        |
| status                        | string  |   |                              |        |
| kategoria                     | string  |   |                              |        |
| priorytet                     | string  |   |                              |        |
| wymaga_czlowieka              | boolean |   |                              |        |
| propozycja_odpowiedzi         | string  |   |                              |        |
| odpowiedz_finalna             | string  |   |                              |        |
| link_zatwierdzenia            | string  |   |                              |        |
| tokeny_we / tokeny_wy         | number  |   |                              |        |
| koszt_usd                     | number  |   |                              |        |

Tabele n8n (Data tables) wystarczają do ćwiczeń. W firmie ten sam przepływ zapisuje dane
do bazy (np. PostgreSQL) albo do systemu zgłoszeń – zmienia się tylko węzeł zapisu.

## Krok 1. Plan przepływu (kartka, 15 min)

Dla każdego kroku zapisz: **wejście → przetwarzanie → decyzja → wynik**. Odpowiedz na pytania:
co się stanie, gdy dane są niekompletne? gdy formularz wyśle zgłoszenie dwa razy? gdy model nie odpowie?
kto zatwierdza odpowiedź i gdzie to widać?

## Krok 2. Webhook

Nowy przepływ „Obsługa zgłoszeń – [Twoje imię]” → węzeł **Webhook**:
- HTTP Method: `POST`, Path: `zgloszenie-[twoje-imie]`
- Respond: `Using 'Respond to Webhook' Node`
- Options → Allowed Origins (CORS): `*` (potrzebne w Module 7, gdy formularz wysyła dane z innej strony)

Test: **Listen for test event**, potem w terminalu na swoim komputerze
(adres testowy z zakładki „Test URL” wpisz w `.env` jako `WEBHOOK_URL`):

```
python m06_api/wyslij_webhook.py
```

Sprawdź w n8n wynik węzła: dane formularza są w polu **body**, obok `headers`, `params`, `query`.

## Krok 3. Walidacja i normalizacja

Węzeł **Code** o nazwie `Walidacja`, tryb *Run Once for Each Item* – kod [1] z `kod_wezlow.md`.
Wynik: płaski obiekt z polami zgłoszenia oraz `braki` (lista) i `kompletne` (true/false).

## Krok 4. Decyzja „Kompletne?”

Węzeł **If**: warunek *Boolean* → `{{ $json.kompletne }}` *is true*.

Gałąź **false** → węzeł **Respond to Webhook** `Odpowiedź 422`:
- Respond With: `JSON`, Response Code (Options): `422`
- Response Body: `{{ { "status": "blad", "bledy": $json.braki } }}`

## Krok 5. Duplikaty – „Czy już przyjęte?”

Gałąź **true** → węzeł **Data table** → operacja *Get row(s)*: tabela `zgloszenia`,
warunek `id_wysylki` = `{{ $json.id_wysylki }}`. W ustawieniach węzła (Settings) włącz **Always Output Data**
– inaczej przy braku wiersza przepływ się zatrzyma.

Węzeł **If** `Nowe?`: `{{ $json.numer }}` *is empty* (String).
- **false** (zgłoszenie już było) → **Respond to Webhook** `Odpowiedź 200`:
  `{{ { "status": "przyjete", "numer": $json.numer, "powtorzone": true } }}`
- **true** → krok 6.

> Dlaczego `id_wysylki`, a nie e-mail + treść? Klucz nadaje formularz przy każdym kliknięciu „Wyślij”.
> Ponowienie tej samej wysyłki ma ten sam klucz, a nowa sprawa tego samego klienta – nowy.

## Krok 6. Numer i zapis zgłoszenia

1. **Code** `Numer zgłoszenia` – kod [2] (bierze dane z węzła `Walidacja`).
2. **Data table** `Zapisz zgłoszenie` → *Insert row*, tabela `zgloszenia`, mapowanie pól:
   numer, id_wysylki, przyjeto, temat, tresc, email, status.
   Sprawdź, czy nazwy kolumn w tabeli i nazwy pól się zgadzają – błędne mapowanie
   nie zatrzyma przepływu, tylko zapisze puste wartości.
3. **Respond to Webhook** `Odpowiedź 201`, Response Code `201`:
   `{{ { "status": "przyjete", "numer": $('Numer zgłoszenia').item.json.numer } }}`

Po tym węźle klient ma już odpowiedź – przepływ działa dalej w tle.

## Krok 7. Model językowy – wariant A (24.10): węzeł n8n

Węzeł **Basic LLM Chain**:
- Prompt: *Define below* → wiadomość z sekcji „Wiadomość użytkownika” w `instrukcja_dla_modelu.md`
- Require Specific Output Format: **włączone** → podłącz **Structured Output Parser**
  (Schema Type: *Define using JSON Schema* → treść `schemat_odpowiedzi.json`)
- Chat Messages → System: instrukcja z `instrukcja_dla_modelu.md`
- Model: podłącz **Anthropic Chat Model** (dane uwierzytelniające kursu, model `claude-opus-5-5`)
  albo **OpenAI Chat Model** – zależnie od klucza kursu.

Do modelu trafiają tylko temat, numer zamówienia i treść – bez imienia, e-maila i telefonu.
Wynik parsera jest w polu `output`, np. `{{ $json.output.kategoria }}` – tak mapujemy pola w kolejnym kroku.
Jeśli model zwróci odpowiedź niezgodną ze schematem, węzeł zakończy się błędem – obsługę takich
przypadków dodajemy w części 2 (krok 11).

## Krok 8. Zapis klasyfikacji i zatwierdzenie przez człowieka

1. **Data table** `Zapisz klasyfikację` → *Update row(s)*: warunek `numer` = numer zgłoszenia;
   pola: kategoria, priorytet, wymaga_czlowieka, propozycja_odpowiedzi, status = `do_zatwierdzenia`,
   link_zatwierdzenia = `{{ $execution.resumeFormUrl }}`.
2. **Wait** `Zatwierdzenie` → Resume: *On Form Submitted*. Pola formularza:
   - `Decyzja` – lista: *zatwierdź*, *odrzuć* (wymagane)
   - `Odpowiedź do klienta` – pole tekstowe wielowierszowe
   - `Uwagi` – tekst
   Opis formularza: `Zgłoszenie {{ $('Numer zgłoszenia').item.json.numer }}: {{ $json.propozycja_odpowiedzi }}`
3. Osoba zatwierdzająca otwiera link z kolumny `link_zatwierdzenia` w tabeli.
4. **Data table** `Zapisz decyzję` → *Update row(s)*: status = `{{ $json.Decyzja === 'zatwierdź' ? 'zatwierdzone' : 'odrzucone' }}`,
   odpowiedz_finalna = `{{ $json['Odpowiedź do klienta'] }}`.

Wysyłkę e-maila do klienta dodajemy dopiero po zatwierdzeniu – i tylko z adresu testowego.

## Krok 9. Testy części 1

Przełącz Webhook w tryb testowy i wyślij kolejno przypadki 1–7:

```
python m06_api/wyslij_webhook.py --testy 1
```

| # | Przypadek | Oczekiwany wynik |
|---|-----------|------------------|
| 1 | Poprawne zgłoszenie | 201, wiersz w tabeli, klasyfikacja, link do zatwierdzenia |
| 2 | Ponowna wysyłka (ten sam `id_wysylki`) | 200 `powtorzone`, brak nowego wiersza i brak wywołania modelu |
| 3 | Niekompletne dane | 422 z listą braków |
| 4 | Próba zmiany instrukcji | 201, `wymaga_czlowieka = true`, brak obietnic w odpowiedzi |
| 5 | Zgłoszenie po angielsku | 201, poprawna kategoria |
| 6 | Złe typy i spacje | 201, dane znormalizowane |
| 7 | Temat spoza listy | 422 |

Zapisz w zeszycie: numer wykonania (Executions), wynik, czy zgodny z oczekiwanym.

---

## Część 2 (21.11): niezawodność, koszty, przetwarzanie zbiorów

## Krok 10. Model przez HTTP Request – wariant B

Zamień Basic LLM Chain na:
1. **Code** `Przygotuj zapytanie` – kod [3].
2. **HTTP Request** `Model – API Anthropic`:
   - Method `POST`, URL `https://api.anthropic.com/v1/messages`
   - Authentication: *Generic Credential Type* → *Header Auth* → nowe dane uwierzytelniające:
     Name `x-api-key`, Value = klucz kursu (klucz nie trafia do węzła ani do eksportu przepływu)
   - Send Headers: `anthropic-version: 2023-06-01`
   - Send Body: JSON → `{{ JSON.stringify($json.zapytanie) }}`
   - Options → Timeout: `60000`
3. **Code** `Kontrola odpowiedzi` – kod [4] (sprawdza format, wartości, liczy tokeny i koszt).
4. **If** `Poprawna?` → `{{ $json.poprawna }}` *is true*.

## Krok 11. Błędy i ponowienia

- HTTP Request → **Settings**: *Retry On Fail* = on, Max Tries `3`, Wait Between Tries `5000` ms.
- HTTP Request → Settings → *On Error*: **Continue (using error output)** → gałąź błędu:
  Data table *Update row* status = `blad_modelu` + **Code** [5] + **Data table** *Insert row* do `zdarzenia`.
- Gałąź `Poprawna? = false`: status `blad_klasyfikacji`, wpis do `zdarzenia`, zgłoszenie trafia do człowieka.
- Przepływ błędów: nowy przepływ z **Error Trigger** → wpis do `zdarzenia` (bez treści zgłoszenia).
  W ustawieniach głównego przepływu (Settings → Error Workflow) wskaż ten przepływ.

Test: zmień na chwilę klucz w danych uwierzytelniających na błędny – jaki kod zwraca API?
Czy ponawianie ma wtedy sens? (401 – nie; 429, 529, 5xx – tak).

## Krok 12. Przetwarzanie zbioru zgłoszeń (zaległości) – pokaz prowadzącego

Osobny przepływ: **Manual Trigger** → **Data table** *Get rows* (status = `nowe`) →
**Loop Over Items** (Batch Size `5`) → Przygotuj zapytanie → Model → Kontrola → Zapisz →
**Wait** 2 s (ochrona przed limitem wywołań) → z powrotem do pętli. Po pętli: **Code** [6] – podsumowanie.

## Krok 13. Pomiar: wywołania, koszt, czas

- Liczba wywołań i koszt: wynik węzła [6] oraz kolumny `tokeny_we`, `tokeny_wy`, `koszt_usd`.
- Czas: lista **Executions** (kolumna czasu wykonania) oraz czas poszczególnych węzłów w podglądzie wykonania.
- Uzupełnij tabelę w zeszycie: koszt na 1 zgłoszenie, koszt miesięczny przy 1000 zgłoszeń,
  porównanie z czasem pracy człowieka.

## Krok 14. Aktywacja

Przełącz przepływ na **Active**. Adres produkcyjny webhooka to `/webhook/…` (bez `-test`).
Podłącz go do formularza z Modułu 7 i wykonaj test całego procesu od strony WWW do zatwierdzenia.
