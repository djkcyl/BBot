import contextlib

from loguru import logger
from sentry_sdk import init as sentry_sdk_init

sentry_sdk_init(
    dsn="https://e7455ef7813c42e2b854bdd5c26adeb6@o1418272.ingest.sentry.io/6761179",
    traces_sample_rate=1.0,
)


def run_bot():

    from ..bot import app

    with contextlib.suppress(Exception):
        app.launch_blocking()
    logger.info("BBot is shut down.")
