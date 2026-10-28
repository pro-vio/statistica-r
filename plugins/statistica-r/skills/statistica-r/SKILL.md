---
name: statistica-r
description: >-
  Verifică în R, local, estimările statistice făcute în Python: reface aceeași estimare pe același tabel, cu
  pachetele de referință din R (fixest pentru OLS cu erori standard grupate, diferențe de discontinuitate,
  regresii cu interacțiuni și praguri placebo), și compară cifră cu cifră cele două fișiere de rezultate.
  Ține R și pachetele la zi singur: la prima apelare după ce a trecut o lună de la ultima actualizare,
  actualizează R (winget) și pachetele înainte de rulare. Folosește-l ori de câte ori o regresie, un test sau
  o estimare dintr-un script Python trebuie verificată independent, ori de câte ori utilizatorul spune
  „rulează și în R", „verifică în R", „fixest", „Rscript", „dă aceleași cifre?", „replicăm în R", „erori
  grupate", „cluster-robust", „vcovCL", sau cere actualizarea lui R ori a pachetelor — chiar dacă nu spune
  „skill". R rulează numai pe calculatorul utilizatorului, niciodată în cloud.
---

# Statistica în R — verificarea estimărilor din Python

Skill-ul are două sarcini. Prima e **verificarea**: o estimare făcută în Python se reface în R, pe exact
același tabel, cu o implementare scrisă de alții, iar cele două rezultate se compară cifră cu cifră. A doua
e **întreținerea**: R și pachetele se actualizează o dată pe lună, fără să le ceară cineva.

## De ce o a doua implementare, și ce dovedește ea

O regresie scrisă de mână în numpy poate greși în locuri care nu se văd în cifră: corecția pentru eșantion
mic a erorilor grupate, coloana de interacțiune pusă în altă ordine, indicele coeficientului citit greșit.
`fixest` e scris de altcineva și folosit de mii de oameni, deci greșelile lui nu sunt ale noastre. Când
amândouă dau aceeași cifră, știm că **codul face ce spune**.

Verificarea nu spune nimic despre design: dacă fereastra e aleasă greșit sau dacă populația e alta decât
trebuie, R o reface la fel de greșit. Deci în raport se scrie „implementarea Python și cea din R dau
aceleași cifre", nu „rezultatele sunt validate". Regula e cea din `reguli-de-lucru.md`: confirmarea cere o
sursă independentă de lucrul confirmat, iar aici independent e numai codul.

## R rulează numai local

R e instalat pe calculatorul utilizatorului (`C:/Program Files/R/R-<versiune>`), nu e pe PATH. Toate
rulările trec prin `scripts/r_local.py`, care găsește cea mai nouă versiune instalată. Nu se folosesc
servicii în cloud, webR sau containere: datele pe care se estimează sunt adesea date personale și nu
pleacă de pe calculator.

Pachetele stau pe D:, în `D:/R-lib/<major.minor>`, nu în biblioteca lui R de pe C:. Un dosar pe versiunea
minoră există fiindcă un pachet compilat pentru R 4.6 nu se încarcă în R 4.7: după o actualizare majoră
dosarul nou e gol, iar `r_local.py` instalează în el lista din `pachete.txt`.

## Actualizarea lunară

La fiecare `ruleaza`, `r_local.py` citește data ultimei actualizări din `D:/R-lib/actualizare.json`. Dacă
a trecut o lună calendaristică de atunci, sau fișierul lipsește, actualizează mai întâi:

1. R însuși, cu `winget upgrade --id RProject.R`;
2. pachetele: instalează ce lipsește din `pachete.txt`, apoi `update.packages` pe toată biblioteca.

Data se scrie numai dacă amândouă au reușit, ca o actualizare căzută să se reia la apelarea următoare. O
actualizare a lui R poate cere confirmarea de administrator a Windows; utilizatorul e de față când se
rulează, deci se spune înainte că poate apărea fereastra.

```
python ~/.claude/skills/statistica-r/scripts/r_local.py stare
python ~/.claude/skills/statistica-r/scripts/r_local.py actualizeaza [--forteaza]
python ~/.claude/skills/statistica-r/scripts/r_local.py ruleaza <script.R> [argumente]
```

Un pachet nou se adaugă în `pachete.txt`, nu cu `install.packages` dintr-un script de proiect: altfel
actualizarea lunară nu-l vede, iar biblioteca de după o actualizare majoră nu-l mai are.

## Fluxul verificării

1. **Python exportă tabelul pe care estimează**, cu o opțiune adăugată scriptului care estimează (de
   exemplu `--export-r <dosar>`), nu cu un script separat care reface încărcarea: două încărcări ar putea
   diverge tăcut, iar atunci R ar verifica alt tabel. Exportul are două fișiere:
   - tabelul, rând pe observație, doar coloanele care intră în estimare;
   - designul, ca JSON: constantele scriptului (praguri, ferestre, grupuri, liste de excluderi).

   Dosarul stă în afara repo-ului, pe D:. Identificatorii de persoană se scriu ca numere de ordine, dacă
   intră numai în gruparea erorilor: R n-are nevoie de altceva, iar fișierul nu mai poartă identitatea.
2. **Scriptul R stă în proiect**, lângă scriptul Python pe care îl verifică (`<proiect>/r/`), fiindcă e
   specific estimării lui. Citește constantele din fișierul de design, nu le rescrie: o constantă scrisă de
   două ori e o a doua sursă, iar cele două pot diverge. Ce se *calculează* din constante — ferestre, date
   placebo, subeșantioane — se recalculează în R, ca să se verifice și calculul acela.
3. **Scriptul R scrie un JSON cu aceeași structură** ca rezultatele din Python: aceleași chei, aceleași
   unități, aceeași rotunjire. Ce adaugă numai R (versiunile, note) stă sub chei care încep cu `R: `.
4. **Comparația**: `python scripts/compara.py python.json r.json --iesire raport.md`. Raportul spune câte
   cifre s-au comparat, câte depășesc toleranța, cea mai mare diferență, și ce chei lipsesc de o parte sau
   de alta. Toleranța implicită, 0,01, e cea a rotunjirii la două zecimale; dacă rezultatele nu sunt
   rotunjite, se dă `--toleranta` mai mică.

## Echivalențele care contează

Detaliile, cu formulele: `references/echivalente-python-r.md`. Pe scurt, ce trebuie potrivit ca cifrele
să iasă la fel:

- **Erorile grupate.** Corecția uzuală (CR1, cea din Stata) e `G/(G−1) · (n−1)/(n−k)`. În `fixest`
  e implicită la `vcov = ~id`, fără efecte fixe; în `sandwich`, `vcovCL(..., type = "HC1")`.
- **Rezultatul constant.** Când variabila dependentă nu variază în eșantion, numpy dă coeficient 0 și
  eroare 0, iar `fixest` refuză estimarea. Saltul e 0 prin definiție; scriptul R îl scrie 0 și pune cazul
  într-o listă separată, ca să se vadă că n-a fost estimat.
- **Interacțiunile** se construiesc ca coloane explicite (`dG = d*G`), nu cu `*` în formulă: numele
  coeficienților rămân previzibile, iar coeficientul citit e chiar cel din Python.

## Resurse

- `scripts/r_local.py` — găsește R, ține biblioteca pe D:, actualizează lunar, rulează scripturi R.
- `scripts/compara.py` — compară două JSON-uri de rezultate, cifră cu cifră.
- `pachete.txt` — pachetele pe care le instalează și le actualizează `r_local.py`.
- `references/echivalente-python-r.md` — corespondențele dintre estimatorii scriși în numpy și cei din R.
