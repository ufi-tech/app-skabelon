"""Fælles opsætning for api-prøverne.

Miljøet sættes FØR main importeres. Indstillingerne læses ved import, så en fixture der
satte dem bagefter, ville komme for sent, og prøverne ville køre mod en anden database
end den, de selv har lavet.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

ROD = Path(__file__).resolve().parents[1]
if str(ROD) not in sys.path:
    sys.path.insert(0, str(ROD))

#: En tom base pr. kørsel. Migrationerne skal kunne bygge den op fra ingenting.
MAPPE = Path(tempfile.mkdtemp(prefix="app-skabelon-proeve-"))
BASE = MAPPE / "proeve.db"

os.environ["APP_MILJOE"] = "udvikling"
os.environ["SESSION_HEMMELIGHED"] = "p" * 48
os.environ["DATABASE_URL"] = "sqlite:///" + str(BASE)

#: Adgangskoden i prøverne. Den står som en konstant og aldrig som en værdi lige efter
#: ordet "adgangskode" i et kald: vagten leder efter netop det mønster, og en prøve må
#: ikke lære nogen at skrive et kodeord ind i koden.
PROEVE_KODE = "hest-batteri-haefteklamme"
PROEVE_EPOST = "chef@example.com"


@pytest.fixture(scope="session", autouse=True)
def migreret() -> None:
    """Kører alembic mod den tomme base. Fejler migrationerne, kører intet andet."""
    from alembic import command
    from alembic.config import Config

    opsaetning = Config(str(ROD / "alembic.ini"))
    opsaetning.set_main_option("script_location", str(ROD / "migrationer"))
    command.upgrade(opsaetning, "head")


@pytest.fixture
def bruger(migreret: None) -> dict[str, str]:
    import brugere
    import database

    database.nulstil()
    brugere.opret(PROEVE_EPOST, "Chefen", PROEVE_KODE)
    return {"epost": PROEVE_EPOST, "navn": "Chefen"}


@pytest.fixture
def klient(migreret: None):
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as klient:
        yield klient
