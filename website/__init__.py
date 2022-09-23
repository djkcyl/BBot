from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from launart import Launchable, ExportInterface, Launart
from graia.amnesia.transport.common.asgi import ASGIHandlerProvider

from .api.router import router


async def root():
    return {"message": "Hello World"}


class BotService(Launchable):
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
            app.get("/", tags=["Hello World"])(root)
            app.include_router(router, prefix="/api")
