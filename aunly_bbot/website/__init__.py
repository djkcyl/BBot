from pathlib import Path
from typing import Union
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from launart import Launchable, ExportInterface, Launart
from graia.amnesia.transport.common.asgi import ASGIHandlerProvider

from .api.router import router

STATIC_PATH = Path(__file__).parent.joinpath("static")


async def root():
    return FileResponse(STATIC_PATH.joinpath("html", "index.html"))


async def status():
    return {"status": "ok"}


class BotWebService(Launchable):
    id: str = "webapi/bbot"

    @property
    def required(self) -> set[Union[str, type[ExportInterface]]]:
        return {ASGIHandlerProvider}

    @property
    def stages(self):
        return {"preparing"}

    async def launch(self, launart: Launart):
        async with self.stage("preparing"):
            app: FastAPI = launart.get_interface(ASGIHandlerProvider).get_asgi_handler()
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            app.include_router(router, prefix="/api")
            app.get("/api/status")(status)
            app.get("/")(root)
            app.mount(
                "/",
                StaticFiles(directory=STATIC_PATH.joinpath("html")),
                name="static",
            )
