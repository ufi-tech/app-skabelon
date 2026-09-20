# Regler for dig, der skriver kode her

Du arbejder i en kundes workspace. Alt du skriver, går gennem en vagt, og alt der skal
udgives, går gennem en gate. Vagten er ikke en modstander: den fanger de ting, der er
dyre at opdage bagefter, og den siger hvorfor med et link til guiden.

Denne fil er kort med vilje. Den siger, hvad der aldrig må brydes, og hvor fælderne
ligger. Uddybningen står i README.md og i guiden:
<https://mcp.ufi-tech.dk/retningslinjer/guide>

## Det der aldrig må brydes

1. **Ingen hemmeligheder i koden.** Ingen nøgler, adgangskoder eller tokens, heller ikke
   som reserveværdi bag `os.environ.get`. De ligger i miljøfilen på serveren og læses
   med `os.environ`. Det gælder også en prøve: skriv aldrig et kodeord som en streng
   lige efter ordet `adgangskode`.
2. **Ingen nøgle i `web/`.** Alt i frontenden kan læses af enhver besøgende. Skal der
   kaldes en tjeneste med en nøgle, sker det fra `api/`.
3. **Alt der ændrer noget, kræver login.** Et `@router.post`, `put`, `patch` eller
   `delete` skal have `Depends(kraev_bruger)` eller en anden afhængighed i signaturen.
   Et `GET` må stå åbent, hvis indholdet er offentligt, og kun da.
4. **SQL med parametre.** Aldrig en f-streng eller en sammensat streng ind i `execute`.
   Brug SQLAlchemy eller `?`-pladsholdere.
5. **Migrationer er expand/contract.** Tilføj i denne udgivelse, fjern i den næste.
   `drop_column`, `drop_table`, `rename_column` og `alter_column(..., nullable=False)`
   stopper både gaten og udgivelsen. Se README.md for de to skridt.
6. **Ingen `eval`, `exec`, `pickle` eller `yaml.load` uden `SafeLoader`.** Kør aldrig en
   kommando gennem en skal, og slå aldrig certifikat-tjekket fra i et http-kald. Der
   findes altid en anden vej, også når inddata ser sikre ud i dag.
7. **Ingen åben CORS.** Browseren møder kun ét domæne. Skal noget kaldes udefra, så spørg
   ufi-tech først.
8. **Ingen eksterne scripts, stilark, fonte eller billeder.** De kan ikke nås gennem
   proxyen i workspacet, og de fortæller andre, hvem der besøger sitet. Læg filen i
   `web/public/` i stedet.
9. **Rør ikke `Dockerfile*`, `docker-compose*`, `.github/` eller `Makefile`.** De hører
   til platformen. Skriv hvad du har brug for, så retter ufi-tech dem.
10. **Alt pinnes.** `package-lock.json` og `uv.lock` committes. Ingen `"latest"` og
    ingen `"*"` i `package.json`.

## Sådan tilføjer du

- **En side:** en post i `_SIDER` i `api/indhold.py`. Indholdet er statisk i version 1.
- **En bloktype:** navnet i `BLOKTYPER` i `api/indhold.py`, typen i `web/src/typer.ts`,
  komponenten i `web/src/blokke/<type>.tsx`, valget i `web/src/blokke/index.tsx` og en
  prøve i `web/src/blokke/blokke.test.tsx`. Komponentfilen skal hedde det samme som
  typen; en prøve holder øje med det.
- **En model:** tabellen i `api/modeller.py`, derefter
  `uv run alembic revision --autogenerate -m "..."`, og læs migrationen igennem.
- **Et endpoint:** i `api/auth.py` eller `api/indhold.py`, eller i en ny fil der får sin
  egen `APIRouter` og bliver hængt op i `api/main.py`. Altid med en afhængighed, når det
  ændrer noget.

## Inden du siger, du er færdig

```bash
cd web && npm run build && npm run test && npm run lint
cd api && uv run pytest -q && uv run ruff check . && uv run ruff format --check .
```

Alle fire skal være grønne, og træet skal være committet. Gaten hænger på et commit: er
der ændringer, der ikke er committet, bliver den rød, uden at resten bliver målt.

## Fælder, vi allerede er faldet i

- **Et kodeord i en prøve.** `{"adgangskode": "sommer2026"}` er et blokerende fund, også
  i en prøve. Læg værdien i en konstant og send konstanten med.
- **`os.environ.get("API_KEY", "noget")`.** Reserveværdien er lige så meget en
  hemmelighed som den rigtige. Lad den være væk, og fejl tydeligt i stedet.
- **En migration med `nullable=False` på en ny kolonne.** Den fejler på rækkerne, der
  allerede findes. Tilføj kolonnen med en standardværdi, fyld den, og stram den i en
  senere udgivelse.
- **En port bundet bredt.** Porte bindes til `127.0.0.1`. Trafikken kommer ind gennem
  tunnelen og ingen andre steder fra.
- **Et billede fra et fremmed domæne.** Det bliver ikke hentet i workspacet, og du får
  ikke en fejl, du kan se. Læg filen i `web/public/`.
- **`npm install` i stedet for `npm ci`.** `install` retter i `package-lock.json`, og så
  er træet snavset, når gaten kigger.
