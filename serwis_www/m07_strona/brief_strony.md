# Brief: strona „Centrum pomocy VeloNova” (Moduł 7)

Firma fikcyjna. Strona ćwiczeniowa – publikowana tylko w środowisku demonstracyjnym.

## Cel strony
Klient w 2 minuty znajduje odpowiedź na typowe pytanie albo wysyła zgłoszenie,
które trafia do przepływu n8n z Modułu 9.

## Odbiorcy
Klienci sklepu (hulajnogi i rowery elektryczne), w większości na telefonie.

## Wymagania – treść i układ
1. Nagłówek z nazwą „VeloNova – Centrum pomocy” i krótkim zdaniem, w czym pomagamy.
2. Sekcja „Najczęstsze pytania” – 4 pytania z odpowiedziami (rozwijane): zwrot towaru (14 dni),
   status zamówienia, reklamacja (co przygotować: numer zamówienia, numer seryjny, opis, zdjęcia),
   ładowanie baterii (nie ładować bez nadzoru, przy przegrzaniu – odłączyć i nie używać).
3. Formularz zgłoszenia – pola jak w `m03_formularz/index.html`.
4. Informacja: „Propozycję odpowiedzi przygotowuje system AI, każdą odpowiedź sprawdza i wysyła pracownik.”
5. Stopka: dane firmy (fikcyjne), link do informacji o przetwarzaniu danych.

## Wymagania – jakość
- Działa na telefonie (szerokość 360 px) i na komputerze.
- Obsługa wyłącznie klawiaturą: Tab przechodzi po polach, widać, gdzie jest fokus, Enter wysyła.
- Każde pole ma etykietę; komunikaty o błędach są przy polu i czytelne dla czytnika ekranu.
- Kontrast tekstu co najmniej 4,5 : 1.
- Po wysłaniu: komunikat o powodzeniu z numerem zgłoszenia albo czytelny komunikat o błędzie;
  przycisk zablokowany na czas wysyłania (brak podwójnego wysłania).
- Kolorystyka: granat lub zieleń jako kolor główny, białe tło, jeden kolor akcentu.
- Bez zewnętrznych bibliotek i śledzenia; jeden plik HTML + CSS + JS.

## Kryteria odbioru
- [ ] Wszystkie sekcje 1–5 są na stronie.
- [ ] Test na telefonie (tryb urządzenia w przeglądarce) – bez przewijania w poziomie.
- [ ] Test klawiaturą – całe zgłoszenie da się wysłać bez myszy.
- [ ] Wysłanie poprawnego zgłoszenia → numer zgłoszenia na stronie i wiersz w tabeli n8n.
- [ ] Wysłanie niepełnego zgłoszenia → komunikat o błędzie, brak wiersza w tabeli.
- [ ] Strona opublikowana pod adresem HTTPS; test całego procesu wykonany po publikacji.

## Polecenie dla AI (punkt wyjścia)

> Przygotuj jedną stronę HTML (z CSS i JavaScript w tym samym pliku) według briefu poniżej.
> Użyj semantycznego HTML (header, main, section, footer), etykiet `<label for>` dla wszystkich pól
> i elementów `<details>` dla pytań. Formularz wysyła dane jako JSON metodą POST pod adres zapisany
> w stałej `ADRES_WEBHOOKA` na początku skryptu. Dodaj pole ukryte `id_wysylki` (losowy identyfikator
> nadawany przy każdym wysłaniu), blokadę przycisku w czasie wysyłki i komunikaty o powodzeniu oraz błędzie.
> Nie używaj zewnętrznych bibliotek. [wklej brief]
