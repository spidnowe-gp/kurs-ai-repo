"""
Atrapa API modelu (Anthropic Messages API) – test przepływu n8n bez kosztów i bez klucza.

Uruchomienie:
    python m09_n8n/atrapa_modelu.py                    – nasłuch na 127.0.0.1:8099
    python m09_n8n/atrapa_modelu.py --host 0.0.0.0     – gdy n8n działa w Dockerze na tym samym komputerze

Adres do wpisania w węźle HTTP Request „Model – API Anthropic” na czas testu:
    http://127.0.0.1:8099/v1/messages                  (n8n uruchomione bez Dockera)
    http://host.docker.internal:8099/v1/messages       (n8n w Dockerze)
Dane uwierzytelniające Header Auth: nazwa x-api-key, dowolna wartość. Wartość „zly” → odpowiedź 401.

Atrapa klasyfikuje zgłoszenie prostymi regułami słów kluczowych i zwraca odpowiedź
w tym samym kształcie co prawdziwe API (content, stop_reason, usage). Po teście
przywróć w węźle adres https://api.anthropic.com/v1/messages.
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KATEGORIE = [("faktur", "faktura"), ("zwrot", "zwrot"), ("odstępuję", "zwrot"), ("reklamac", "reklamacja"),
             ("nagrzał", "reklamacja"), ("error", "reklamacja"), ("nie działa", "reklamacja"),
             ("paczk", "zamowienie"), ("dostaw", "zamowienie"), ("bluetooth", "pytanie_techniczne")]


def klasyfikuj(tekst: str) -> dict:
    t = tekst.lower()
    kategoria = next((k for slowo, k in KATEGORIE if slowo in t), "inne")
    wysoki = any(s in t for s in ("nagrzał", "spalenizn", "dym", "przyspiesza"))
    proba_zmiany = any(s in t for s in ("zignoruj", "ignore previous", "ignore all"))
    return {
        "kategoria": kategoria,
        "priorytet": "wysoki" if wysoki else "normalny",
        "podsumowanie": "Zgłoszenie testowe sklasyfikowane przez atrapę modelu.",
        "brakujace_dane": [] if "vn-" in t else ["numer zamówienia"],
        "propozycja_odpowiedzi": "Dzień dobry, dziękujemy za zgłoszenie. Sprawdzimy sprawę i odpowiemy "
                                 "w ciągu 2 dni roboczych. Zespół VeloNova",
        "wymaga_czlowieka": wysoki or proba_zmiany,
    }


class Atrapa(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.rstrip("/") != "/v1/messages":
            self.odpowiedz(404, {"type": "error", "error": {"type": "not_found_error", "message": self.path}})
            return
        klucz = self.headers.get("x-api-key", "")
        if not klucz or klucz == "zly":
            self.odpowiedz(401, {"type": "error", "error": {"type": "authentication_error",
                                                           "message": "invalid x-api-key"}})
            return
        dlugosc = int(self.headers.get("Content-Length", 0))
        try:
            zapytanie = json.loads(self.rfile.read(dlugosc) or b"{}")
        except json.JSONDecodeError:
            self.odpowiedz(400, {"type": "error", "error": {"type": "invalid_request_error", "message": "bad JSON"}})
            return
        tresc = " ".join(str(m.get("content", "")) for m in zapytanie.get("messages", []))
        wynik = klasyfikuj(tresc)
        print(f"Atrapa: {wynik['kategoria']:18} {wynik['priorytet']:9} człowiek={wynik['wymaga_czlowieka']}", flush=True)
        self.odpowiedz(200, {
            "id": "msg_atrapa", "type": "message", "role": "assistant", "model": zapytanie.get("model", "atrapa"),
            "content": [{"type": "text", "text": json.dumps(wynik, ensure_ascii=False)}],
            "stop_reason": "end_turn", "usage": {"input_tokens": 1200, "output_tokens": 350},
        })

    def odpowiedz(self, kod: int, dane: dict) -> None:
        cialo = json.dumps(dane, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cialo)))
        self.end_headers()
        self.wfile.write(cialo)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atrapa API modelu do testów n8n")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8099)
    a = parser.parse_args()
    print(f"Atrapa modelu: http://{a.host}:{a.port}/v1/messages  (zatrzymanie: Ctrl+C)", flush=True)
    try:
        ThreadingHTTPServer((a.host, a.port), Atrapa).serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymano atrapę.")
