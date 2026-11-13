# Checklista: strona przed i po publikacji (Moduł 7)

## Przed publikacją – na swoim komputerze
- [ ] `<!DOCTYPE html>`, `<html lang="pl">`, `<meta name="viewport" …>` – są na stronie
- [ ] Każde pole formularza ma `<label for="…">` powiązany z `id` pola i atrybut `name`
- [ ] Tab przechodzi po wszystkich elementach w logicznej kolejności; fokus jest widoczny
- [ ] Przyciski to `<button>`, a nie `<div onclick>`; pytania FAQ działają z klawiatury (`<details>`)
- [ ] Obrazy mają `alt` (albo `alt=""`, jeśli są tylko ozdobą)
- [ ] Kontrast tekstu ≥ 4,5 : 1 (narzędzia przeglądarki → Elementy → podgląd koloru)
- [ ] Tryb urządzenia 360 px: brak przewijania w poziomie, przycisk w całości widoczny
- [ ] Komunikat o powodzeniu pokazuje się dopiero po odpowiedzi serwera (a nie od razu po kliknięciu)
- [ ] Błąd serwera i brak połączenia → czytelny komunikat; dane w formularzu nie znikają
- [ ] W kodzie strony nie ma kluczy API, haseł ani adresów testowych (`localhost`, `webhook-test`)

## Publikacja
- [ ] Wybrane miejsce: Netlify (Drop lub repozytorium), GitHub Pages albo Cloudflare Pages
- [ ] Adres strony zaczyna się od `https://` – kłódka w przeglądarce, certyfikat ważny
- [ ] Jeśli własna domena: rekord DNS (`CNAME` dla subdomeny albo `A` dla domeny głównej) ustawiony
      zgodnie z instrukcją usługi; certyfikat HTTPS wystawiony automatycznie
- [ ] Webhook n8n działa w trybie aktywnym (`/webhook/…`), adres w stałej `ADRES_WEBHOOKA`

## Po publikacji – test całego procesu
- [ ] Strona otwiera się na telefonie (sieć komórkowa, nie Wi-Fi biura)
- [ ] Konsola przeglądarki bez błędów (szczególnie „CORS” i „Mixed Content”)
- [ ] Poprawne zgłoszenie → numer na stronie → wiersz w tabeli n8n → klasyfikacja → link do zatwierdzenia
- [ ] Niepełne zgłoszenie → komunikat o błędzie → brak wiersza w tabeli
- [ ] Szybkie dwukrotne kliknięcie „Wyślij” → jedno zgłoszenie w tabeli
- [ ] Wyłączony przepływ n8n → strona pokazuje komunikat o błędzie, a nie „Dziękujemy”

## Typowe błędy po publikacji
| Objaw w Konsoli | Przyczyna | Rozwiązanie |
|-----------------|-----------|-------------|
| `blocked by CORS policy` | Webhook nie zezwala na żądania z adresu strony | Webhook → Options → Allowed Origins: adres strony (albo `*` w ćwiczeniach) |
| `Mixed Content … was loaded over HTTPS, but requested an insecure resource` | Strona HTTPS wysyła dane na adres `http://` | Webhook tylko przez HTTPS |
| `404` z adresu `/webhook-test/…` | Adres testowy działa tylko po kliknięciu „Listen for test event” | Użyj adresu `/webhook/…` i aktywuj przepływ |
| `Failed to fetch` / `ERR_NAME_NOT_RESOLVED` | Literówka w adresie albo serwer nieosiągalny z internetu | Sprawdź adres; `localhost` działa tylko na Twoim komputerze |
