// =====================================================================
// Moduł 3 – wysyłka zapytania ze strony VeloNova do przepływu n8n (webhook)
// Strona: zapytanie.html (formularz id="formularz-zapytania", komunikat id="komunikat")
// Przepływ: Webhook (POST, Respond: Using 'Respond to Webhook' Node, Allowed Origins)
//           → Sprawdź dane (Code) → 201 z numerem albo 422 z listą błędów
// =====================================================================

// Production URL z węzła Webhook – zawsze HTTPS; w teście: Test URL i „Listen for test event”
// Przy uruchomionym serwer_formularza.py ten wiersz jest podmieniany na lokalny adres przekazania
// (serwer dokłada nagłówek api-key z .env, więc klucz nie trafia do przeglądarki).
const ADRES_WEBHOOKA = "https://n8n-kurs.tailf6aa90.ts.net/webhook/velonova-zapytanie-TWOJE-IMIE";
const LIMIT_CZASU_MS = 90000;                       // przepływ odpowiada po zakończeniu pracy AI Agenta

const formularz = document.getElementById("formularz-zapytania");
const komunikat = document.getElementById("komunikat");
const przycisk = formularz.querySelector('button[type="submit"]');

function pokaz(tekst, rodzaj) {
  komunikat.className = `komunikat ${rodzaj}`;      // klasy .komunikat.sukces / .komunikat.blad z style.css
  komunikat.textContent = "";
  for (const linia of [].concat(tekst)) {           // tekst albo lista linii; bez innerHTML – bezpieczniej
    const p = document.createElement("p");
    p.textContent = linia;
    komunikat.appendChild(p);
  }
}

formularz.addEventListener("submit", async (zdarzenie) => {
  zdarzenie.preventDefault();                       // zamiast przeładowania strony – wysyłka w tle
  if (!formularz.reportValidity()) return;          // sprawdzenie w przeglądarce (wygoda, nie ochrona!)

  const dane = Object.fromEntries(new FormData(formularz));
  dane.zgoda = formularz.zgoda.checked;             // checkbox → true / false
  dane.id_wysylki = crypto.randomUUID();            // identyfikator zapytania (ponowienie = to samo zapytanie)

  przycisk.disabled = true;                         // brak podwójnego kliknięcia
  pokaz("Wysyłanie…", "");
  const przerwij = new AbortController();
  const zegar = setTimeout(() => przerwij.abort(), LIMIT_CZASU_MS);

  try {
    const odp = await fetch(ADRES_WEBHOOKA, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(dane),
      signal: przerwij.signal,
    });
    const wynik = await odp.json().catch(() => ({}));
    if (odp.ok) {
      pokaz(`Dziękujemy! Numer zapytania: ${wynik.numer ?? wynik.zamowienie_id ?? "nadany"}. Odpowiedź wyślemy e-mailem.`, "sukces");
      formularz.reset();
    } else if ((odp.status === 400 || odp.status === 422) && Array.isArray(wynik.bledy)) {
      pokaz(["Popraw dane:", ...wynik.bledy], "blad");
    } else {
      pokaz(`Nie udało się wysłać zapytania (kod ${odp.status}). Spróbuj za chwilę.`, "blad");
    }
  } catch (blad) {
    const powod = blad.name === "AbortError" ? "Serwer nie odpowiedział na czas." : "Brak połączenia z serwerem.";
    pokaz(`${powod} Sprawdź adres webhooka i zakładkę Sieć (F12).`, "blad");
  } finally {
    clearTimeout(zegar);
    przycisk.disabled = false;
  }
});
