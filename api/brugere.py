"""Opret eller ret en bruger fra kommandolinjen.

    uv run python brugere.py chef@example.com "Chefen"

Adgangskoden læses fra miljøvariablen START_ADGANGSKODE. Den står aldrig som argument:
en kommandolinje kan læses af enhver på maskinen og ender i shell-historikken.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import select

from auth import hash_kode
from database import sessioner
from modeller import Bruger


def opret(epost: str, navn: str, kode: str) -> str:
    """Opretter brugeren eller sætter en ny adgangskode på en der findes."""
    if len(kode) < 12:
        raise SystemExit("Adgangskoden skal være mindst 12 tegn.")
    with sessioner()() as session:
        bruger = session.scalar(select(Bruger).where(Bruger.epost == epost))
        if bruger is None:
            bruger = Bruger(epost=epost, navn=navn, kode_hash=hash_kode(kode), aktiv=True)
            session.add(bruger)
            svar = f"Brugeren {epost} blev oprettet."
        else:
            bruger.navn = navn or bruger.navn
            bruger.kode_hash = hash_kode(kode)
            bruger.aktiv = True
            svar = f"Adgangskoden for {epost} blev skiftet."
        session.commit()
    return svar


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("brug: python brugere.py <e-post> [navn]", file=sys.stderr)
        return 2
    kode = os.environ.get("START_ADGANGSKODE", "")
    if not kode:
        print("START_ADGANGSKODE mangler i miljøet.", file=sys.stderr)
        return 2
    print(opret(argv[1].strip().lower(), (argv[2] if len(argv) == 3 else "").strip(), kode))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
