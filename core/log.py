import sys
from pathlib import Path

from loguru import logger
from core.bot_config import BotConfig

# read log_level and verify
log_level = str(BotConfig.log_level).upper()
if log_level not in ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]:
    logger.error("log_level 未配置或配置无效，已自动调整为 INFO")
    log_level = "INFO"

# ensure logs dir exist
LOGPATH = Path("logs")
LOGPATH.mkdir(exist_ok=True)

# remove all default logger
logger.warning("开始重载 logger")
logger.remove()

# add latest logger
logger.add(
    LOGPATH.joinpath("latest.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="1 years",
    compression="tar.xz",
    colorize=False,
    level="INFO",
)

# add debug logger
logger.add(
    LOGPATH.joinpath("debug.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="15 days",
    compression="tar.xz",
    colorize=False,
    level="DEBUG",
)

# add stdout logger
logger.add(sys.stdout, backtrace=True, diagnose=True, colorize=True, level=log_level)

logger.success(f"成功重载 logger，当前日志等级为 {log_level}")

# logger.trace("TRACE 等级将会输出至控制台")
# logger.debug("DEBUG 等级将会输出至控制台")
# logger.info("INFO 等级将会输出至控制台")
# logger.success("SUCCESS 等级将会输出至控制台")
# logger.warning('WARNING 等级将会输出至控制台')
# logger.error("ERROR 等级将会输出至控制台")
# logger.critical('CRITICAL 等级将会输出至控制台')
