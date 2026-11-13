// Bierze wynik agenta (obiekt z Structured Output Parser) i dokłada dane zgłoszenia potrzebne do szkicu, logu i odpowiedzi WWW lub czatu
const ctx = $('Przygotuj kontekst').isExecuted
  ? $('Przygotuj kontekst').first().json
  : $('Waliduj czat').isExecuted
    ? $('Waliduj czat').first().json
    : $('Waliduj zamówienie').first().json;
const agent = $input.first().json;
const out = agent.output;

let w;
try {
  if (out && typeof out === 'object') {
    w = out;
  } else {
    const raw = String(out ?? '');
    w = JSON.parse(raw.slice(raw.indexOf('{'), raw.lastIndexOf('}') + 1));
  }
} catch (e) {
  w = null;
}
if (!w || !w.decyzja) {
  w = {
    kategoria: 'inne', decyzja: 'do_decyzji',
    uzasadnienie: 'Nie udało się odczytać wyniku agenta.',
    tryb_oferty: null, produkty: [], waluta: null, suma_brutto: null,
    tresc_odpowiedzi: null, pytania_do_klienta: [],
    uwagi: 'Błąd agenta lub parsera: ' + String(agent.error ?? JSON.stringify(out ?? null)).slice(0, 5000),
    wymaga_czlowieka: true,
  };
}

const zrodlo = ctx.zrodlo || 'email';
const typZgloszenia = ctx.typ_zgloszenia || '';
const temat = ctx.email_subject || '';
const tematOdpowiedzi = /^re:/i.test(temat) ? temat : `Re: ${temat}`;
const jestOdpowiedz = w.kategoria === 'zapytanie'
  && ['dopytaj', 'przygotuj_oferte', 'potwierdz_zakup', 'do_decyzji'].includes(w.decyzja)
  && typeof w.tresc_odpowiedzi === 'string' && w.tresc_odpowiedzi.trim() !== '';
// Szkic w wątku Gmaila dla maili z zapytaniem sprzedażowym; dla zapytań z formularza WWW – nowy mail do klienta.
// Zamówienia WWW i czat dostają odpowiedź bezpośrednio na stronie.
const maOdpowiedz = zrodlo === 'email' && jestOdpowiedz;
const szkicWww = zrodlo === 'www' && typZgloszenia === 'zapytanie' && jestOdpowiedz;

let raw = null;
if (maOdpowiedz || szkicWww) {
  const b64 = s => Buffer.from(s, 'utf8').toString('base64');
  const dataMaila = ctx.email_date
    ? DateTime.fromISO(ctx.email_date).setZone('Europe/Warsaw').toFormat('dd.MM.yyyy HH:mm')
    : '';
  const cytat = String(ctx.email_text || '').split('\n').map(l => `> ${l}`).join('\n');
  const wstepCytatu = szkicWww
    ? `Zapytanie wysłane przez formularz na stronie WWW (${dataMaila}):`
    : `W dniu ${dataMaila} ${ctx.nadawca} napisał(a):`;
  const tresc = `${w.tresc_odpowiedzi.trim()}\n\n${wstepCytatu}\n${cytat}`;
  const tematMaila = szkicWww ? 'Odpowiedź na zapytanie ze strony WWW' : tematOdpowiedzi;
  const naglowki = [
    `To: ${ctx.nadawca_adres}`,
    `Subject: =?UTF-8?B?${b64(tematMaila)}?=`,
    maOdpowiedz && ctx.email_message_id ? `In-Reply-To: ${ctx.email_message_id}` : null,
    maOdpowiedz && ctx.email_message_id ? `References: ${[ctx.email_references, ctx.email_message_id].filter(Boolean).join(' ')}` : null,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset="UTF-8"',
    'Content-Transfer-Encoding: base64',
  ].filter(Boolean);
  const mime = `${naglowki.join('\r\n')}\r\n\r\n${b64(tresc).replace(/.{76}/g, '$&\r\n')}`;
  raw = b64(mime).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

return [{ json: {
  ...w,
  zrodlo,
  typ_zgloszenia: typZgloszenia,
  thread_id: ctx.thread_id,
  message_id: ctx.message_id,
  nadawca: ctx.nadawca,
  nadawca_adres: ctx.nadawca_adres,
  temat,
  temat_odpowiedzi: tematOdpowiedzi,
  wiadomosc_klienta: String(ctx.nowa_tresc || ctx.email_text || '').slice(0, 20000),
  ma_odpowiedz: maOdpowiedz,
  szkic_www: szkicWww,
  raw,
} }];
