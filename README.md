# statistica-r

A Claude Code skill that checks statistical estimates made in Python by redoing them in R, locally, on the same
table (`fixest`, clustered standard errors CR1), and comparing the two result files number by number. It also keeps
R and its packages up to date by itself, at the first call after a month has passed.

## Install

```
/plugin marketplace add pro-vio/statistica-r
/plugin install statistica-r@statistica-r
/reload-plugins
```

Requires R installed under `C:/Program Files/R` (Windows, updated with winget). The workflow is in
`plugins/statistica-r/skills/statistica-r/SKILL.md`; the documentation is in Romanian.

This repository is a published copy, updated from time to time from a private source; changes made here directly
are overwritten.
