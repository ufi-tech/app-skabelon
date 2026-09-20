"""Forbindelsen til SQLite. Eet sted, saa der aldrig opstaar to motorer.

Motoren er DOVEN med vilje: den bliver foerst lavet ved foerste brug, saa en test kan
pege DATABASE_URL et andet sted hen, foer noget er aabnet. `nulstil()` er der for netop
det, og testene kalder den i en fixture.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from indstillinger import hent

_motor: Engine | None = None
_lav_session: sessionmaker[Session] | None = None


def _sti_fra_url(url: str) -> Path | None:
    if not url.startswith("sqlite:///"):
        return None
    return Path(url[len("sqlite:///") :])


def motor() -> Engine:
    global _motor
    if _motor is None:
        url = hent().database_url
        sti = _sti_fra_url(url)
        if sti is not None and sti.parent != Path(""):
            sti.parent.mkdir(parents=True, exist_ok=True)
        _motor = create_engine(url, future=True, pool_pre_ping=True)

        @event.listens_for(_motor, "connect")
        def _saet_pragmaer(forbindelse, _post):  # noqa: ANN001 - DBAPI-objekt uden type
            markoer = forbindelse.cursor()
            markoer.execute("PRAGMA journal_mode=WAL")
            markoer.execute("PRAGMA foreign_keys=ON")
            markoer.close()

    return _motor


def sessioner() -> sessionmaker[Session]:
    global _lav_session
    if _lav_session is None:
        _lav_session = sessionmaker(bind=motor(), autoflush=False, expire_on_commit=False)
    return _lav_session


def nulstil() -> None:
    """Smider motoren vaek. Bruges af testene og af intet andet."""
    global _motor, _lav_session
    if _motor is not None:
        _motor.dispose()
    _motor = None
    _lav_session = None


def hent_db() -> Iterator[Session]:
    """FastAPI-afhaengighed. Kalderen ejer transaktionen og committer selv."""
    session = sessioner()()
    try:
        yield session
    finally:
        session.close()
