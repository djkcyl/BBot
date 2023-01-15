from fastapi import APIRouter

from . import user, ws, auth, follow, home, config

router = APIRouter()

router.include_router(user.router, prefix="/user")
router.include_router(ws.router, prefix="/ws")
router.include_router(auth.router, prefix="/auth")
router.include_router(follow.router, prefix="/follow")
router.include_router(home.router, prefix="/home")
router.include_router(config.router, prefix="/config")
