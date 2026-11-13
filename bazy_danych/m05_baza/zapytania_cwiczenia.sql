-- ============================================================
-- Moduł 5 – Praca z bazą danych. Plik: m05_baza/zgloszenia.db
-- Zapytania wykonuj pojedynczo (zaznacz zapytanie → Ctrl+Enter / Cmd+Enter
-- w DB Browser for SQLite, zakładka „Wykonaj SQL”).
-- PRZED uruchomieniem zapisz w zeszycie, jakiego wyniku się spodziewasz.
-- ============================================================

-- 5.1 Odczyt: ile jest zgłoszeń i jakie mają kolumny?
SELECT COUNT(*) AS liczba_zgloszen FROM zgloszenia;
SELECT * FROM zgloszenia LIMIT 5;

-- 5.2 Filtrowanie i sortowanie
-- a) Przewidź: ile wierszy zwróci zapytanie? (podpowiedź: status nowe i temat reklamacja)
SELECT numer, data_wplywu, temat, status
FROM zgloszenia
WHERE status = 'nowe' AND temat = 'reklamacja'
ORDER BY data_wplywu;

-- b) Zgłoszenia o priorytecie wysokim – najnowsze na górze
SELECT numer, priorytet, status, data_wplywu
FROM zgloszenia
WHERE priorytet = 'wysoki'
ORDER BY data_wplywu DESC;

-- c) Uwaga na NULL: dlaczego to zapytanie NIE zwraca zgłoszeń bez priorytetu?
SELECT COUNT(*) FROM zgloszenia WHERE priorytet <> 'wysoki';
-- Popraw je tak, aby liczyło także zgłoszenia, w których priorytet jest pusty (NULL):
-- SELECT COUNT(*) FROM zgloszenia WHERE priorytet <> 'wysoki' OR priorytet IS NULL;

-- 5.3 Grupowanie: liczba zgłoszeń według tematu
SELECT temat, COUNT(*) AS liczba
FROM zgloszenia
GROUP BY temat
ORDER BY liczba DESC;

-- 5.4 Łączenie dwóch tabel (JOIN)
-- a) Zgłoszenia z danymi klienta
SELECT z.numer, k.imie_nazwisko, k.email, z.temat
FROM zgloszenia AS z
JOIN klienci AS k ON k.id = z.klient_id
ORDER BY z.numer;

-- b) Przewidź: czym różni się wynik LEFT JOIN od JOIN? Których zgłoszeń brakowało w a)?
SELECT z.numer, k.email, z.kanal
FROM zgloszenia AS z
LEFT JOIN klienci AS k ON k.id = z.klient_id
WHERE k.id IS NULL;

-- 5.5 Duplikaty – identyfikator zgłoszenia
-- a) Które numery występują więcej niż raz?
SELECT numer, COUNT(*) AS ile, MIN(id) AS pierwszy_id
FROM zgloszenia
GROUP BY numer
HAVING COUNT(*) > 1;

-- b) Usunięcie duplikatów – zostaje wiersz o najmniejszym id.
--    NAJPIERW zrób kopię bazy:  python m05_baza/kopia_zapasowa.py kopia
--    Uwaga: zdarzenia duplikatów też trzeba usunąć (inaczej zostaną „osierocone”).
-- DELETE FROM zdarzenia WHERE zgloszenie_id NOT IN (SELECT MIN(id) FROM zgloszenia GROUP BY numer);
-- DELETE FROM zgloszenia WHERE id NOT IN (SELECT MIN(id) FROM zgloszenia GROUP BY numer);

-- c) Zabezpieczenie na przyszłość: unikalny indeks na numerze zgłoszenia
-- CREATE UNIQUE INDEX ux_zgloszenia_numer ON zgloszenia(numer);

-- d) Ponowne wysłanie tego samego zgłoszenia nie tworzy już duplikatu:
-- INSERT INTO zgloszenia (numer, temat, tresc) VALUES ('ZG-0003', 'zamowienie', 'ponowienie')
-- ON CONFLICT(numer) DO NOTHING;

-- 5.6 Modyfikacja danych – zawsze z WHERE!
-- Przewidź: ile wierszy zmieni to polecenie? Co by się stało bez WHERE?
-- UPDATE zgloszenia SET status = 'w_toku' WHERE numer = 'ZG-0026';
-- INSERT INTO zdarzenia (zgloszenie_id, czas, typ, opis)
-- SELECT id, datetime('now'), 'zmiana_statusu', 'nowe → w_toku' FROM zgloszenia WHERE numer = 'ZG-0026';

-- 5.7 Historia zgłoszenia – zdarzenia w kolejności
SELECT z.numer, d.czas, d.typ, d.opis
FROM zdarzenia AS d
JOIN zgloszenia AS z ON z.id = d.zgloszenie_id
WHERE z.numer = 'ZG-0026'
ORDER BY d.czas;
