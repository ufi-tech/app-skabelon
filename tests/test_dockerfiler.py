"""Dockerfilerne: pinnet base, ingen root, ingen ADD fra en adresse.

Det er de tre krav gatens trin 8 stiller. Bliver de brudt, begynder hver ny kunde på
rødt, og så holder ingen dem i hævd.
"""

from __future__ import annotations

import re

import pytest
from stier import REPO

FILER = sorted(REPO.glob("Dockerfile*"))

FROM_LINJE = re.compile(r"^\s*FROM\s+(?P<billede>\S+)", re.IGNORECASE)
STADIE = re.compile(r"^\s*FROM\s+\S+\s+AS\s+(?P<navn>\S+)", re.IGNORECASE)
USER_LINJE = re.compile(r"^\s*USER\s+(?P<bruger>\S+)", re.IGNORECASE)
ADD_URL = re.compile(r"^\s*ADD\s+[^\n]*https?://", re.IGNORECASE)


def _er_pinnet(billede: str) -> bool:
    if billede.startswith("$") or "${" in billede:
        return False
    if "@sha256:" in billede:
        return True
    _, skilletegn, maerkat = billede.rpartition(":")
    if not skilletegn or "/" in maerkat:
        return False
    return bool(maerkat) and maerkat.lower() != "latest"


def test_der_er_dockerfiler() -> None:
    assert {fil.name for fil in FILER} == {"Dockerfile.api", "Dockerfile.web"}


@pytest.mark.parametrize("fil", FILER, ids=lambda f: f.name)
def test_basebilleder_er_pinnede(fil) -> None:
    stadier: set[str] = set()
    for linje in fil.read_text(encoding="utf-8").splitlines():
        traef = FROM_LINJE.match(linje)
        if not traef:
            continue
        billede = traef.group("billede")
        if billede.lower() not in stadier:
            assert _er_pinnet(billede), f"{fil.name}: {billede} er ikke pinnet"
        navn = STADIE.match(linje)
        if navn:
            stadier.add(navn.group("navn").lower())


@pytest.mark.parametrize("fil", FILER, ids=lambda f: f.name)
def test_sidste_trin_koerer_ikke_som_root(fil) -> None:
    bruger: str | None = None
    for linje in fil.read_text(encoding="utf-8").splitlines():
        if FROM_LINJE.match(linje):
            bruger = None
        traef = USER_LINJE.match(linje)
        if traef:
            bruger = traef.group("bruger")
    assert bruger is not None, f"{fil.name} sætter ikke USER i sidste trin"
    assert bruger not in ("root", "0", "0:0"), f"{fil.name} kører som root"


@pytest.mark.parametrize("fil", FILER, ids=lambda f: f.name)
def test_ingen_add_fra_en_adresse(fil) -> None:
    for nummer, linje in enumerate(fil.read_text(encoding="utf-8").splitlines(), start=1):
        assert not ADD_URL.match(linje), f"{fil.name}:{nummer} henter med ADD fra en adresse"


def test_afhaengighederne_installeres_med_sha256() -> None:
    """--require-hashes: en pakke der er skiftet ud på vejen, stopper byggeriet."""
    tekst = (REPO / "Dockerfile.api").read_text(encoding="utf-8")
    assert "--require-hashes" in tekst
    krav = (REPO / "api" / "requirements.txt").read_text(encoding="utf-8")
    assert "--hash=sha256:" in krav
