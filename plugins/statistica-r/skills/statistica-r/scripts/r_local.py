#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rulează R local și îl ține la zi: R însuși (winget) și pachetele, o dată pe lună, la prima apelare
după ce a trecut o lună de la ultima actualizare.

    python r_local.py ruleaza <script.R> [argumente...]   # verifică luna, apoi rulează scriptul
    python r_local.py actualizeaza [--forteaza]           # numai actualizarea
    python r_local.py stare                               # ce R, ce bibliotecă, când s-a actualizat

R nu e pe PATH: se caută cea mai nouă versiune din C:/Program Files/R. Pachetele stau pe D:, nu pe C:,
într-un dosar pe versiunea minoră a lui R (D:/R-lib/4.6), fiindcă pachetele compilate pentru 4.6 nu merg
pe 4.7. Data ultimei actualizări stă în D:/R-lib/actualizare.json și se scrie numai dacă actualizarea a
reușit, ca o actualizare căzută să se reia la apelarea următoare.
"""
import datetime
import glob
import json
import os
import re
import subprocess
import sys

RADACINA_R = "C:/Program Files/R"
BIBLIOTECI = os.environ.get("STATISTICA_R_LIB", "D:/R-lib")
STAMPILA = os.path.join(BIBLIOTECI, "actualizare.json")
PACHETE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pachete.txt")
CRAN = "https://cloud.r-project.org"


def versiune(cale):
    m = re.search(r"R-(\d+)\.(\d+)\.(\d+)", cale)
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def rscript():
    instalate = sorted(glob.glob(RADACINA_R + "/R-*/bin/Rscript.exe"), key=versiune)
    if not instalate:
        sys.exit("R nu e instalat în %s" % RADACINA_R)
    return instalate[-1]


def biblioteca(rs):
    v = versiune(rs)
    lib = "%s/%d.%d" % (BIBLIOTECI, v[0], v[1])
    os.makedirs(lib, exist_ok=True)
    return lib


def mediu(lib):
    e = dict(os.environ)
    e["R_LIBS_USER"] = lib
    e["R_LIBS"] = lib
    e["STATISTICA_R_SKILL"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
    return e


def o_luna_dupa(d):
    an, luna = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    for zi in (d.day, 30, 29, 28):
        try:
            return datetime.date(an, luna, zi)
        except ValueError:
            pass


def citeste_stampila():
    try:
        with open(STAMPILA, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def e_scadenta():
    s = citeste_stampila()
    if not s:
        return True
    return datetime.date.today() >= o_luna_dupa(datetime.date.fromisoformat(s["data"]))


def lipsesc(rs):
    """Un pachet adăugat în pachete.txt între două actualizări se instalează la prima rulare, nu peste o lună."""
    lib = biblioteca(rs)
    cerute = {p.strip() for p in open(PACHETE, encoding="utf-8") if p.strip() and not p.startswith("#")}
    return bool(cerute - set(os.listdir(lib)))


def actualizeaza():
    print("[statistica-r] actualizez R (winget)…", flush=True)
    w = subprocess.run(["winget", "upgrade", "--id", "RProject.R", "-e", "--silent",
                        "--accept-source-agreements", "--accept-package-agreements"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    iesire = (w.stdout or "") + (w.stderr or "")
    # winget întoarce cod nenul și când nu are ce actualiza; ce contează e dacă R e instalat după
    print("[statistica-r] winget:", " ".join(iesire.split()[-12:]), flush=True)
    rs = rscript()
    lib = biblioteca(rs)
    pachete = [p.strip() for p in open(PACHETE, encoding="utf-8") if p.strip() and not p.startswith("#")]
    cod = ("lib <- '%s'; options(repos = c(CRAN = '%s'));"
           "lipsa <- setdiff(c(%s), rownames(installed.packages(lib.loc = lib)));"
           "if (length(lipsa)) install.packages(lipsa, lib = lib, quiet = TRUE);"
           "update.packages(lib.loc = lib, ask = FALSE, checkBuilt = TRUE, quiet = TRUE);"
           "lipsa <- setdiff(c(%s), rownames(installed.packages(lib.loc = lib)));"
           "if (length(lipsa)) stop('nu s-au instalat: ', paste(lipsa, collapse = ', '));"
           "cat(R.version.string, '\\n')") % (lib, CRAN, ", ".join("'%s'" % p for p in pachete),
                                                ", ".join("'%s'" % p for p in pachete))
    print("[statistica-r] actualizez pachetele în %s…" % lib, flush=True)
    r = subprocess.run([rs, "-e", cod], env=mediu(lib))
    if r.returncode != 0:
        sys.exit("[statistica-r] actualizarea pachetelor a căzut; data n-a fost scrisă, se reia la apelarea următoare")
    with open(STAMPILA, "w", encoding="utf-8") as f:
        json.dump({"data": datetime.date.today().isoformat(), "r": ".".join(map(str, versiune(rs))),
                   "biblioteca": lib}, f, ensure_ascii=False)
    print("[statistica-r] actualizat:", STAMPILA, flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2 or sys.argv[1] not in ("ruleaza", "actualizeaza", "stare"):
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "stare":
        rs = rscript()
        print(json.dumps({"rscript": rs, "biblioteca": biblioteca(rs), "ultima actualizare": citeste_stampila(),
                          "scadentă": e_scadenta()}, ensure_ascii=False, indent=1))
        return
    if cmd == "actualizeaza":
        if "--forteaza" in sys.argv or e_scadenta():
            actualizeaza()
        else:
            print("[statistica-r] la zi:", citeste_stampila())
        return
    if len(sys.argv) < 3:
        sys.exit("lipsește scriptul R")
    rs = rscript()
    if e_scadenta() or lipsesc(rs):
        actualizeaza()
        rs = rscript()
    sys.exit(subprocess.run([rs, "--encoding=UTF-8"] + sys.argv[2:], env=mediu(biblioteca(rs))).returncode)


if __name__ == "__main__":
    main()
