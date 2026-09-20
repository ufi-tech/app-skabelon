"""Tabellen brugere.

Revision: 0001
Bygger på: ingen

Den første migration. Den tilføjer kun, og den er derfor bagudkompatibel: kører den, og
bliver koden bagefter rullet tilbage, møder den gamle kode en tabel den ikke kender, og
det gør ingen skade.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brugere",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("epost", sa.String(length=320), nullable=False),
        sa.Column("navn", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("kode_hash", sa.String(length=200), nullable=False),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("oprettet", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_brugere_epost", "brugere", ["epost"], unique=True)


def downgrade() -> None:
    """Tom med vilje.

    En nedadgående migration der fjerner noget, er præcis det gaten ikke vil have. Skal
    tabellen væk, sker det i en senere udgivelse, når ingen kode bruger den længere.
    """
