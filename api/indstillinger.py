"""Indstillinger læst fra miljøet. Ingen hemmelighed står i koden.

SESSION_HEMMELIGHED findes i den rækkefølge:

1. miljøvariablen, hvis den er sat. Den vinder altid, så en driftsansvarlig kan styre
   den fra miljøfilen på serveren.
2. filen `session-hemmelighed` i datamappen, hvis den findes.
3. ellers laves en ny med `secrets.token_urlsafe` og skrives med rettighederne 600.

Hvorfor punkt 2 og 3: datamappen er /srv/prod-data i produktion, og den er ejet af root
og ikke af den bruger kundens AI kører som. Hemmeligheden ligger altså på den anden side
af den samme grænse som databasen selv, og ingen behøver at huske at sætte en variabel,
før den første udgivelse virker. Uden filen ville alle blive logget ud ved hver
genstart, og så ville nogen skrive en fast værdi ind i repoet i stedet.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path

#: Navnet på miljøet. Alt andet end "udvikling" behandles som produktion.
UDVIKLING = "udvikling"

#: Standardplaceringen af SQLite-basen. Mappen data/ er monteret ind i containeren.
STANDARD_DATABASE = "sqlite:///./data/app.db"

#: Filen med sessionshemmeligheden, inde i datamappen.
HEMMELIGHEDSFIL = "session-hemmelighed"

#: Kortere end det er ikke en hemmelighed, det er en gæt-opgave.
MINDSTE_LAENGDE = 32

#: Hvor længe en session lever. Otte timer er en arbejdsdag.
SESSION_LEVETID_S = 8 * 60 * 60


class OpsaetningsFejl(RuntimeError):
    """Appen er sat forkert op. Beskeden er dansk og siger hvad der mangler."""


@dataclass(frozen=True)
class Indstillinger:
    miljoe: str
    session_hemmelighed: str
    database_url: str
    data_mappe: Path
    sikker_cookie: bool

    @property
    def er_udvikling(self) -> bool:
        return self.miljoe == UDVIKLING


def _datamappe(database_url: str) -> Path:
    valgt = os.environ.get("DATA_MAPPE", "").strip()
    if valgt:
        return Path(valgt)
    if database_url.startswith("sqlite:///"):
        forael = Path(database_url[len("sqlite:///") :]).parent
        if str(forael) not in ("", "."):
            return forael
    return Path("data")


def _fra_fil(mappe: Path) -> str:
    sti = mappe / HEMMELIGHEDSFIL
    try:
        if sti.is_file():
            tekst = sti.read_text(encoding="utf-8").strip()
            if len(tekst) >= MINDSTE_LAENGDE:
                return tekst
        ny = secrets.token_urlsafe(48)
        mappe.mkdir(parents=True, exist_ok=True)
        beskrivelse = os.open(sti, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(beskrivelse, "w", encoding="utf-8") as fil:
            fil.write(ny)
        return ny
    except OSError as fejl:
        raise OpsaetningsFejl(
            f"Sessionshemmeligheden kunne hverken læses eller skrives i {mappe}. "
            "Sæt SESSION_HEMMELIGHED i miljøet, eller giv appen skriveadgang til datamappen."
        ) from fejl


def _hemmelighed(mappe: Path) -> str:
    vaerdi = os.environ.get("SESSION_HEMMELIGHED", "").strip()
    if not vaerdi:
        return _fra_fil(mappe)
    if len(vaerdi) < MINDSTE_LAENGDE:
        raise OpsaetningsFejl(
            f"SESSION_HEMMELIGHED er for kort. Brug mindst {MINDSTE_LAENGDE} tegn, for "
            "eksempel fra python -c 'import secrets; print(secrets.token_urlsafe(48))'."
        )
    return vaerdi


def hent() -> Indstillinger:
    miljoe = os.environ.get("APP_MILJOE", UDVIKLING).strip().lower() or UDVIKLING
    database_url = os.environ.get("DATABASE_URL", "").strip() or STANDARD_DATABASE
    mappe = _datamappe(database_url)
    return Indstillinger(
        miljoe=miljoe,
        session_hemmelighed=_hemmelighed(mappe),
        database_url=database_url,
        data_mappe=mappe,
        sikker_cookie=miljoe != UDVIKLING,
    )
