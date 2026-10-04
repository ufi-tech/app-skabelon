# Platform-motoren: én kerne i kode, hver kunde som data

**Status:** forslag til beslutning · **Dato:** 2026-10-05 · **Første kunde:** OneOps (Plinthcode sag 16)
**Gælder:** app-skabelon (som motoren vokser ud af), ufi-tech/oneops og de næste Byg selv-kunder

Planen er intern for ufi-tech. Den ligger her og ikke i kundens repo, fordi den handler om
ejerskab, licens og genbrug på tværs af kunder. `docs/plans/` er udeladt af skabelonens
tarball med `.gitattributes` (`export-ignore`), så den følger ikke med ud til et workspace.

## 1. Mål

Vi vil kunne stille et komplet system op til en ny kunde hurtigt og stabilt, uden at kopiere
og rette kode for hver kunde. Alt, der varierer fra kunde til kunde, styres fra databasen:
skærme, menu, roller og rettigheder, felter, design, tekster og SEO. Koden er den samme for
alle og bliver bedre for alle, hver gang vi retter den.

Tommelfingerregel for hele planen:

> **Det, der varierer mellem kunder, er data. Regler, der gælder for alle, er kode.**

## 2. Grundlag: optælling af OneOps' Lovable-forlæg

Optalt 2026-10-05 med et script over alle 12 Lovable-moduler (sidernes lokale imports fulgt
tre niveauer ned) og stikprøver i hånden på 12 af de store og tvivlsomme sider.

| | Skærme | Andel |
| --- | --- | --- |
| Rigtige skærme i alt (163 sidefiler minus 22 trivielle) | 141 | |
| Kan beskrives som data med standardklodser | 125 | 89 % |
| Kræver en særlig klods i kode | 16 | 11 % |

Signaler på tværs af skærmene: formular 87, tabel 77, faner 50, dialog 35, tjekliste med
fremdrift 19, graf 16, rapport/print 13, godkendelse/signatur 11, kalender 9, upload 7.
Resten er nøgletalskort (hele lean-beginnings og strategic-compass).

De 16 særlige: login ×2, brugere, roller og AdminMaster (kerne), Flow Builder-canvas
(8.881 linjer), planlægningstavle med træk og slip (4.523 linjer), feltappen ×2 og stempel,
flow-opsætningens wizard, kort over sites, RCA med fiskeben- og fejltræsdiagram, og tre
infoskærm-editorer, som screen.iocast allerede dækker.

Forbehold: klassificeringen er heuristisk. Lovable kører på mock-data, så forretningslogikken
(11/48 timer, prognoser, udløb) findes ikke i forlæggene og skal skrives som backend-kode
under alle omstændigheder.

## 3. De tre lag

| Lag | Indhold | Hvor | Ens for alle? |
| --- | --- | --- | --- |
| **1. Motor** | Login og passkey, rettighedsmotor, PWA og offline-kø, skærm-motor med klodser, temamotor, offentlige sider og SEO, data-MCP, gateway-klient, revisionslog, opsætningens livscyklus | Kode, versioneret (v0.3 … v1.0) | Ja |
| **2. Pakker** | Særlige klodser og deres backend: Flow Builder, feltapp, planlægningstavle, kort, beregninger og datakilder | Kode, som slås til og fra pr. kunde | Genbruges på tværs |
| **3. Kundens opsætning** | Skærme, menu, roller og rettigheder, ekstra felter, tema, tekster, SEO, aktive moduler og pakker | Databasen | Nej, unik pr. kunde |

Lag 1 og 2 går gennem gaten og vagten som al anden kode. Lag 3 går gennem schemavalidering,
kladde og udgivelse (afsnit 8). Der findes ingen tredje vej: ingen JS, HTML eller SQL gemt i
databasen og kørt derfra.

### Hvorfor ikke Screens widget-model hele vejen

I screen.iocast er en widget HTML, CSS og JS gemt i databasen og kørt i en iframe. Det er
fint til skærme, der kun viser data. Til en hel forretningsapp holder det ikke:

1. Kode i databasen går uden om gaten og vagten. I et Byg selv-workspace kan kundens AI så
   skrive JS, der sender data ud eller ændrer noget, uden at noget bliver gennemset.
