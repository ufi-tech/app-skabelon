"""skabelon.yaml er det, katalogets post i website-mcp hviler på."""

from __future__ import annotations

import json

import yaml
from stier import REPO

SKABELON = yaml.safe_load((REPO / "skabelon.yaml").read_text(encoding="utf-8"))


def test_navn_og_version() -> None:
    assert SKABELON["navn"] == "site-basis"
    assert SKABELON["version"] == "0.1.0"


def test_gate_kommandoerne_findes_som_scripts() -> None:
    pakke = json.loads((REPO / "web" / "package.json").read_text(encoding="utf-8"))
    for trin in SKABELON["gate"]["byg"] + SKABELON["gate"]["test"] + SKABELON["gate"]["lint"]:
        if trin["mappe"] == "web" and trin["kommando"][:2] == ["npm", "run"]:
            assert trin["kommando"][2] in pakke["scripts"], f"web mangler scriptet {trin['kommando'][2]}"


def test_egresslisten_har_det_byggetrinnet_skal_bruge() -> None:
    domaener = set(SKABELON["egress"])
    for paakraevet in ("registry.npmjs.org", "pypi.org", "files.pythonhosted.org"):
        assert paakraevet in domaener


def test_kravene_passer_med_dockerfilerne() -> None:
    api = (REPO / "Dockerfile.api").read_text(encoding="utf-8")
    web = (REPO / "Dockerfile.web").read_text(encoding="utf-8")
    assert SKABELON["krav"]["python"] in api
    assert SKABELON["krav"]["node"] in web


def test_versionen_er_den_samme_i_api_og_web() -> None:
    pakke = json.loads((REPO / "web" / "package.json").read_text(encoding="utf-8"))
    pyproject = (REPO / "api" / "pyproject.toml").read_text(encoding="utf-8")
    assert pakke["version"] == SKABELON["version"]
    assert f'version = "{SKABELON["version"]}"' in pyproject
