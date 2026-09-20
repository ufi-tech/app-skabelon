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

BASIS = REPO / "docker-compose.yml"
DEV_OVERLAY = REPO / "docker-compose.dev.yml"
PROD_OVERLAY = REPO / "docker-compose.prod.yml"

#: De to projekter, praecis som workspace_agent/docker.py COMPOSE_FILER starter dem.
#:
#: PRODUKTIONEN STAAR ALENE. Compose fletter `ports` og `volumes` ved at laegge sammen,
#: og en arvet liste kan kun erstattes med !override/!reset, som agentens eget
#: compose-vaern (yaml.safe_load) rejser paa. Med basis-filen under fik produktionen
#: BAADE 8080 og 8081 paa web, og baade ./data og /srv/prod-data paa api.
DEV_FILER = (BASIS, DEV_OVERLAY)
PROD_FILER = (PROD_OVERLAY,)

#: Alle filer, hver for sig. Agenten validerer dem enkeltvis foer den fletter.
ALLE = (BASIS, DEV_OVERLAY, PROD_OVERLAY)

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


def _flettede_porte(stier, tjeneste: str) -> list[str]:
    """Docker Compose-flettereglen for `ports`, skrevet ned.

    Compose slår overlay-filer sammen ved at LÆGGE ports SAMMEN på nøglen
    target+published+host_ip+protocol, ikke ved at erstatte listen. Prøven kan ikke køre
    `docker compose config` (docker er ikke en afhængighed af skabelonen), så reglen står
    her i stedet. Se docs: "ports ... are merged by appending".
    """
    ud: list[str] = []
    for sti in stier:
        for post in _tjenester(sti).get(tjeneste, {}).get("ports") or []:
            tekst = str(post)
            if tekst not in ud:
                ud.append(tekst)
    return ud


def _vaertsport(post: str) -> str:
    """'127.0.0.1:8080:8080' -> '127.0.0.1:8080'."""
    dele = post.split(":")
    return ":".join(dele[:-1])


@pytest.mark.parametrize("sti", ALLE, ids=["basis", "dev", "prod"])
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


@pytest.mark.parametrize("sti", ALLE, ids=["basis", "dev", "prod"])
def test_porte_er_bundet_til_loopback(sti) -> None:
    for navn, tjeneste in _tjenester(sti).items():
        for post in tjeneste.get("ports") or []:
            tekst = str(post)
            assert tekst.startswith(LOOPBACK + ":"), f"{navn} i {sti.name} binder '{tekst}' bredt"
            assert len(tekst.split(":")) == 3, f"{navn} i {sti.name} mangler en værtsadresse"


@pytest.mark.parametrize("sti", ALLE, ids=["basis", "dev", "prod"])
def test_ingen_farlige_noegler(sti) -> None:
    for navn, tjeneste in _tjenester(sti).items():
        for noegle in FORBUDT:
            assert not tjeneste.get(noegle), f"{navn} i {sti.name} bruger {noegle}"
        for vaert_noegle in ("network_mode", "pid", "ipc"):
            assert str(tjeneste.get(vaert_noegle) or "") != "host"
        for bind in tjeneste.get("volumes") or []:
            assert "docker.sock" not in str(bind)


def test_basis_udstiller_ingen_porte() -> None:
    """Basis-filen maa ikke publicere noget.

    Docker fletter `ports` ved at laegge sammen (noeglen er
    target+published+host_ip+protocol), ikke ved at erstatte. Stod preview-porten i
    basis-filen, ville produktionen faa BEGGE porte.
    """
    for navn, tjeneste in _tjenester(BASIS).items():
        assert not tjeneste.get("ports"), f"{navn} i {BASIS.name} publicerer en port"


