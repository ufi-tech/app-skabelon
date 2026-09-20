"""Skabelonen skal kunne bestå sin egen gate.

DEN RIGTIGE VAGT kører, hvis miljøet peger på en udgave af website-mcp:

    VAGT_MODUL=/sti/til/website-mcp VAGT_REGLER=/sti/til/retningslinjer/regler.yaml

Så importeres workspace_agent.vagt, og hele træet bliver gennemgået med det regelsæt,
agenten selv bruger. Det er den prøve, der gælder, og den kører i ufi-tech's egen
kontrol, før en ny version af skabelonen bliver tagget.

UDEN DEN peger prøven det ud i stedet for at lade som om den har målt noget. Kunden har
ikke website-mcp liggende, og en kopi af regelmotoren her ville være en anden motor, der
langsomt drev fra den rigtige. Kanariefuglen nedenunder kører altid: den fanger de fund,
der er nemmest at komme til at lave, mens den rigtige vagt fanger resten.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest
from stier import REPO

#: Mapper der ikke er vores kode.
SPRING_OVER = {".git", "node_modules", ".venv", "dist", "__pycache__", ".pytest_cache", ".ruff_cache"}

#: Filer der aldrig hører til i et repo.
FORBUDTE_MOENSTRE = ("*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*")

#: Det mest almindelige, en hemmelighed ligner. Den fulde liste står i vagtens regelsæt.
HEMMELIGHEDER = (
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"),
    re.compile(
        r"(?i)\b(?:adgangskode|kodeord|password|passwd|secret|hemmelighed|api[_-]?key)"
        r"\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']"
    ),
)


def _filer() -> list[Path]:
    fundne: list[Path] = []
    for sti in REPO.rglob("*"):
        if not sti.is_file():
            continue
        if SPRING_OVER & set(sti.relative_to(REPO).parts):
            continue
        fundne.append(sti)
    return fundne


def test_ingen_noeglefiler_i_repoet() -> None:
    for sti in _filer():
        navn = sti.name
        for moenster in FORBUDTE_MOENSTRE:
            assert not Path(navn).match(moenster), f"{sti} hører ikke i repoet"
        assert navn != ".env", f"{sti} hører ikke i repoet"


def test_ingen_hemmeligheder_i_koden() -> None:
    """Dokumentation og eksempelfiler er undtaget, præcis som i vagtens regelsæt:
    de skal kunne vise et mønster frem uden at være et fund."""
    for sti in _filer():
        undtaget = sti.suffix in (".md", ".lock", ".png", ".jpg", ".svg", ".woff2")
        if undtaget or sti.name.endswith((".example", ".sample")) or sti.name == "package-lock.json":
            continue
        try:
            tekst = sti.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for moenster in HEMMELIGHEDER:
            traef = moenster.search(tekst)
            assert traef is None, f"{sti.relative_to(REPO)} ligner en hemmelighed"


def test_den_rigtige_vagt_finder_ingenting_blokerende() -> None:
    modul = os.environ.get("VAGT_MODUL", "").strip()
    regler_sti = os.environ.get("VAGT_REGLER", "").strip()
    if not modul or not regler_sti:
        pytest.skip(
            "VAGT_MODUL og VAGT_REGLER er ikke sat, så den rigtige vagt kørte ikke. "
            "Agentens gate kører den i workspacet."
        )
    if modul not in sys.path:
        sys.path.insert(0, modul)
    from workspace_agent import vagt  # type: ignore[import-not-found]

    regler = vagt.indlaes_fil(regler_sti)
    fund = vagt.tjek_traeet(regler, REPO, rolle="ufitech")
    blokerende = vagt.blokerende(fund)
    assert not blokerende, "\n".join(f"{f.regel}: {f.fil}:{f.linje} {f.besked}" for f in blokerende)
