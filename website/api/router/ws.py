import time
import contextlib

from loguru import logger
from fastapi import WebSocket, APIRouter
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK

from core.control import Permission

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
    connect_time = time.time()
    oauth2 = None

    try:
        while True:
            data = await websocket.receive_json()
            if oauth2:
                if data["type"] == "log":
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
                            await websocket.send_json({"type": "sys", "status": "success"})
                            logger.info("[WS] Log transfer stopped")
                        else:
                            await websocket.send_json(
                                {
                                    "type": "sys",
                                    "status": "error",
                                    "message": "Log transfer not started",
                                }
                            )
                else:
                    await websocket.send_json(
                        {"type": "sys", "status": "error", "message": "Invalid request"}
                    )
            elif time.time() - connect_time < 10:
                if time.time() - connect_time > 10:
                    await websocket.send_json({"type": "sys", "status": "error", "message": "Auth Timeout"})
                    logger.warning("[WS] Auth failed, Auth timeout")
                    return await websocket.close()
                if data.get("type", "") == "auth":
                    if data.get("token", ""):
                        try:
                            oauth2 = await verify_token(data["token"])
                            if oauth2.permission < Permission.MASTER:
                                raise UnauthorizedException(detail="Permission denied")
                            await websocket.send_json(
                                {
                                    "type": "sys",
                                    "status": "success",
                                    "message": f"Auth success, Welcome {oauth2.qq}",
                                }
                            )
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
                    else:
                        await websocket.send_json(
                            {"type": "sys", "status": "error", "message": "Invalid token"}
                        )
                        logger.warning("[WS] Auth failed, Invalid token")
                        return await websocket.close()
                else:
                    await websocket.send_json(
                        {"type": "sys", "status": "error", "message": "Auth required"}
                    )
                    logger.warning("[WS] Auth failed, Auth required")
                    return await websocket.close()
            else:
                await websocket.send_json(
                    {"type": "sys", "status": "error", "message": "Auth timeout"}
                )
                logger.warning("[WS] Auth failed, Auth timeout")
                return await websocket.close()

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
