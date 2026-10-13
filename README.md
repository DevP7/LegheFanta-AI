# LegheFanta-AI

Strumenti per le leghe di [Leghe Fantacalcio](https://leghe.fantacalcio.it): legge le rose di tutte
le squadre e, nei prossimi passi, propone formazione (11 + panchina) e scambi realistici.

## Import delle rose

Leghe Fantacalcio non ha un'API pubblica. Il sito usa un'API JSON privata
(`apileague.fantacalcio.it`) con un token per ogni lega, che si ottiene facendo login.
Endpoint e campi sono ricavati dal frontend del sito e possono cambiare senza preavviso.

```bash
pip install -e '.[login]'      # playwright serve solo per il login automatico
playwright install chromium     # non serve nelle sessioni cloud di Claude

export LEGHE_USERNAME=...       # meglio come segreto dell'ambiente, mai nel codice
export LEGHE_PASSWORD=...

python -m leghefanta leghe              # elenca le leghe dell'account
python -m leghefanta rose               # tutte le leghe -> data/<alias>/rose.json
python -m leghefanta rose --lega ALIAS  # una lega sola
```

Al primo uso viene fatto il login e i token (validi circa un anno) sono salvati in
`.leghe_tokens.json`, escluso da git.

Se il login automatico non funziona (captcha, pagina cambiata):
- `python -m leghefanta login --headed` apre il browser e mostra cosa succede;
- oppure copia dal browser, dopo il login, il valore di Local Storage
  `LEAGUES2024_LOCAL` (DevTools > Application > Local Storage > leghe.fantacalcio.it)
  nella variabile `LEGHE_LOCALSTORAGE`.

### Cosa contiene `rose.json`

Per ogni squadra: nome, allenatore, crediti residui e spesi, e i giocatori con ruolo
Classic e Mantra, squadra di Serie A, quotazione, FVM e costo d'acquisto. La squadra
dell'account ha `"mia": true`.

### Rete

Servono i domini `leghe.fantacalcio.it` e `apileague.fantacalcio.it` (più `www.fantacalcio.it`
per le statistiche nei prossimi passi).

## Test

```bash
python -m unittest
```
