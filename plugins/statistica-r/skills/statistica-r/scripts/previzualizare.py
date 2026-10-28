#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Previzualizarea unei verificări, ca într-un program de statistică: panoul „Date” și panoul „Rezultate”.

    python previzualizare.py <dosar> [port]       # implicit 8775

Panoul „Date” arată tabelele din dosar (.csv și .csv.gz), rând cu rând, cu numărul rândului și pagini de câte 200.
Panoul „Rezultate” arată fișierele *_iesire.json scrise de scripturile R prin iesire.R — fiecare model cu tabelul
coeficienților, N, grupuri, eroare și R² — și rapoartele de comparație cu Python (comparatie*.md).
Serverul citește dosarul la fiecare cerere a listei, deci o rulare nouă se vede la reîncărcarea paginii.
Ascultă numai pe 127.0.0.1: datele nu pleacă de pe calculator.
"""
import csv
import glob
import gzip
import io
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

AICI = os.path.dirname(os.path.abspath(__file__))
DOSAR = sys.argv[1] if len(sys.argv) > 1 else "."
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8775
PAGINA = os.path.join(AICI, "previzualizare.html")
_cache = {}


def seturi():
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(DOSAR, "*.csv")) + glob.glob(os.path.join(DOSAR, "*.csv.gz")))


def randuri(nume):
    p = os.path.join(DOSAR, os.path.basename(nume))
    cheie = (p, os.path.getmtime(p))
    if cheie not in _cache:
        _cache.clear()
        deschide = gzip.open if p.endswith(".gz") else io.open
        with deschide(p, "rt", encoding="utf-8-sig") as f:
            linii = f.read().splitlines()
        _cache[cheie] = linii
    return _cache[cheie]


def imparte(linie):
    return next(csv.reader([linie]))


def rezultate():
    out = []
    for p in sorted(glob.glob(os.path.join(DOSAR, "*_iesire.json"))):
        with io.open(p, encoding="utf-8") as f:
            d = json.load(f)
        d["fisier"] = os.path.basename(p)
        out.append(d)
    comparatii = []
    for p in sorted(glob.glob(os.path.join(DOSAR, "comparatie*.md"))):
        comparatii.append({"fisier": os.path.basename(p), "text": io.open(p, encoding="utf-8").read()})
    return {"iesiri": out, "comparatii": comparatii}


class H(BaseHTTPRequestHandler):
    def trimite(self, cod, corp, tip):
        b = corp.encode("utf-8") if isinstance(corp, str) else corp
        self.send_response(cod)
        self.send_header("Content-Type", tip)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def json(self, x):
        self.trimite(200, json.dumps(x, ensure_ascii=False), "application/json; charset=utf-8")

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/":
                self.trimite(200, io.open(PAGINA, encoding="utf-8").read(), "text/html; charset=utf-8")
            elif u.path == "/api/seturi":
                self.json([{"nume": s, "randuri": len(randuri(s)) - 1, "coloane": imparte(randuri(s)[0])} for s in seturi()])
            elif u.path == "/api/date":
                r = randuri(q["set"][0])
                de_la, cate = int(q.get("de_la", ["0"])[0]), min(int(q.get("cate", ["200"])[0]), 1000)
                self.json({"randuri": [imparte(x) for x in r[1 + de_la:1 + de_la + cate]]})
            elif u.path == "/api/rezultate":
                self.json(rezultate())
            else:
                self.trimite(404, "nu există", "text/plain; charset=utf-8")
        except Exception as e:  # eroarea se arată în pagină, nu oprește serverul
            self.trimite(500, str(e), "text/plain; charset=utf-8")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("previzualizare: http://127.0.0.1:%d  (dosar %s)" % (PORT, os.path.abspath(DOSAR)), flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
