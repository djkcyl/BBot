import aunly_bbot.function.command.add_talk
import aunly_bbot.function.command.announcement
import aunly_bbot.function.command.init
import aunly_bbot.function.command.quit_group
import aunly_bbot.function.command.status
import aunly_bbot.function.command.video_resolve
import aunly_bbot.function.command.vive_dynamic
import aunly_bbot.function.command.admin.add
import aunly_bbot.function.command.admin.remove
import aunly_bbot.function.command.configure.atall
import aunly_bbot.function.command.configure.nick
import aunly_bbot.function.command.menu
import aunly_bbot.function.command.subgroup.add_up
import aunly_bbot.function.command.subgroup.add
import aunly_bbot.function.command.subgroup.get_subgroup
import aunly_bbot.function.command.subgroup.remove_up
import aunly_bbot.function.command.subgroup.remove
import aunly_bbot.function.command.up.get_subscribe
import aunly_bbot.function.command.up.subscribe
import aunly_bbot.function.command.up.unsubscribe
import aunly_bbot.function.command.vip.add
import aunly_bbot.function.command.vip.remove
import aunly_bbot.function.command.whitelist.add
import aunly_bbot.function.command.whitelist.close
import aunly_bbot.function.command.whitelist.open
import aunly_bbot.function.command.whitelist.remove
import aunly_bbot.function.command.web_auth
import aunly_bbot.function.event.bot_launch
import aunly_bbot.function.event.exception
import aunly_bbot.function.event.invited_join_group
import aunly_bbot.function.event.join_group
import aunly_bbot.function.event.leave_group
import aunly_bbot.function.event.mute
import aunly_bbot.function.event.offline
import aunly_bbot.function.event.new_friend
import aunly_bbot.function.event.prem_change
import aunly_bbot.function.pusher.init
import aunly_bbot.function.pusher.dynamic
import aunly_bbot.function.pusher.live
import aunly_bbot.function.scheduler.version_update  # noqa

# import function.scheduler.refresh_token  # noqa

from loguru import logger

logger.success("[function] 加载完成")