def test_det_flettede_dev_binder_kun_8080_og_prod_kun_8081() -> None:
    """Måler det resultat agenten faktisk starter, ikke filerne hver for sig.

    Den gamle prøve målte kun hver fil alene og gav derfor falsk tryghed: den ville stå
    grøn, selv hvis produktionen endte med både 8080 og 8081 og dermed slog preview ihjel.
    """
    assert _flettede_porte(DEV_FILER, "web") == ["127.0.0.1:8080:8080"]
    assert _flettede_porte(PROD_FILER, "web") == ["127.0.0.1:8081:8080"]
    assert _flettede_porte(DEV_FILER, "api") == []
    assert _flettede_porte(PROD_FILER, "api") == []


def test_de_to_miljoeer_deler_ingen_vaertsport() -> None:
    """Preview og produktion skal kunne køre samtidig på den samme VM."""
    dev = {_vaertsport(p) for p in _flettede_porte(DEV_FILER, "web")}
    prod = {_vaertsport(p) for p in _flettede_porte(PROD_FILER, "web")}
    assert dev and prod
    assert not (dev & prod), f"preview og produktion deler værtsporten {dev & prod}"


def test_dev_starter_ikke_sig_selv_igen() -> None:
    for navn, tjeneste in _tjenester(BASIS).items():
        genstart = str(tjeneste.get("restart") or "").lower()
        assert genstart not in ("always", "unless-stopped"), f"{navn} må ikke genstarte i dev"


def test_produktionen_gemmer_data_uden_for_hjemmemappen() -> None:
    api = _tjenester(PROD_OVERLAY)["api"]
    binds = [str(b) for b in api["volumes"]]
    assert "/srv/prod-data:/app/data" in binds
    assert not any(b.startswith("./data") for b in binds), "repoets data-mappe må ikke følge med"


def test_produktionsfilen_kan_staa_alene() -> None:
    """Agenten starter ws-prod med KUN docker-compose.prod.yml.

    Filen skal derfor selv have alt: begge tjenester, deres build, deres netværk. Mangler
    noget, starter produktionen ikke, og fejlen kommer først i VM'en.
    """
    tjenester = _tjenester(PROD_OVERLAY)
    assert set(tjenester) == {"api", "web"}
    for navn, tjeneste in tjenester.items():
        byg = tjeneste.get("build")
        assert isinstance(byg, dict), f"{navn} i prod-filen bygger ikke fra en Dockerfile"
        for noegle in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"):
            assert noegle in (byg.get("args") or {}), f"{navn} mangler byggeargumentet {noegle}"
        assert tjeneste.get("networks"), f"{navn} i prod-filen er ikke på et netværk"
    assert (_laes(PROD_OVERLAY).get("networks") or {}), "prod-filen mangler netværksdefinitionen"


def test_produktionen_laeser_appens_hemmeligheder_fra_en_fil_uden_for_repoet() -> None:
    """/srv/prod-build er et frisk worktree ved hver udgivelse.

    Hverken en .env i projektmappen eller en utracked fil overlever, så en rigtig ekstern
    nøgle har kun én vej ind: operatørens fil. Den er root:ws 640, og required: false,
    så en ny kunde uden hemmeligheder stadig kan starte.
    """
    api = _tjenester(PROD_OVERLAY)["api"]
    poster = api.get("env_file") or []
    stier = [p.get("path") if isinstance(p, dict) else str(p) for p in poster]
    assert "/srv/prod-env/app.env" in stier
    for post in poster:
        if isinstance(post, dict) and post.get("path") == "/srv/prod-env/app.env":
            assert post.get("required") is False


def test_netvaerket_er_navngivet_med_et_kendt_subnet() -> None:
    for sti in (BASIS, PROD_OVERLAY):
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
    for navn, tjeneste in _tjenester(BASIS).items():
        byg = tjeneste.get("build")
        assert isinstance(byg, dict), f"{navn} bygger ikke fra en Dockerfile i repoet"
        argumenter = byg.get("args") or {}
        for noegle in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"):
            assert noegle in argumenter, f"{navn} mangler byggeargumentet {noegle}"
        assert str(byg.get("context") or "").strip() in (".", "./")
