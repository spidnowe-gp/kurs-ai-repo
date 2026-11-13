// Stan rozmowy na czacie WWW. Nowa rozmowa (nowy klucz pamięci agenta) zaczyna się, gdy:
// - klient wyraźnie zakończył poprzednią rozmowę (zakonczona = true w ostatnim wierszu),
// - od ostatniej odpowiedzi czatu minęło ponad 2 minuty bez odpowiedzi klienta.
const LIMIT_CISZY_MS = 2 * 60 * 1000;
const dane = $('Waliduj czat').first().json;
const ostatni = $input.first()?.json ?? {};   // pusty obiekt, gdy to pierwsza wiadomość w sesji

let rozmowa = 1;
let powod = '';
if (ostatni.id) {
  rozmowa = Number(ostatni.rozmowa) || 1;
  const cisza = Date.now() - new Date(ostatni.createdAt).getTime();
  if (ostatni.zakonczona === true) {
    rozmowa += 1;
    powod = 'zakonczona_przez_klienta';
  } else if (cisza > LIMIT_CISZY_MS) {
    rozmowa += 1;
    powod = 'brak_odpowiedzi';
  }
}

return [{ json: {
  ...dane,
  czat_klucz: dane.thread_id,
  thread_id: `${dane.thread_id}-${rozmowa}`,
  numer_rozmowy: rozmowa,
  powod_nowej_rozmowy: powod,
} }];
