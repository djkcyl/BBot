from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.console.saya import ConsoleSchema
from graia.ariadne.message.parser.twilight import FullMatch, Twilight

channel = Channel.current()


@channel.use(ConsoleSchema(dispatchers=[Twilight([FullMatch("stop")])]))
async def stop(app: Ariadne, console: Console):
    await app.stop()
    console.stop()
