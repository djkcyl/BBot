from graia.saya import Channel
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from ...core.data import add_talk_count

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def main():

    add_talk_count()
