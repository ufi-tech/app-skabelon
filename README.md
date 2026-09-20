# site-basis

Skabelonen en Byg selv-kunde starter med. React 18 og Vite i `web/`, FastAPI og SQLite i
`api/`, login med session i en cookie, migrationer der kan rulles tilbage, og en gate der
kører de samme trin som ufi-tech's workspace-agent.

Alt i repoet er tænkt som noget, der skal rettes i. Det er meningen, at du bygger videre.

## Sådan ser det ud

```
app-skabelon/
  skabelon.yaml            navn, version, gate-trin og egress-domæner
  docker-compose.yml       basis til udvikling, udstiller ingen port
  docker-compose.dev.yml   udvikling: 127.0.0.1:8080, lægges oven på basis
  docker-compose.prod.yml  produktion, STÅR ALENE: 127.0.0.1:8081, /srv/prod-data
  Dockerfile.api           python 3.12, pinnet, kører som uid 10001
  Dockerfile.web           node bygger, nginx serverer, kører som uid 101
  api/
    main.py                FastAPI-appen: middleware og routere
    auth.py                login, log ud, hvem er jeg
    indhold.py             siderne (statiske i version 1)
    indstillinger.py       alt der læses fra miljøet
    database.py            forbindelsen til SQLite, ét sted
    modeller.py            tabellerne
    brugere.py             opret en bruger fra kommandolinjen
    migrationer/           alembic
    tests/                 prøver af api'et
  web/
    src/blokke/            én komponent pr. bloktype
    src/sider/             siderne i frontenden
    src/api.ts             alle kald til api'et samlet ét sted
  tests/                   prøver af compose, dockerfiler og skabelonen selv
  .github/workflows/gate.yml
```

## Kom i gang

```bash
cp .env.example .env          # ret APP_UID og APP_GID til din egen bruger
docker compose up --build     # siden ligger på http://127.0.0.1:8080
```

Første bruger:

```bash
docker compose run --rm api alembic upgrade head
START_ADGANGSKODE='vælg-noget-langt-her' docker compose run --rm api python brugere.py dig@eksempel.dk "Dit navn"
```

Uden Docker, hvis du vil arbejde hurtigt på én del ad gangen:

```bash
cd api && uv sync && uv run alembic upgrade head && uv run uvicorn main:app --port 8000
cd web && npm ci && npm run dev        # 127.0.0.1:5173, sender /api videre til 8000
```

## Gaten

De samme trin som agenten kører, før noget kan udgives:

```bash
cd web && npm ci && npm run build && npm run test && npm run lint
cd api && uv sync --frozen && uv run pytest -q && uv run ruff check . && uv run ruff format --check .
```

Gaten hænger på et commit. Er der ændringer, der ikke er committet, bliver den rød, uden
at resten overhovedet bliver målt.

## Sådan tilføjer du noget

### En side

1. Tilføj en post i `_SIDER` i `api/indhold.py` med `sti`, `titel` og `blokke`.
2. Kør `cd api && uv run pytest -q`. Prøven holder øje med, at formen passer.

### En bloktype

1. Skriv typen i `BLOKTYPER` i `api/indhold.py`.
2. Lav typen i `web/src/typer.ts` og tilføj den til `Blok`.
3. Lav komponenten i `web/src/blokke/<type>.tsx` og vælg den i `web/src/blokke/index.tsx`.
4. Skriv en prøve pr. bloktype i `web/src/blokke/blokke.test.tsx`.

Komponenten skal hedde det samme som typen. Prøven `test_hver_bloktype_har_en_komponent`
fejler ellers, og den fejler med vilje: en bloktype uden komponent bliver usynlig uden en
fejlmeddelelse nogen ser.

### En model og en migration

1. Tilføj tabellen eller kolonnen i `api/modeller.py`.
2. `cd api && uv run alembic revision --autogenerate -m "hvad du tilføjer"`.
3. Læs migrationen igennem. Den skal kun tilføje.
4. `uv run alembic upgrade head`, og kør prøverne.

**Migrationer skal være expand/contract.** Tilføj i én udgivelse, fjern i den næste.
Grunden er ikke pænhed: ruller vi koden tilbage efter en migration, der har fjernet en
kolonne, møder den gamle kode et skema, den ikke kender, og så virker hverken den nye
eller den gamle udgave. Derfor stopper både gaten og udgivelsen på `drop_column`,
`drop_table`, `rename_column` og `alter_column(..., nullable=False)`.

Skal en kolonne væk, tager det to udgivelser:

1. Hold op med at bruge den i koden. Udgiv.
2. Fjern den i en migration i en senere udgivelse, når ingen kode læser den.

### Et endpoint

