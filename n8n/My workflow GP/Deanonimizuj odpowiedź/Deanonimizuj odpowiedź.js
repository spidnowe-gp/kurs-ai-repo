// Przywraca prawdziwe dane w wyniku AI Agent – odwrotność węzła „Anonimizuj dane” (przywroc_tekst z anonimizuj.py).
// Dłuższe znaczniki zamieniane są najpierw, żeby [OSOBA_1] nie podmienił fragmentu [OSOBA_10].
const mapa = $('Anonimizuj dane').first().json.mapa_anonimizacji || {};
const znaczniki = Object.keys(mapa).sort((a, b) => b.length - a.length);

function przywroc(wartosc) {
  if (typeof wartosc === 'string') {
    for (const znacznik of znaczniki) wartosc = wartosc.split(znacznik).join(mapa[znacznik]);
    return wartosc;
  }
  if (Array.isArray(wartosc)) return wartosc.map(przywroc);
  if (wartosc && typeof wartosc === 'object') {
    return Object.fromEntries(Object.entries(wartosc).map(([klucz, v]) => [klucz, przywroc(v)]));
  }
  return wartosc;
}

return $input.all().map((item, index) => ({ json: przywroc(item.json), pairedItem: { item: index } }));
