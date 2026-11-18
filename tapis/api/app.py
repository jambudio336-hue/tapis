from .routes import audio, chain as chain_r, events, intel, radius as radius_r, targets, warrants, ws
...
for r in (targets.router, warrants.router, events.router, audio.router,
          intel.router, radius_r.router, chain_r.router, ws.router):

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .. import __version__, db
from .routes import audio, chain as chain_r, events, intel, targets, warrants, ws

WEB = Path(__file__).resolve().parent.parent / "web"


def buat_app() -> FastAPI:
    db.init_db()
    app = FastAPI(title="TAPIS", version=__version__, docs_url="/api/docs")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    for r in (targets.router, warrants.router, events.router, audio.router, intel.router, chain_r.router, ws.router):
        app.include_router(r, prefix="/api/v1")
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
    return app


app = buat_app()
