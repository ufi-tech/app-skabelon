"""Login, session og de veje der skal give 401."""

from __future__ import annotations

from conftest import PROEVE_EPOST, PROEVE_KODE


def _log_ind(klient, kode: str = PROEVE_KODE, epost: str = PROEVE_EPOST):
    return klient.post("/api/log-ind", json={"epost": epost, "adgangskode": kode})


def test_login_virker_og_giver_adgang(klient, bruger) -> None:
    svar = _log_ind(klient)
    assert svar.status_code == 200
    assert svar.json()["bruger"]["epost"] == PROEVE_EPOST

    mig = klient.get("/api/mig")
    assert mig.status_code == 200
    assert mig.json()["bruger"]["navn"] == "Chefen"


def test_uden_cookie_er_der_ingen_adgang(klient, bruger) -> None:
    assert klient.get("/api/mig").status_code == 401


def test_ugyldig_cookie_giver_401(klient, bruger) -> None:
    """En pillet cookie holder ikke signaturen, og så er sessionen tom."""
    assert _log_ind(klient).status_code == 200
    rigtig = klient.cookies.get("session")
    assert rigtig
    klient.cookies.set("session", rigtig[:-4] + "aaaa")
    assert klient.get("/api/mig").status_code == 401


def test_opdigtet_cookie_giver_401(klient, bruger) -> None:
    klient.cookies.set("session", "eJ0aXNlcnNpZ25ldA.dette.er-ikke-signeret")
    assert klient.get("/api/mig").status_code == 401


def test_forkert_kode_giver_401(klient, bruger) -> None:
    svar = _log_ind(klient, kode="et-helt-andet-kodeord")
    assert svar.status_code == 401
    assert klient.get("/api/mig").status_code == 401


def test_ukendt_epost_giver_samme_svar(klient, bruger) -> None:
    svar = _log_ind(klient, epost="findes-ikke@example.com")
    assert svar.status_code == 401
    assert svar.json()["detail"] == "E-posten eller adgangskoden passer ikke."


def test_log_ud_rydder_sessionen(klient, bruger) -> None:
    assert _log_ind(klient).status_code == 200
    ud = klient.post("/api/log-ud")
    assert ud.status_code == 200
    assert ud.json()["var_logget_ind"] is True
    assert klient.get("/api/mig").status_code == 401


def test_kodehash_er_ikke_kodeordet(bruger) -> None:
    from auth import hash_kode, kode_passer

    hash_vaerdi = hash_kode(PROEVE_KODE)
    assert PROEVE_KODE not in hash_vaerdi
    assert hash_vaerdi.startswith("$2b$")
    assert kode_passer(PROEVE_KODE, hash_vaerdi)
    assert not kode_passer(PROEVE_KODE + "x", hash_vaerdi)


def test_sundhed_svarer_uden_login(klient) -> None:
    svar = klient.get("/healthz")
    assert svar.status_code == 200
    assert svar.json()["status"] == "ok"


def test_hemmeligheden_laves_og_genbruges(tmp_path, monkeypatch) -> None:
    """Uden en variabel laver appen selv en hemmelighed og bruger den samme igen."""
    import importlib

    import indstillinger

    importlib.reload(indstillinger)
    monkeypatch.delenv("SESSION_HEMMELIGHED", raising=False)
    monkeypatch.setenv("DATA_MAPPE", str(tmp_path / "data"))
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "data" / "app.db"))

    foerste = indstillinger.hent()
    anden = indstillinger.hent()
    assert foerste.session_hemmelighed == anden.session_hemmelighed
    assert len(foerste.session_hemmelighed) >= indstillinger.MINDSTE_LAENGDE

    fil = tmp_path / "data" / indstillinger.HEMMELIGHEDSFIL
    assert fil.is_file()
    assert oct(fil.stat().st_mode)[-3:] == "600"


def test_for_kort_hemmelighed_afvises(tmp_path, monkeypatch) -> None:
    import indstillinger

    monkeypatch.setenv("SESSION_HEMMELIGHED", "for-kort")
    monkeypatch.setenv("DATA_MAPPE", str(tmp_path / "data"))
    try:
        indstillinger.hent()
    except indstillinger.OpsaetningsFejl as fejl:
        assert "for kort" in str(fejl)
    else:
        raise AssertionError("en for kort hemmelighed skal give OpsaetningsFejl")
