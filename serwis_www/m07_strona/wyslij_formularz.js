// =====================================================================
// Moduł 7 – wysyłka formularza do automatyzacji (n8n) z komunikatami
// Dołącz na końcu strony:  <script src="wyslij_formularz.js"></script>
// Formularz musi mieć id="formularz-zgloszenia", a pod nim element:
//   <div id="komunikat" role="status" aria-live="polite"></div>
// =====================================================================

// Adres produkcyjny webhooka n8n (Moduł 9, krok 14) – zawsze HTTPS
const ADRES_WEBHOOKA = "https://ADRES-SERWERA-N8N/webhook/zgloszenie-twoje-imie";
const LIMIT_CZASU_MS = 15000;

const formularz = document.getElementById("formularz-zgloszenia");
const komunikat = document.getElementById("komunikat");
const przycisk = formularz.querySelector('button[type="submit"]');

function pokaz(tekst, rodzaj) {
  komunikat.className = `komunikat ${rodzaj}`;      // klasy .komunikat.sukces / .komunikat.blad z style.css
  komunikat.innerHTML = tekst;
}

formularz.addEventListener("submit", async (zdarzenie) => {
  zdarzenie.preventDefault();                       // zamiast przeładowania strony – wysyłka w tle
  if (!formularz.reportValidity()) return;          // sprawdzenie w przeglądarce (wygoda, nie ochrona!)

  const dane = Object.fromEntries(new FormData(formularz));
  dane.id_wysylki = crypto.randomUUID();            // klucz idempotencji: ponowienie = to samo zgłoszenie

  przycisk.disabled = true;                         // brak podwójnego kliknięcia
  pokaz("Wysyłanie…", "");
  const przerwij = new AbortController();
  const zegar = setTimeout(() => przerwij.abort(), LIMIT_CZASU_MS);

  try {
    const odp = await fetch(ADRES_WEBHOOKA, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(dane),
      signal: przerwij.signal
    });
    const wynik = await odp.json().catch(() => ({}));
    if (odp.ok) {
      pokaz(`Dziękujemy! Numer zgłoszenia: <b>${wynik.numer ?? "nadany"}</b>. Odpowiemy w ciągu 2 dni roboczych.`, "sukces");
      formularz.reset();
    } else if (odp.status === 422 && Array.isArray(wynik.bledy)) {
      pokaz("Popraw dane:<ul>" + wynik.bledy.map(b => `<li>${b}</li>`).join("") + "</ul>", "blad");
    } else {
      pokaz(`Nie udało się wysłać zgłoszenia (kod ${odp.status}). Spróbuj za chwilę.`, "blad");
    }
  } catch (blad) {
    const powod = blad.name === "AbortError" ? "Serwer nie odpowiedział na czas." : "Brak połączenia z serwerem.";
    pokaz(`${powod} Twoje dane nie zostały utracone – spróbuj ponownie.`, "blad");
    console.error("Wysyłka formularza:", blad);     // szczegóły dla nas – w Konsoli przeglądarki
  } finally {
    clearTimeout(zegar);
    przycisk.disabled = false;
  }
});
