"""Migrationerne: de kører fra en tom base, og de fjerner ikke noget.

Gaten kræver expand/contract. Grunden står i README: kører der en destruktiv migration,
og bliver koden bagefter rullet tilbage, møder den gamle kode et skema den ikke kender,
og så virker hverken den nye eller den gamle udgave.
"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from conftest import BASE, ROD

#: De kald i en alembic-migration der fjerner noget. Agentens udgivelse leder efter
#: præcis de her ord, før den kører en migration i produktion.
FJERNER = ("drop_table", "drop_column", "drop_constraint", "drop_index", "rename_table")

#: Det samme i ren SQL. Vagten leder efter de her ord i alt under migrationer/.
FJERNER_SQL = ("drop table", "drop column", "truncate table", "rename column")


def _migrationsfiler() -> list[Path]:
    return sorted((ROD / "migrationer" / "versions").glob("*.py"))


def test_der_er_mindst_een_migration() -> None:
    assert _migrationsfiler()


def test_migrationerne_byggede_basen_op(migreret: None) -> None:
    """Fixturen kørte alembic mod en tom fil. Her tjekkes resultatet."""
    motor = sa.create_engine("sqlite:///" + str(BASE))
    with motor.connect() as forbindelse:
        navne = set(sa.inspect(forbindelse).get_table_names())
    motor.dispose()
    assert {"brugere", "alembic_version"} <= navne


def test_ingen_migration_fjerner_noget() -> None:
    for fil in _migrationsfiler():
        tekst = fil.read_text(encoding="utf-8")
        krop = "\n".join(linje for linje in tekst.splitlines() if not linje.strip().startswith("#")).lower()
        for ord_ in FJERNER:
            assert f"op.{ord_}(" not in krop, f"{fil.name} kalder {ord_}"
        for ord_ in FJERNER_SQL:
            assert ord_ not in krop, f"{fil.name} indeholder '{ord_}'"


def test_revisionerne_er_entydige() -> None:
    set_af_revisioner = set()
    for fil in _migrationsfiler():
        for linje in fil.read_text(encoding="utf-8").splitlines():
            if linje.startswith("revision"):
                set_af_revisioner.add(linje.split("=", 1)[1].strip())
    assert len(set_af_revisioner) == len(_migrationsfiler())
