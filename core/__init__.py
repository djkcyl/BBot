from typing import Optional
from bilireq.auth import Auth

from core.bot_config import BotConfig

BOT_Status = {
    "living": {},
    "offset": None,
    "init": False,
    "dynamic_updating": False,
    "live_updating": False,
}

Bili_Auth = Auth()
Bot_Config = BotConfig
