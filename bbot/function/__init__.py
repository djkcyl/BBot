import bbot.function.command.add_talk
import bbot.function.command.announcement
import bbot.function.command.init
import bbot.function.command.quit_group
import bbot.function.command.status
import bbot.function.command.video_resolve
import bbot.function.command.vive_dynamic
import bbot.function.command.admin.add
import bbot.function.command.admin.remove
import bbot.function.command.configure.atall
import bbot.function.command.configure.nick
import bbot.function.command.menu
import bbot.function.command.subgroup.add_up
import bbot.function.command.subgroup.add
import bbot.function.command.subgroup.get_subgroup
import bbot.function.command.subgroup.remove_up
import bbot.function.command.subgroup.remove
import bbot.function.command.up.get_subscribe
import bbot.function.command.up.subscribe
import bbot.function.command.up.unsubscribe
import bbot.function.command.vip.add
import bbot.function.command.vip.remove
import bbot.function.command.whitelist.add
import bbot.function.command.whitelist.close
import bbot.function.command.whitelist.open
import bbot.function.command.whitelist.remove
import bbot.function.command.web_auth
import bbot.function.event.bot_launch
import bbot.function.event.exception
import bbot.function.event.invited_join_group
import bbot.function.event.join_group
import bbot.function.event.leave_group
import bbot.function.event.mute
import bbot.function.event.offline
import bbot.function.event.new_friend
import bbot.function.event.prem_change
import bbot.function.pusher.init
import bbot.function.pusher.dynamic
import bbot.function.pusher.live  # noqa

# import function.scheduler.refresh_token  # noqa

from loguru import logger

logger.success("[function] 加载完成")
