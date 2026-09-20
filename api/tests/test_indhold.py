"""Indholdet er statisk i version 1, men formen ligger fast."""

from __future__ import annotations

import indhold


def test_sider_har_den_aftalte_form() -> None:
    alle = indhold.sider()
    assert alle
    for side in alle:
        assert side["sti"].startswith("/")
        assert side["titel"]
        for blok in side["blokke"]:
            assert blok["type"] in indhold.BLOKTYPER


def test_side_findes_og_findes_ikke() -> None:
    assert indhold.side("/")["titel"] == "Forside"
    assert indhold.side("/findes-ikke") is None
    assert indhold.side("../../etc/passwd") is None
    assert indhold.side("/Store-Bogstaver") is None


def test_kalderen_kan_ikke_aendre_kilden() -> None:
    foerste = indhold.side("/")
    foerste["blokke"].clear()
    assert indhold.side("/")["blokke"]


def test_ruterne_svarer(klient) -> None:
    liste = klient.get("/api/indhold/sider")
    assert liste.status_code == 200
    assert liste.json()["bloktyper"] == list(indhold.BLOKTYPER)

    side = klient.get("/api/indhold/side", params={"sti": "/om-os"})
    assert side.status_code == 200
    assert side.json()["titel"] == "Om os"

    assert klient.get("/api/indhold/side", params={"sti": "/vaek"}).status_code == 404


def test_hver_bloktype_har_en_komponent() -> None:
    """En bloktype uden komponent i web/ ville blive usynlig uden en fejl."""
    from conftest import ROD

    mappe = ROD.parent / "web" / "src" / "blokke"
    for type_ in indhold.BLOKTYPER:
        assert (mappe / f"{type_}.tsx").is_file(), f"der mangler en komponent til {type_}"
