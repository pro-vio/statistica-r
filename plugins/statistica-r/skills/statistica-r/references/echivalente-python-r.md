# Corespondențe între estimatorii scriși în numpy și cei din R

## OLS cu erori standard grupate (CR1)

Python, scris de mână:

```python
XtX_inv = np.linalg.pinv(X.T @ X)
b = XtX_inv @ (X.T @ y)
u = y - X @ b
S = suma, pe fiecare grup g, a lui X_g' u_g          # G × k
c = G/(G-1) * (n-1)/(n-k)
V = c * XtX_inv @ (S.T @ S) @ XtX_inv
```

R:

```r
m <- fixest::feols(y ~ x1 + x2, data, vcov = ~id)   # corecția de mai sus e implicită fără efecte fixe
# sau
m <- lm(y ~ x1 + x2, data); sandwich::vcovCL(m, cluster = ~id, type = "HC1")
```

În `fixest` corecția se numește `ssc(K.adj = TRUE, G.adj = TRUE)` în versiunile noi și
`ssc(adj = TRUE, cluster.adj = TRUE)` în cele vechi; implicitul e același. Cu efecte fixe, `fixest` scade
din k numai efectele care nu sunt cuprinse în grupare (`K.fixef = "nonnested"`), deci cifra poate diferi
de o implementare care le numără pe toate.

`np.linalg.pinv` și `solve` dau același rezultat când matricea are rang întreg. Când nu are, numpy dă o
soluție, iar `fixest` scoate coloanele coliniare și o spune; diferența apare în raport ca o cheie care
lipsește sau ca un coeficient diferit, și se aduce la autor, fiindcă înseamnă că estimarea din Python nu
era identificată.

## Rezultat care nu variază

Dacă y e constant în eșantion, numpy dă b = (constantă, 0, …) și erori 0. `feols` oprește estimarea cu
„The dependent variable is a constant". Scriptul R scrie 0 și 0 și pune cazul într-o listă separată
(`R: estimări cu rezultat constant`), ca să nu treacă drept estimare.

## Discontinuitatea, în cele două forme

Cu d = luna minus luna pragului și D = 1 după prag:

| forma | formula | coeficientul saltului |
|---|---|---|
| media pe fiecare parte | `y ~ D` | `D` |
| dreapta pe fiecare parte | `y ~ d + D + dD` | `D` |

Diferența de discontinuitate între un grup (G = 1) și grupul de comparație (G = 0), pe aceleași luni:

| forma | formula | coeficientul diferenței |
|---|---|---|
| media | `y ~ D + G + DG` | `DG` |
| dreapta | `y ~ d + D + dD + G + dG + DG + dDG` | `DG` |

Ordinea coloanelor nu schimbă coeficienții, deci matricea din Python poate avea altă ordine; contează numai
ca setul de coloane să fie același.
