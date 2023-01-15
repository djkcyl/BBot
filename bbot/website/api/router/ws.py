import contextlib

from loguru import logger
from fastapi import WebSocket, APIRouter
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK

from ....core.control import Permission
from .auth import verify_token, UnauthorizedException


router = APIRouter(tags=["Logs"])


@router.websocket("/logs", name="logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def log_handler(message: str):
        try:
            await websocket.send_json({"type": "log", "message": message})
        except Exception:
            with contextlib.suppress():
                await websocket.close()

    log = None
    log_level = None

    try:
        while True:
            data = await websocket.receive_json()
            if data["token"] is None:
                raise UnauthorizedException
            try:
                oauth2 = await verify_token(data["token"])
                if oauth2.permission < Permission.MASTER:
                    raise UnauthorizedException(detail="Permission denied")
                logger.info(f"[WS] Auth success, {oauth2.qq}")
            except UnauthorizedException as e:
                await websocket.send_json(
                    {
                        "type": "sys",
                        "status": "error",
                        "message": e.detail,
                    }
                )
                logger.warning("[WS] Auth failed, Permission denied")
                return await websocket.close()
            if data.get("status", "") == "start":
                if (level := data.get("level", "").upper()) in [
                    "DEBUG",
                    "INFO",
                    "WARNING",
                    "ERROR",
                    "CRITICAL",
                ]:
                    if log_level != level:
                        if log:
                            logger.remove(log)
                        log = logger.add(log_handler, level=level, colorize=False)
                        await websocket.send_json(
                            {"type": "sys", "status": "success", "level": level}
                        )
                        logger.info(f"[WS] Log transfer started, level: {level}")
                    else:
                        await websocket.send_json(
                            {
                                "type": "sys",
                                "status": "ignore",
                                "message": f"Log level is already {level}",
                            }
                        )
                else:
                    logger.warning(f"[WS] Invalid log level {level}")
                    await websocket.send_json(
                        {
                            "type": "sys",
                            "status": "error",
                            "message": "Invalid log level",
                        }
                    )
            elif data.get("status", "") == "stop":
                if log:
                    logger.remove(log)
                    log = None
                    await websocket.send_json(
                        {"type": "sys", "status": "success", "message": "Log transfer stopped"}
                    )
                    logger.info("[WS] Log transfer stopped")
                else:
                    await websocket.send_json(
                        {
                            "type": "sys",
                            "status": "error",
                            "message": "Log transfer not started",
                        }
                    )

    except (WebSocketDisconnect, ConnectionClosedOK):
        pass
    except Exception as e:
        with contextlib.suppress():
            await websocket.send_json({"type": "sys", "status": "error", "message": str(e)})
        with contextlib.suppress():
            await websocket.close()
        logger.error(e)
    if log:
        logger.remove(log)
