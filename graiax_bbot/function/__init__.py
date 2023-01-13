import graiax_bbot.function.command.add_talk
import graiax_bbot.function.command.announcement
import graiax_bbot.function.command.init
import graiax_bbot.function.command.quit_group
import graiax_bbot.function.command.status
import graiax_bbot.function.command.video_resolve
import graiax_bbot.function.command.vive_dynamic
import graiax_bbot.function.command.admin.add
import graiax_bbot.function.command.admin.remove
import graiax_bbot.function.command.configure.atall
import graiax_bbot.function.command.configure.nick
import graiax_bbot.function.command.menu
import graiax_bbot.function.command.subgroup.add_up
import graiax_bbot.function.command.subgroup.add
import graiax_bbot.function.command.subgroup.get_subgroup
import graiax_bbot.function.command.subgroup.remove_up
import graiax_bbot.function.command.subgroup.remove
import graiax_bbot.function.command.up.get_subscribe
import graiax_bbot.function.command.up.subscribe
import graiax_bbot.function.command.up.unsubscribe
import graiax_bbot.function.command.vip.add
import graiax_bbot.function.command.vip.remove
import graiax_bbot.function.command.whitelist.add
import graiax_bbot.function.command.whitelist.close
import graiax_bbot.function.command.whitelist.open
import graiax_bbot.function.command.whitelist.remove
import graiax_bbot.function.command.web_auth
import graiax_bbot.function.event.bot_launch
import graiax_bbot.function.event.exception
import graiax_bbot.function.event.invited_join_group
import graiax_bbot.function.event.join_group
import graiax_bbot.function.event.leave_group
import graiax_bbot.function.event.mute
import graiax_bbot.function.event.offline
import graiax_bbot.function.event.new_friend
import graiax_bbot.function.event.prem_change
import graiax_bbot.function.pusher.init
import graiax_bbot.function.pusher.dynamic
import graiax_bbot.function.pusher.live  # noqa

# import function.scheduler.refresh_token  # noqa

from loguru import logger

logger.success("[function] 加载完成")