```python
@router.post("/api/noget")
def noget(krop: NogetKrop, bruger: Bruger = Depends(kraev_bruger)) -> dict[str, object]: ...
```

Alt der ændrer noget, skal have en afhængighed, der kræver login. Er data offentlige,
kan et `GET` stå uden, men så skal det være et valg og ikke en forglemmelse.

## Det man aldrig gør

- **Ingen hemmeligheder i repoet.** Ingen nøgler, ingen adgangskoder, ingen tokens,
  heller ikke som reserveværdi i `os.environ.get("NOGET", "hemmeligt")`. De ligger i
  miljøfilen på serveren.
- **Ingen nøgle i `web/`.** Alt i frontenden kan læses af enhver besøgende. Skal der
  kaldes en tjeneste med en nøgle, sker det fra `api/`.
- **Ingen SQL sat sammen af tekst.** Brug parametre eller SQLAlchemy.
- **Ingen `eval`, `exec` eller `pickle`, og ingen kommando gennem en skal.**
- **Slå aldrig certifikat-tjekket fra** i et http-kald. Et slukket certifikat-tjek er en
  krypteret forbindelse, uden at nogen ved, hvem der er i den anden ende.
- **Ingen åben CORS.** Browseren møder kun ét domæne: nginx serverer frontenden og
  sender `/api` videre til api'et.
- **Ingen eksterne scripts, stilark eller fonte.** De kan ikke nås gennem proxyen i
  workspacet, og de fortæller andre, hvem der besøger sitet.
- **Ingen ændringer i `Dockerfile*`, `docker-compose*` eller `.github/`.** De filer hører
  til platformen. Skriv hvad du har brug for, så retter ufi-tech dem.
- **Ingen migration der fjerner noget** uden at der er gået en udgivelse først.

Hele listen med begrundelser står i guiden:
<https://mcp.ufi-tech.dk/retningslinjer/guide>

## Hvordan det hænger sammen i drift

| | Udvikling | Produktion |
| --- | --- | --- |
| Compose-projekt | `docker-compose.yml` plus `docker-compose.dev.yml` | `docker-compose.prod.yml` alene |
| Adresse | `127.0.0.1:8080` | `127.0.0.1:8081` |
| Data | `./data` i repoet | `/srv/prod-data` |
| Genstart | nej | `unless-stopped` |
| Sundhedstjek | `/healthz` | `/healthz`, pollet af udgivelsen i op til 60 sekunder |

Docker compose fletter felt for felt med hver sin regel: `ports` og `volumes` lægges
sammen, og en arvet liste kan kun erstattes med YAML-taggene `!override` og `!reset`, som
agentens eget compose-værn afviser. Derfor **står produktionsfilen alene**. Den gentager
det meste af basis-filen, og det er med vilje: en produktion skal kunne læses i sin
helhed i én fil. Prøven `test_produktionsfilen_kan_staa_alene` holder øje med, at den
faktisk har alt, og `test_de_to_miljoeer_deler_ingen_vaertsport` med, at preview og
produktion kan køre samtidig.

`docker-compose.yml` udstiller stadig ingen port. Ellers ville et ældre repo uden
`docker-compose.dev.yml` ikke kunne starte preview på den rigtige port.

`/srv/prod-data` ejes af `10001:10001` med rettighederne 750, for det er den bruger,
api-billedet kører som. Den er IKKE ejet af den bruger kundens AI kører som, så
produktionen ikke kan slettes af et uheld i workspacet.

### Appens egne hemmeligheder

Skal appen bruge en rigtig ekstern nøgle (mail, betaling), ligger den i
`/srv/prod-env/app.env` på VM'en. Filen er `root:ws` med rettighederne 640: appen kan
læse den, og kundens AI kan ikke ændre den. En operatør fra ufi-tech skriver den; der er
ingen vej til den fra et værktøj.

`/srv/prod-build` er et frisk git-worktree ved hver udgivelse, så hverken en `.env` i
projektmappen eller en fil uden for git overlever en udgivelse. Derfor ligger filen uden
for repoet.

Sessionshemmeligheden læses fra `SESSION_HEMMELIGHED`, hvis den er sat. Ellers laver appen
selv en og gemmer den i datamappen med rettighederne 600, så alle ikke bliver logget ud
ved hver genstart.

## Versioner

Alt er pinnet. `web/package-lock.json` og `api/uv.lock` er committet, og `api/requirements.txt`
er lavet af uv med en sha256 pr. pakke, så `pip install --require-hashes` i byggetrinnet
stopper, hvis en pakke er skiftet ud på vejen.

Basebillederne er pinnet på et konkret tag. Vil du længere ned, kan de pinnes på et
digest (`python:3.12-slim-bookworm@sha256:...`), og så skal de opdateres med vilje.
