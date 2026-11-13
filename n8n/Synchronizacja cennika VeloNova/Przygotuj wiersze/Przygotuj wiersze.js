// Zamienia wiersze arkusza na wiersze tabeli cennik_velonova. Pusty lub niepełny odczyt przerywa
// synchronizację, żeby nie wyczyścić ostatniej dobrej kopii cennika.
const liczba = v => (v === '' || v === null || v === undefined || isNaN(Number(v)) ? null : Number(v));
const teraz = $now.setZone('Europe/Warsaw').toFormat('dd.MM.yyyy HH:mm');
const wiersze = $input.all().map(i => i.json).filter(r => r.sku && r.nazwa).map(r => ({
  sku: String(r.sku),
  nazwa: String(r.nazwa),
  kategoria: String(r.kategoria ?? ''),
  cena_brutto_pln: liczba(r.cena_brutto_pln),
  stan_magazynowy: liczba(r.stan_magazynowy),
  zasieg_km: liczba(r.zasieg_km),
  max_obciazenie_kg: liczba(r.max_obciazenie_kg),
  opis: String(r.opis ?? ''),
  zrodlo_danych: `arkusz, synchronizacja ${teraz}`,
}));
if (wiersze.length === 0) throw new Error('Arkusz cennika nie zwrócił żadnych produktów – kopia zostaje bez zmian.');
return [{ json: { wiersze } }];
