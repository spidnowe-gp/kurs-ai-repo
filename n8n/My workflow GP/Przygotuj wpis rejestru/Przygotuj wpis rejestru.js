// Dokłada pola do rejestru zapytań: nową część wiadomości po anonimizacji (bez cytatów i linków) i czas startu obsługi przez AI
return $input.all().map((item, index) => {
  const tekst = String(item.json.email_text || '');
  const linie = tekst.split('\n');
  const koniec = linie.findIndex(l => /^\s*(W dniu \d|On .+wrote|-{2,}\s*(Original|Oryginalna)|Od:\s)/i.test(l));
  const nowa = (koniec >= 0 ? linie.slice(0, koniec) : linie)
    .filter(l => !/^\s*>/.test(l)).join('\n').trim();
  const tresc = (nowa || tekst).replace(/https?:\/\/\S+/g, '[LINK]').slice(0, 20000);
  return { json: { ...item.json, rejestr_tresc: tresc, rejestr_start_ms: Date.now() }, pairedItem: { item: index } };
});
