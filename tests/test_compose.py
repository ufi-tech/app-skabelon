"""Compose-filerne skal kunne bestå agentens compose-værn ved første preview.

Værnet ligger i workspace_agent/docker.py og kan ikke importeres her: det er et andet
repo. Prøven gentager derfor de krav, der er skrevet ned i BYGSELV-DESIGN.md kap. 5.6,
så en ændring i skabelonen bliver stoppet her og ikke først hos en kunde.
"""

from __future__ import annotations

import ipaddress
from typing import Any

import pytest
import yaml
from stier import REPO

DEV = REPO / "docker-compose.yml"
PROD = REPO / "docker-compose.prod.yml"

#: Den eneste adresse en port må bindes til.
LOOPBACK = "127.0.0.1"

#: Brandmuren i VM'en tillader netop det her område container til container.
TILLADT_OMRAADE = ipaddress.ip_network("172.20.0.0/16")

#: Nøgler der aldrig må stå på en tjeneste.
FORBUDT = (
    "privileged",
    "cap_add",
    "devices",
    "security_opt",
    "sysctls",
    "userns_mode",
    "group_add",
    "volumes_from",
    "extends",
)


def _laes(sti) -> dict[str, Any]:
    return yaml.safe_load(sti.read_text(encoding="utf-8"))


def _tjenester(sti) -> dict[str, dict[str, Any]]:
    data = _laes(sti)
    assert isinstance(data, dict)
    tjenester = data.get("services")
    assert isinstance(tjenester, dict) and tjenester, f"{sti.name} har ingen tjenester"
    return tjenester


@pytest.mark.parametrize("sti", [DEV, PROD], ids=["dev", "prod"])
def test_hver_tjeneste_har_lofter_og_en_bruger(sti) -> None:
    """mem_limit, pids_limit og user på hver tjeneste, i BEGGE filer.

    Agenten validerer hver compose-fil for sig, før den lader docker flette dem. En
    overlay-fil skal derfor kunne stå alene og stadig overholde reglerne.
    """
    for navn, tjeneste in _tjenester(sti).items():
        assert tjeneste.get("mem_limit"), f"{navn} i {sti.name} mangler mem_limit"
        assert tjeneste.get("pids_limit"), f"{navn} i {sti.name} mangler pids_limit"
        assert tjeneste.get("user"), f"{navn} i {sti.name} mangler user"
        assert "0:0" not in str(tjeneste["user"]), f"{navn} kører som root"


@pytest.mark.parametrize("sti", [DEV, PROD], ids=["dev", "prod"])
def test_porte_er_bundet_til_loopback(sti) -> None:
    for navn, tjeneste in _tjenester(sti).items():
        for post in tjeneste.get("ports") or []:
            tekst = str(post)
            assert tekst.startswith(LOOPBACK + ":"), f"{navn} i {sti.name} binder '{tekst}' bredt"
            assert len(tekst.split(":")) == 3, f"{navn} i {sti.name} mangler en værtsadresse"


@pytest.mark.parametrize("sti", [DEV, PROD], ids=["dev", "prod"])
def test_ingen_farlige_noegler(sti) -> None:
    for navn, tjeneste in _tjenester(sti).items():
        for noegle in FORBUDT:
            assert not tjeneste.get(noegle), f"{navn} i {sti.name} bruger {noegle}"
        for vaert_noegle in ("network_mode", "pid", "ipc"):
            assert str(tjeneste.get(vaert_noegle) or "") != "host"
        for bind in tjeneste.get("volumes") or []:
            assert "docker.sock" not in str(bind)


def test_dev_binder_8080_og_prod_binder_8081() -> None:
    dev = _tjenester(DEV)["web"]["ports"]
    prod = _tjenester(PROD)["web"]["ports"]
    assert dev == ["127.0.0.1:8080:8080"], "preview forventer 127.0.0.1:8080"
    assert prod == ["127.0.0.1:8081:8080"], "udgivelsens sundhedstjek forventer 127.0.0.1:8081"


def test_dev_starter_ikke_sig_selv_igen() -> None:
    for navn, tjeneste in _tjenester(DEV).items():
        genstart = str(tjeneste.get("restart") or "").lower()
        assert genstart not in ("always", "unless-stopped"), f"{navn} må ikke genstarte i dev"


def test_produktionen_gemmer_data_uden_for_hjemmemappen() -> None:
    api = _tjenester(PROD)["api"]
    assert "/srv/prod-data:/app/data" in [str(b) for b in api["volumes"]]


def test_netvaerket_er_navngivet_med_et_kendt_subnet() -> None:
    for sti in (DEV, PROD):
        netvaerk = _laes(sti).get("networks") or {}
        assert netvaerk, f"{sti.name} mangler et navngivet netværk"
        for navn, definition in netvaerk.items():
            assert definition.get("name"), f"netværket {navn} i {sti.name} er ikke navngivet"
            opsaetning = (definition.get("ipam") or {}).get("config") or []
            assert opsaetning, f"netværket {navn} i {sti.name} mangler et subnet"
            for post in opsaetning:
                net = ipaddress.ip_network(post["subnet"])
                assert net.subnet_of(TILLADT_OMRAADE), f"{net} ligger uden for {TILLADT_OMRAADE}"


def test_byggetrinnet_kender_proxyen() -> None:
    """Containere kan ikke nå VM'ens loopback. Proxyen skal stå som byggeargument."""
    for navn, tjeneste in _tjenester(DEV).items():
        byg = tjeneste.get("build")
        assert isinstance(byg, dict), f"{navn} bygger ikke fra en Dockerfile i repoet"
        argumenter = byg.get("args") or {}
        for noegle in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"):
            assert noegle in argumenter, f"{navn} mangler byggeargumentet {noegle}"
        assert str(byg.get("context") or "").strip() in (".", "./")
