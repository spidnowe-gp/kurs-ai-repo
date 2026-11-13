// Łączy bieżącego maila z wcześniejszymi wpisami z logu dla tego samego wątku Gmail
const email = $('Edit Fields').first().json;
const wpisy = $input.all().map(i => i.json).filter(r => r.thread_id);

const historia = wpisy.map(r => {
  let s = `[${r.data}] KLIENT:\n${r.wiadomosc_klienta}`;
  if (r.odpowiedz_agenta) {
    s += `\n\n[${r.data}] NASZ PROJEKT ODPOWIEDZI (decyzja: ${r.decyzja}):\n${r.odpowiedz_agenta}`;
  }
  return s;
}).join('\n\n---\n\n');

// Nowa część wiadomości bez cytowanej korespondencji
const linie = String(email.email_text || '').split('\n');
const koniec = linie.findIndex(l => /^\s*(W dniu \d|On .+wrote|-{2,}\s*(Original|Oryginalna)|Od:\s)/i.test(l));
const nowaTresc = (koniec >= 0 ? linie.slice(0, koniec) : linie)
  .filter(l => !/^\s*>/.test(l)).join('\n').trim();

// Temat sprzedażowy: kontynuacja zapytania z logu albo słowa związane z ofertą sklepu
const SLOWA = /hulajnog|rower|e-?bike|velonova|bateri|akumulator|ładowar|opon|kask|u-?lock|zapięci|cennik|ofert|\bcen[aeyę]\b|kosztuj|kupi|kupn|zamów|zamaw|zakup|dostaw|wysyłk|przegląd|serwis/i;
const kontynuacja = wpisy.some(r => r.kategoria === 'zapytanie');
const tematSprzedazowy = kontynuacja || SLOWA.test(`${email.email_subject || ''}\n${nowaTresc}`);

return [{ json: {
  ...email,
  nowa_tresc: nowaTresc,
  temat_sprzedazowy: tematSprzedazowy,
  historia: historia || 'Brak wcześniejszej korespondencji w tym wątku.',
} }];