2. Feltappen skal skrive og virke offline, med låsning af site, passkey og kamera. Løse
   iframes passer dårligt med service worker og cookie-login.
3. Rettigheder skal håndhæves pr. handling på serveren. Det kan en widget ikke.

Det, vi tager fra Screen, er ideen med et `config_schema`: en klods har en beskrevet
opsætning, som en editor kan vise som felter. Selve klodsen er kode.

## 4. Skærm-motoren

En skærm er et JSON-dokument, der valideres mod et schema, før det gemmes. Det beskriver
hvilke klodser skærmen består af, hvilken datakilde hver klods læser fra, og hvilke
handlinger der er tilladt for hvilke rettigheder.

```json
{
  "sti": "/hr/medarbejdere",
  "titel": "Medarbejdere",
  "rettighed": "hr.medarbejder.se",
  "klodser": [
    {"type": "noegletal", "kilde": "hr.medarbejdere.status",
     "felter": ["aktive", "under_onboarding", "certifikater_udloeber_30d"]},
    {"type": "liste", "kilde": "hr.medarbejdere",
     "kolonner": ["navn", "rolle", "site", "status"],
     "filtre": ["site", "status"], "soegning": true,
     "raekke_handling": {"aabn": "/hr/medarbejdere/{id}"},
     "handlinger": [{"navn": "opret", "rettighed": "hr.medarbejder.opret",
                     "aabner": {"type": "dialog", "formular": "hr.medarbejder.ny"}}]}
  ]
}
```

### Klodserne (12 dækker de 125 skærme)

| Klods | Bruges til |
| --- | --- |
| `liste` | Tabel med filtre, søgning, sortering, sidevisning og række-handlinger |
| `formular` | Felter i sektioner og faner, validering, ekstra felter fra databasen |
| `detalje` | Visning af én post med faner og relaterede lister |
| `dialog` | Opret og rediger oven på en skærm (bruger `formular`) |
| `noegletal` | Kort med tal, tendens og farve efter tærskler |
| `graf` | Linje, søjle, cirkel og område |
| `tjekliste` | Punkter med status, fremdrift og evt. signatur pr. punkt |
| `godkendelse` | Status, godkend og afvis med begrundelse, signatur via link og SMS-kode |
| `kalender` | Måned, uge og periode med begivenheder |
| `dokumenter` | Upload, versioner, arkiv og udløb |
| `rapport` | PDF eller print ud fra en skabelon |
| `log` | Tidslinje over ændringer og aktivitet |

Felttyper i `formular` følger samme idé som `config_schema` i Screen: tekst, tal, dato,
valg, flervalg, ja/nej, fil, signatur, person, site og relation.

### Datakilder

En klods læser aldrig direkte fra en tabel. Den læser fra en navngiven datakilde
(`hr.medarbejdere`), som er backend-kode i motoren eller i en pakke. Datakilden ejer
forespørgslen, rettighedstjekket pr. række og beregningerne. Det svarer til collectors i
Screen. En ny datakilde er kode og går gennem gaten. En ny skærm, der bruger eksisterende
datakilder, er data.

### Særlige klodser (pakker)

| Pakke | Indhold | Kilde til genbrug |
| --- | --- | --- |
| `feltapp` | Låsning af site, offline-kø (IndexedDB-outbox, synk, konfliktregel), start og stop pr. punkt, foto, vagtskifte | Ny; krav i oneops `docs/krav/pwa-spec.md` |
| `flow` | Flow Builder-canvas, flowafvikler, Gantt | Ny; forlæg i Lovable flow-builder |
| `planlaegning` | Ugegitter med træk og slip | Ny; forlæg i time-registrering |
| `kort` | Sites på kort, offline-tiles | Ny |
| `rca` | Fiskeben, 5 hvorfor, fejltræ | Ny; forlæg i hseq |
| `tid` | Stempel, 11/48 timer, saldi, fravær | Logik fra Tider |
| `vejr` | Vejr pr. site med vind i navhøjde og vindstød | iocast-screen `collectors/builtin.py` (weather) |
| `infoskaerm` | Ingen editor i motoren; leverer data til screen.iocast | iocast-screen |

## 5. Rettighedsmotoren

