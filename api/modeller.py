"""Tabellerne. Een fil, saa migrationerne har eet sted at se efter.

Tidskolonner er tidszone-bevidste og gemmes i UTC. Servere koerer UTC, og en tid uden
zone bliver foer eller siden laest som lokaltid af nogen.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def nu_utc() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Bruger(Base):
    """En person der kan logge ind. Adgangskoden gemmes kun som et bcrypt-hash."""

    __tablename__ = "brugere"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    epost: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    navn: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    kode_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    aktiv: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    oprettet: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=nu_utc)

    def som_dict(self) -> dict[str, object]:
        return {"id": self.id, "epost": self.epost, "navn": self.navn}
