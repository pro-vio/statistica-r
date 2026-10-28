# Rezultatele unei rulări R, adunate pentru panoul „Rezultate” din previzualizare (scripts/previzualizare.py).
# Se încarcă din scriptul de proiect cu source(file.path(Sys.getenv("STATISTICA_R_SKILL"), "scripts", "iesire.R")),
# variabilă pe care o pune r_local.py. Fiecare element are o secțiune (nodul din arborele din stânga) și un titlu.
#   iesire_model(m, sectiune, titlu)   — tabelul coeficienților unui model fixest, cu N, grupuri, eroare, R²
#   iesire_nota(sectiune, titlu, text) — un rând de text, de exemplu o estimare care n-a putut rula
#   iesire_tabel(df, sectiune, titlu)  — un data.frame oarecare
#   iesire_scrie(cale)                 — scrie totul ca JSON
.iesire <- new.env()
.iesire$el <- list()

.adauga <- function(x) .iesire$el[[length(.iesire$el) + 1]] <- x

iesire_model <- function(m, sectiune, titlu) {
  ct <- fixest::coeftable(m)
  vc <- attr(ct, "vcov_type")
  g <- tryCatch(fixest::fitstat(m, "g")[[1]], error = function(e) NA)
  .adauga(list(tip = "model", sectiune = sectiune, titlu = titlu,
               formula = paste(deparse(stats::formula(m)), collapse = " "),
               n = stats::nobs(m), grupuri = unname(g), eroare = if (is.null(vc)) "" else vc,
               r2 = unname(fixest::r2(m, "r2")),
               coloane = c("Coeficient", "Eroare std.", "t", "p"),
               randuri = lapply(seq_len(nrow(ct)), function(i)
                 list(nume = rownames(ct)[i], valori = unname(as.numeric(ct[i, 1:4]))))))
}

iesire_nota <- function(sectiune, titlu, text) .adauga(list(tip = "nota", sectiune = sectiune, titlu = titlu, text = text))

iesire_tabel <- function(df, sectiune, titlu) {
  .adauga(list(tip = "tabel", sectiune = sectiune, titlu = titlu, coloane = names(df),
               randuri = lapply(seq_len(nrow(df)), function(i) unname(as.list(df[i, , drop = TRUE])))))
}

iesire_scrie <- function(cale) {
  writeLines(jsonlite::toJSON(list(creat = format(Sys.time(), "%Y-%m-%d %H:%M"), r = R.version.string,
                                   elemente = .iesire$el),
                              auto_unbox = TRUE, digits = NA, na = "null", null = "null"), cale, useBytes = TRUE)
}