- Roller, moduler og rettigheder er rækker i databasen. Ingen rolle står i koden.
- Hver handling har et navn (`hr.medarbejder.opret`). Datakilder og endpoints tjekker
  navnet på serveren. Skærme skjuler knapper ud fra det samme navn, men det er kun pynt.
- Første opsætning sås fra en kundefil. For OneOps er det `Rettighedsmatrix_V2_0.xlsx`
  (17 roller, en fane pr. modul, plus fanerne for PWA: biometri, location-lås, vagt).
- Administratoren kan derefter rette rettighederne i appen, som Anders har bedt om.
- Rettigheder kan afgrænses til et site (site-administrator ser kun sine sites).

## 6. Design via databasen

- **Design tokens** i en tabel: farver (lys og mørk), typografi, afrunding, tæthed,
  skygger, logo og favicon. Serveren laver `/tema.css` med CSS-variabler ud fra dem og
  sætter cache-headers efter temaets version.
- **Klodserne må kun bruge tokens.** En prøve i motoren fejler, hvis en komponent under
  `web/src/klodser/` indeholder en hex-farve, en `rgb(` eller en fast px-størrelse uden for
  en godkendt liste. Samme idé som vagtens prøver.
- **Fonte, logoer og billeder uploades** og serveres fra eget domæne. Skabelonens regel 8
  forbyder eksterne fonte og billeder.
- **Tekster og sprog** ligger også i databasen (dansk først, engelsk som valg), så en kunde
  kan kalde "Site" for "Lokation" uden en kodeændring.
- Udgangspunkt: Tider har tema pr. kunde, og skabelonen har allerede `BLOKTYPER`.

## 7. Offentlige sider og SEO

- Skabelonens `_SIDER` og `BLOKTYPER` i `api/indhold.py` flyttes fra kode til databasen:
  side, blokke og meta (titel, beskrivelse, delingsbillede, kanonisk URL, `noindex`).
- **Serveren skriver meta-tags ind i HTML'en**, før den sendes. En ren SPA bliver ellers
  dårligt indekseret og deles uden billede.
- `sitemap.xml` og `robots.txt` laves af serveren ud fra databasen.
- Strukturerede data (JSON-LD for organisation og side) som felter på siden.
- For OneOps er det lille, fordi appen ligger bag login. For kunder med en offentlig
  hjemmeside er det afgørende, og det er grunden til, at det hører til motoren.

## 8. Datamodellen

Vi gør **ikke** selve datastrukturen dynamisk. En generisk tabel med JSON for alle poster
giver langsomme rapporter, svær søgning, svære rettigheder pr. række og en dårlig flytning
til Postgres. Det er fælden, hvor man bygger en database inde i databasen.

I stedet:

- **Kernetabeller er rigtige SQLAlchemy-modeller** i motoren og pakkerne: bruger, rolle,
  site, flow, flowpunkt, registrering, vagt, dokument, hændelse osv.
- **Ekstra felter pr. kunde** defineres som data og gemmes i en JSON-kolonne på tabellen
  (`ekstra`). Feltdefinitionerne siger type, validering og om feltet kan søges.
  HR-forlægget har netop sådan en `CustomFieldsAdmin`.
- Felter, der skal kunne søges hurtigt, kan forfremmes til en rigtig kolonne i en senere
  udgivelse (expand/contract).
- Alt er Postgres-portabelt, og SQLite-låsereglerne fra Plinthcode DMS gælder fra dag 1.

## 9. Opsætningens livscyklus

Opsætning i databasen behandles som kode:

1. **Kladde:** en ændring (skærm, felt, tema, rettighed) gemmes som kladde. Kundens AI kan
   oprette kladder via data-MCP'en, men aldrig udgive dem (kladde-grænsen).
2. **Validering:** schemaet tjekker kladden. Henviser den til en datakilde, rettighed eller
   klods, der ikke findes, afvises den med en dansk fejl, der siger hvad der mangler.
3. **Visning:** kladden kan ses på dev, før den udgives.
4. **Udgivelse:** en administrator udgiver. Opsætningen får et versionsnummer.
5. **Tilbagerulning:** hver version gemmes, og man kan gå tilbage.
6. **Revisionslog:** hvem ændrede hvad og hvornår.

