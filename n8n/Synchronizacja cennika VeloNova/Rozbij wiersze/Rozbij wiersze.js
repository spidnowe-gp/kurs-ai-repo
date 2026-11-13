// Po wyczyszczeniu tabeli zwraca przygotowane wiersze jako osobne elementy do zapisu
return $('Przygotuj wiersze').first().json.wiersze.map(w => ({ json: w }));
