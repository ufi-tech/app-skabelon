"""Indholdet til sitet. STATISK i version 1.

HVORFOR STATISK. Version 2 henter siderne fra website-mcp med en læse-nøgle. Den flade
trækker en Access-app, en nøgle der skal skiftes, og hele proxy-opsætningen med sig, og
piloten har ikke noget indhold at hente endnu. Felterne står klar i skabelon.yaml, og
klienten er første punkt på v2-listen.

FORMEN LIGGER FAST NU, saa v2 kun skifter HVOR indholdet kommer fra, ikke hvad resten af
appen ser:

    {"sti": "/", "titel": "Forside", "blokke": [{"type": "overskrift", ...}, ...]}

Hver bloktype har præcis én React-komponent i web/src/blokke/. Tilføjer du en bloktype,
tilføjer du begge dele og en prøve til hver.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter(prefix="/api/indhold", tags=["indhold"])

#: En sti er "/" eller "/" plus et eller flere led med små bogstaver, tal og bindestreg.
STI_MOENSTER = re.compile(r"/|(?:/[a-z0-9](?:[a-z0-9-]{0,62})?)+\Z")

#: De bloktyper der findes. Listen er sandheden begge veje: en blok af en anden type
#: bliver ikke vist, og en type uden komponent i web/src/blokke/ fanges af prøverne.
BLOKTYPER: tuple[str, ...] = ("overskrift", "tekst", "billede", "knap")

_SIDER: tuple[dict[str, Any], ...] = (
    {
        "sti": "/",
        "titel": "Forside",
        "blokke": (
            {"type": "overskrift", "niveau": 1, "tekst": "Velkommen"},
            {
                "type": "tekst",
                "tekst": (
                    "Det her er startsiden i skabelonen site-basis. Ret teksten, tilføj "
                    "blokke, og byg videre. Indholdet står i api/indhold.py."
                ),
            },
            {"type": "knap", "tekst": "Log ind", "href": "/log-ind"},
        ),
    },
    {
        "sti": "/om-os",
        "titel": "Om os",
        "blokke": (
            {"type": "overskrift", "niveau": 1, "tekst": "Om os"},
            {"type": "tekst", "tekst": "Skriv et par linjer om virksomheden her."},
            {
                "type": "billede",
                "kilde": "/billeder/pladsholder.svg",
                "alt": "Pladsholder indtil der ligger et rigtigt billede",
            },
        ),
    },
)


def _kopi(side: dict[str, Any]) -> dict[str, Any]:
    """En frisk kopi, så en kalder aldrig kan rette i kilden ved et uheld."""
    return {
        "sti": side["sti"],
        "titel": side["titel"],
        "blokke": [dict(blok) for blok in side["blokke"]],
    }


def sider() -> list[dict[str, Any]]:
    """Alle sider, i den rækkefølge de står i menuen."""
    return [_kopi(side) for side in _SIDER]


def side(sti: str) -> dict[str, Any] | None:
    """Én side, eller None hvis stien ikke findes."""
    if not isinstance(sti, str) or not STI_MOENSTER.fullmatch(sti):
        return None
    for post in _SIDER:
        if post["sti"] == sti:
            return _kopi(post)
    return None


@router.get("/sider")
def rute_sider() -> dict[str, Any]:
    """Offentligt indhold: det er selve hjemmesiden, og den er åben for alle."""
    return {"sider": [{"sti": s["sti"], "titel": s["titel"]} for s in _SIDER], "bloktyper": list(BLOKTYPER)}


@router.get("/side")
def rute_side(sti: str = Query(min_length=1, max_length=200)) -> dict[str, Any]:
    fundet = side(sti)
    if fundet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Den side findes ikke.")
    return fundet
