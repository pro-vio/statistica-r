#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compară două fișiere JSON de rezultate, cel din Python și cel din R, cifră cu cifră.

    python compara.py python.json r.json [--toleranta 0.01] [--iesire raport.md]

Ambele fișiere se aplatizează pe căi („prag 1 / grupul A / dreapta / salt”). Pentru fiecare cale
cu număr în amândouă se calculează diferența absolută. Raportul spune câte căi s-au comparat, câte depășesc
toleranța, care e cea mai mare diferență și ce căi lipsesc de o parte sau de alta. Toleranța implicită e cea
a rotunjirii: dacă amândouă scriu cifra rotunjită la 2 zecimale, o diferență de 0,01 poate veni numai din
rotunjire.
"""
import argparse
import io
import json
import math
import sys


def aplatizeaza(x, cale=()):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from aplatizeaza(v, cale + (str(k),))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from aplatizeaza(v, cale + (str(i),))
    else:
        yield " / ".join(cale), x


def numar(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not (isinstance(v, float) and math.isnan(v))


def lipsa(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("python")
    ap.add_argument("r")
    ap.add_argument("--toleranta", type=float, default=0.01)
    ap.add_argument("--iesire")
    ap.add_argument("--ignora-prefix", default="R: ", help="cheile de prim nivel pe care le adaugă numai R (versiuni, note)")
    a = ap.parse_args()
    P = dict(aplatizeaza(json.load(io.open(a.python, encoding="utf-8"))))
    R = {c: v for c, v in aplatizeaza(json.load(io.open(a.r, encoding="utf-8"))) if not c.startswith(a.ignora_prefix)}
    comune = sorted(set(P) & set(R))
    dif, nenumerice = [], []
    for c in comune:
        if numar(P[c]) and numar(R[c]):
            dif.append((abs(P[c] - R[c]), c, P[c], R[c]))
        elif P[c] != R[c] and not (lipsa(P[c]) and lipsa(R[c])):
            nenumerice.append((c, P[c], R[c]))
    peste = [d for d in dif if d[0] > a.toleranta]
    numai_p, numai_r = sorted(set(P) - set(R)), sorted(set(R) - set(P))
    l = ["# Python față de R", "",
         "- căi comparate cu număr în amândouă: %d" % len(dif),
         "- peste toleranța de %g: %d" % (a.toleranta, len(peste)),
         "- cea mai mare diferență: %s" % ("%g, la %s" % (max(dif)[0], max(dif)[1]) if dif else "—"),
         "- valori nenumerice diferite: %d" % len(nenumerice),
         "- căi numai în Python: %d; numai în R: %d" % (len(numai_p), len(numai_r)), ""]
    if peste:
        l += ["## Peste toleranță", "", "| cale | Python | R | diferență |", "|---|---|---|---|"]
        l += ["| %s | %s | %s | %g |" % (c, p, r, d) for d, c, p, r in sorted(peste, reverse=True)]
        l.append("")
    for titlu, lista in (("Numai în Python", numai_p), ("Numai în R", numai_r)):
        if lista:
            l += ["## " + titlu, ""] + ["- " + c for c in lista[:50]]
            if len(lista) > 50:
                l.append("- … încă %d" % (len(lista) - 50))
            l.append("")
    if nenumerice:
        l += ["## Valori nenumerice diferite", ""] + ["- %s: %r față de %r" % x for x in nenumerice[:50]] + [""]
    text = "\n".join(l)
    if a.iesire:
        io.open(a.iesire, "w", encoding="utf-8").write(text)
    print(text)
    raise SystemExit(1 if (peste or numai_p or numai_r or nenumerice) else 0)


if __name__ == "__main__":
    main()