**Eksport og import** som JSON giver *branchepakker*: "vindmølle-montage" (OneOps),
"håndværker", "lager" osv. En ny kunde starter fra en pakke og retter til. Det er det, der
gør det hurtigt at stille et komplet system op.

## 10. Versioner og opgradering

- Motoren udgives som skabelonversioner gennem website-mcp's katalog, som i dag.
- Hver kunde står på en bestemt version og opgraderes bevidst.
- Opsætningens schema har sit eget versionsnummer. Ændres formatet, følger der en
  omskriver med, som løfter gamle kladder og udgivelser til det nye format, og en prøve, der
  kører den på branchepakkerne.
- Migrationer er expand/contract som altid.

## 11. Rækkefølge og hvornår et trin er færdigt

| Trin | Indhold | Færdigt når |
| --- | --- | --- |
| **1. Motor v0.3** | Temamotor, rettighedsmotor sået fra en xlsx, skærm-motor med `liste`, `formular`, `noegletal`, `dialog`, opsætningens livscyklus (kladde, validering, udgivelse) | 3 HR-skærme fra forlægget kører alene som data, og et skift af tema ændrer hele appen uden genudgivelse. Gate grøn. |
| **2. OneOps-pakker** | `feltapp` og `flow`, som Anders vil starte med | En montør kan låse et site, arbejde offline gennem et flow med foto og synke bagefter. Afprøvet på telefon i rigtig størrelse. |
| **3. Resten af klodserne** | De sidste 8 klodser, de øvrige OneOps-moduler som opsætning | Skærmene fra HR, HSEQ, Certifikat og Doc wizard er data. Målt mod optællingen i afsnit 2. |
| **4. Motor v1.0** | Offentlige sider og SEO, eksport og import, branchepakken "vindmølle-montage" | En ny tom kunde kan starte fra branchepakken og have et kørende system samme dag. |

## 12. Beslutninger, der skal træffes før trin 1

1. **Ejerskab og licens.** Tilbud #59 lover, at A.B.Mikkelsen ejer koden. Skal motoren
   genbruges, bør aftalen sige: kunden ejer sin opsætning, sine data og de pakker, der er
   lavet alene til kunden; ufi-tech ejer motoren og de fælles pakker og giver kunden licens.
   Det skal med i rettelsen af tilbud #59.
2. **Hvor motoren bor.** Forslag: app-skabelon vokser op til motoren (eller et nyt
   ufi-tech-repo forkes ud af den), og ufi-tech/oneops bliver kundens instans med opsætning
   og egne pakker.
3. **Hvor meget kundens AI må.** Forslag: den må oprette kladder til skærme, felter og tema
   via data-MCP'en og skrive pakkekode gennem gaten, men aldrig udgive opsætning eller
   ændre rettigheder.

## 13. Risici

| Risiko | Modtræk |
| --- | --- |
| Motoren bliver for generisk og langsom at bygge | Kun klodser, der er talt op i rigtige forlæg. En ny klods kræver mindst to skærme, der bruger den. |
| Kunderne driver fra hinanden på motorversioner | Opgradering er en del af driftsaftalen, og branchepakkerne prøves mod hver ny version. |
| Opsætning i databasen bliver uoverskuelig | Eksport som JSON, versionering, revisionslog og en editor, der viser hvor en datakilde bruges. |
| Feltappen bliver forsinket af motorarbejdet | Trin 2 kan starte parallelt med trin 1, fordi `feltapp` er en pakke, der kun skal bruge rettigheder og tema. |

## 14. Kilder

- Optællingen af Lovable-skærmene og genbrugskortet: ufi-viden, projekt `oneops` (2026-10-05).
- OneOps' krav: ufi-tech/oneops `docs/krav/` (app-specifikation, mailen fra 4/5, Rettighedsmatrix V2.0, pwa-spec).
- Screens widget-model: iocast-screen og skill `iocast-screen-widget`.
- Vejr: iocast-screen `backend/app/collectors/builtin.py`.
- Passkey, tema pr. kunde og arbejdstidsloven: Tider.
- Data-MCP med kladde-grænse og låseregler for SQLite: Plinthcode DMS og plinthcode-tire.
