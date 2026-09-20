"""Login med session i en cookie. Ingen selvskrevet krypto.

TO FAERDIGE BIBLIOTEKER GOER ARBEJDET:

- `bcrypt` hasher adgangskoden. Den er langsom med vilje, saa en stjaalet base ikke
  bliver til en liste over kodeord i loebet af en aften.
- Starlettes `SessionMiddleware` signerer cookien med `itsdangerous`. Roeres en cookie
  af nogen undervejs, holder signaturen ikke, sessionen bliver tom, og kaldet ender som
  401. Det er derfor der ikke ligger en eneste linje krypto i den her fil.

Cookien indeholder KUN bruger-id og et tidsstempel. Rettigheder slaas op i basen ved
hvert kald, saa en aendring i basen virker med det samme og ikke foerst naar cookien
udloeber.
"""

from __future__ import annotations

from datetime import UTC, datetime

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import hent_db
from indstillinger import SESSION_LEVETID_S
from modeller import Bruger

router = APIRouter(prefix="/api", tags=["login"])

#: Noeglerne i sessionen. Staar her, saa de kun skrives eet sted.
BRUGER_NOEGLE = "bruger_id"
TID_NOEGLE = "logget_ind"

#: bcrypt laeser hoejst 72 bytes. Laengere input afvises i stedet for at blive klippet,
#: saa to forskellige lange kodeord aldrig kan blive det samme hash.
MAKS_KODE_BYTES = 72


class LogIndKrop(BaseModel):
    epost: str = Field(min_length=3, max_length=320)
    adgangskode: str = Field(min_length=8, max_length=200)


def hash_kode(kode: str) -> str:
    raa = kode.encode("utf-8")
    if len(raa) > MAKS_KODE_BYTES:
        raise ValueError("Adgangskoden er for lang. Brug højst 72 tegn.")
    return bcrypt.hashpw(raa, bcrypt.gensalt()).decode("ascii")


def kode_passer(kode: str, hash_vaerdi: str) -> bool:
    raa = kode.encode("utf-8")
    if len(raa) > MAKS_KODE_BYTES:
        return False
    try:
        return bcrypt.checkpw(raa, hash_vaerdi.encode("ascii"))
    except (ValueError, TypeError):
        return False


def _afvis() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Du er ikke logget ind. Log ind igen.",
    )


def valgfri_bruger(anmodning: Request, db: Session = Depends(hent_db)) -> Bruger | None:
    """Brugeren bag cookien, eller None. Rydder en session der peger på ingenting."""
    bruger_id = anmodning.session.get(BRUGER_NOEGLE)
    if not isinstance(bruger_id, int):
        return None
    bruger = db.get(Bruger, bruger_id)
    if bruger is None or not bruger.aktiv:
        anmodning.session.clear()
        return None
    return bruger


def kraev_bruger(bruger: Bruger | None = Depends(valgfri_bruger)) -> Bruger:
    """Afhængigheden hver beskyttet rute hænger på. Fail-closed hele vejen."""
    if bruger is None:
        raise _afvis()
    return bruger


@router.post("/log-ind")
def log_ind(krop: LogIndKrop, anmodning: Request, db: Session = Depends(hent_db)) -> dict[str, object]:
    """Samme svar uanset om e-posten findes eller kodeordet er forkert."""
    bruger = db.scalar(select(Bruger).where(Bruger.epost == krop.epost.strip().lower()))
    if bruger is None or not bruger.aktiv or not kode_passer(krop.adgangskode, bruger.kode_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posten eller adgangskoden passer ikke.",
        )
    anmodning.session.clear()
    anmodning.session[BRUGER_NOEGLE] = bruger.id
    anmodning.session[TID_NOEGLE] = datetime.now(UTC).isoformat()
    return {"bruger": bruger.som_dict(), "session_levetid_s": SESSION_LEVETID_S}


@router.post("/log-ud")
def log_ud(
    anmodning: Request,
    bruger: Bruger | None = Depends(valgfri_bruger),
) -> dict[str, object]:
    """Virker også når man ikke var logget ind. Så er svaret det samme."""
    anmodning.session.clear()
    return {"logget_ud": True, "var_logget_ind": bruger is not None}


@router.get("/mig")
def mig(bruger: Bruger = Depends(kraev_bruger)) -> dict[str, object]:
    return {"bruger": bruger.som_dict()}
