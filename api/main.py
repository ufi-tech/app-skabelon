"""FastAPI-appen. Her hænger middleware og routere sammen, og intet andet.

RÆKKEFØLGEN BETYDER NOGET. SessionMiddleware skal være lagt på, før en rute læser
`anmodning.session`. Derfor står den her og ikke i auth.py.

Der er med vilje INGEN CORS-middleware. Browseren møder kun én adresse: nginx serverer
frontenden og sender /api videre til det her program på det samme domæne. Åbner du for
CORS, åbner du for at en fremmed side kan kalde med brugerens cookie.
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

import auth
import indhold
from indstillinger import SESSION_LEVETID_S, hent

indstillinger = hent()

app = FastAPI(
    title="site-basis",
    version="0.1.2",
    description="API til skabelonen site-basis.",
    docs_url="/api/docs" if indstillinger.er_udvikling else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if indstillinger.er_udvikling else None,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=indstillinger.session_hemmelighed,
    session_cookie="session",
    max_age=SESSION_LEVETID_S,
    same_site="lax",
    https_only=indstillinger.sikker_cookie,
)

app.include_router(auth.router)
app.include_router(indhold.router)


@app.get("/healthz")
def sundhed() -> dict[str, str]:
    """Udgivelsen poller den her adresse, før den kalder sig selv færdig."""
    return {"status": "ok", "miljoe": indstillinger.miljoe}
