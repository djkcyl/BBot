import sys
import json
import asyncio

from creart import it
from pathlib import Path
from loguru import logger
from graia.saya import Channel
from bilireq.login import Login
from grpc.aio import AioRpcError
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.broadcast.interrupt import Waiter
from graia.ariadne.message.element import Image
from bilireq.exceptions import ResponseCodeError
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.event.lifecycle import AccountLaunch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from bilireq.grpc.dynamic import grpc_get_followed_dynamic_users, grpc_get_user_dynamics

from ...utils.up_operation import delete_uid
from ...core.bot_config import BotConfig
from ...core import BOT_Status, Bili_Auth
from ...core.data import get_all_uid, delete_sub_by_uid
from ...utils.bilibili_request import relation_modify, grpc_get_followed_dynamics_noads


inc = it(InterruptControl)
channel = Channel.current()
login_cache_file = Path("data/login_cache.json")


class CodeWaiter(Waiter.create([FriendMessage], block_propagation=True)):
    async def detected_event(self, app: Ariadne, friend: Friend, message: MessageChain):
        if friend.id == BotConfig.master:
            msg = message.display
            if msg.isdigit() and len(msg) == 6:
                return int(msg)
            else:
                await app.send_friend_message(BotConfig.master, "请输入正确的验证码")


async def init_dyn_id(up_uid):
    resp = await grpc_get_user_dynamics(int(up_uid))
    if resp:
        if len(resp.list) > 0:
            if len(resp.list) == 1:
                dyn = resp.list[0]
            elif resp.list[0].modules[0].module_author.is_top:
                dyn = resp.list[1]
            else:
                dyn = resp.list[0]

            up_name = dyn.modules[0].module_author.author.name
            dyn_id = int(dyn.extend.dyn_id_str)
            BOT_Status["offset"][str(up_uid)] = dyn_id
            if dyn.modules[0].module_author.author.live.is_living == 1:
                logger.info(f"[BiliBili推送] {up_name}（{up_uid}） 已开播")
                BOT_Status["living"][str(up_uid)] = None
            logger.info(f"[BiliBili推送] UP {up_name}（{up_uid}） | {dyn_id}")
        else:
            delete_sub_by_uid(up_uid)
            logger.info(f"[BiliBili推送] UP {up_uid} 没有发布动态，已删除订阅")
    else:
        logger.warning(f"[BiliBili推送] UP {up_uid} 动态获取失败")


@channel.use(ListenerSchema(listening_events=[AccountLaunch]))
async def init(app: Ariadne):

    await asyncio.sleep(1)

    # 如果使用登录模式，则进行登录流程
    if BotConfig.Bilibili.use_login:
        logger.info("[BiliBili推送] 当前为登录模式，正在进行登录流程")
        auth_data = None
        while True:
            await asyncio.sleep(1)
            if login_cache_file.exists():
                Bili_Auth.update(json.loads(login_cache_file.read_text()))
                try:
                    auth_data = await Bili_Auth.refresh()
                    logger.success("[Bilibili推送] 缓存登录完成")
                    await app.send_friend_message(
                        BotConfig.master,
                        MessageChain("[Bilibili推送] 缓存登录完成"),
                    )
                    break
                except ResponseCodeError as e:
                    logger.error(f"[Bilibili推送] 缓存登录失败：{e}，正在重新登录")
                    await app.send_friend_message(
                        BotConfig.master,
                        MessageChain(f"[Bilibili推送] 缓存登录失败：{e}，正在重新登录"),
                    )

            bilibili_login = Login()
            # 开始登录流程
            # 尝试用户名密码登录
            try:
                auth_data = await bilibili_login.pwd_login(
                    BotConfig.Bilibili.username, BotConfig.Bilibili.password
                )
                logger.success("[Bilibili推送] 用户名密码登录完成")
                await app.send_friend_message(
                    BotConfig.master,
                    MessageChain("[Bilibili推送] 用户名密码登录完成"),
                )
            except ResponseCodeError as e:
                logger.warning(f"[BiliBili推送] 用户名密码登录失败：{e.code}，{e.msg}")
                logger.info("[BiliBili推送] 尝试使用短信验证码登录")
                try:
                    data = await bilibili_login.send_sms(BotConfig.Bilibili.username)
                    await app.send_friend_message(
                        BotConfig.master,
                        MessageChain(
                            f"[Bilibili推送] 用户名密码登录失败：{e.msg}\n正在使用验证码登录，请在 120 秒内发送验证码到此处"
                        ),
                    )
                    try:
                        code = await asyncio.wait_for(inc.wait(CodeWaiter()), timeout=120)
                        auth_data = await bilibili_login.sms_login(code)
                        logger.success("[BiliBili推送] 验证码登录完成")
                        await app.send_friend_message(
                            BotConfig.master, MessageChain("[BiliBili推送] 验证码登录完成")
                        )
                        break
                    except asyncio.TimeoutError:
                        logger.warning("[BiliBili推送] 等待输入验证码超时，如需重新登陆，请重启机器人")
                        await app.send_friend_message(
                            BotConfig.master,
                            MessageChain("[BiliBili推送] 等待输入验证码超时，如需重新登陆，请重启机器人"),
                        )
                        sys.exit(1)

                except ResponseCodeError as e:
                    logger.warning(f"[BiliBili推送] 短信验证码登录失败：{e.code}，{e.msg}")
                    logger.info("[BiliBili推送] 尝试使用二维码登录")
                    try:
                        qr_url = await bilibili_login.get_qrcode_url()
                        data = await bilibili_login.get_qrcode(qr_url)
                        await app.send_friend_message(
                            BotConfig.master,
                            MessageChain(
                                f"[BiliBili推送] 验证码登录失败：{e.msg}\n请使用 BiliBili App 扫描此二维码进行登录\n{qr_url}\n",
                                Image(data_bytes=data),
                            ),
                        )
                        auth_data = await bilibili_login.qrcode_login(interval=5)
                        logger.success("[BiliBili推送] 二维码登录完成")
                        await app.send_friend_message(
                            BotConfig.master,
                            MessageChain("[BiliBili推送] 二维码登录完成"),
                        )
                        break
                    except ResponseCodeError as e:
                        logger.error(f"[BiliBili推送] 二维码登录失败：{e.code}，{e.msg}，如需重新登陆，请重启机器人")
                        await app.send_friend_message(
                            BotConfig.master,
                            MessageChain(
                                f"[BiliBili推送] 二维码登录失败：{e.code}，{e.msg}，如需重新登陆，请重启机器人"
                            ),
                        )
                        sys.exit(1)

        logger.info("[Bilibili推送] 登录完成")
        Bili_Auth.update(auth_data)
        logger.debug(await Bili_Auth.get_info())
        login_cache_file.write_text(json.dumps(dict(Bili_Auth), indent=2, ensure_ascii=False))

        # 初始化
        subid_list = get_all_uid()
        for retry in range(3):
            try:
                resp = await grpc_get_followed_dynamic_users(auth=Bili_Auth)
                break
            except AioRpcError as e:
                logger.error(f"[Bilibili推送] 获取关注列表失败，正在重试：{e}")
                await asyncio.sleep(5)
                continue
        else:
            error_msg = "[Bilibili推送] 获取关注列表失败，重试次数过多，正在退出"
            logger.critical(error_msg)
            await app.send_friend_message(BotConfig.master, MessageChain(error_msg))
            sys.exit(1)
        followed_list = resp.items

        if Path("data").joinpath(".lock").exists():
            if Path("data").joinpath(".lock").read_text(encoding="utf-8") != str(
                BotConfig.Bilibili.username
            ):
                logger.critical(
                    "[Bilibili推送] 检测到上次登录的账号与当前账号不一致，如需继续使用，请先手动删除数据库（data/data.db）和 data/.lock 文件"
                )
                sys.exit(1)

        elif (f := len(followed_list)) != 0:
            if sys.argv.pop() != "--ignore-sub":
                logger.critical(
                    f"[Bilibili推送] 该账号已关注 {f} 个用户，为避免产生问题，已停止运行，请先手动取消关注或添加启动参数 --ignore-sub，这将取关所有已关注的用户"
                )
                sys.exit(1)
            else:
                logger.warning(f"[Bilibili推送] 该账号已关注 {f} 个用户，正在尝试自动处理")
                Path("data").joinpath(".lock").write_text(str(BotConfig.Bilibili.username))
        else:
            Path("data").joinpath(".lock").write_text(str(BotConfig.Bilibili.username))

        # 检测在B站关注列表但不在数据库的uid
        if followed_list:
            for uid in followed_list:
                if str(uid.uid) not in subid_list:
                    logger.warning(
                        f"[BiliBili推送] {uid.name}（{uid.uid}）在 BliBili 关注列表中，但不在数据库中，正在从 BliBili 取消关注"
                    )
                    resp = await delete_uid(uid.uid)
                    if resp:
                        await app.send_friend_message(
                            BotConfig.master,
                            MessageChain(
                                f"[BiliBili推送] {uid.name}（{uid.uid}）在 BliBili 关注列表中，但不在数据库中，正在从 BliBili 取消关注"
                            ),
                        )
                        await asyncio.sleep(1)
                        continue
                    else:
                        logger.error(
                            f"[BiliBili推送] {uid.name}（{uid.uid}）从 BliBili 取消关注失败，请检查后重启 Bot"
                        )
                        sys.exit(1)

                # 顺便检测直播状态
                if uid.live_info.status:
                    logger.info(f"[BiliBili推送] {uid.name} 已开播")
                    BOT_Status["living"][str(uid.uid)] = None

        # 检测在数据库但不在B站关注列表的uid
        for up in subid_list:
            for uid in followed_list:
                if up == str(uid.uid):
                    break
            else:
                logger.warning(f"[BiliBili推送] {up} 不在 BliBili 关注列表中，正在修复")
                resp = await relation_modify(up, 1)
                if resp["code"] != 0:
                    await delete_uid(up)
                    logger.error(f"[BiliBili推送] {up} BliBili 订阅修复失败，请检查后重启 Bot：{resp}")
                    await app.send_friend_message(
                        BotConfig.master,
                        MessageChain(f"[BiliBili推送] UP {up} BliBili 订阅修复失败，请检查后重启 Bot：{resp}"),
                    )
                    sys.exit(1)
                else:
                    logger.info(f"[BiliBili推送] {up} BliBili 订阅修复成功")
                await asyncio.sleep(1)

        logger.info(f"[BiliBili推送] 直播初始化完成，当前 {len(BOT_Status['living'])} 个 UP 正在直播")

        # 动态初始化
        sub_num = len(subid_list)
        if sub_num == 0:
            await asyncio.sleep(1)
            logger.success("[BiliBili推送] 未订阅任何 UP ，初始化结束")
            BOT_Status["init"] = True
            return
        await asyncio.sleep(1)

        if resp := await grpc_get_followed_dynamics_noads():
            BOT_Status["offset"] = int(resp[-1].extend.dyn_id_str)
            logger.info(f"[BiliBili推送] 动态初始化完成，offset：{BOT_Status['offset']}")

            logger.success(f"[BiliBili推送] 将对 {sub_num} 个 UP 进行监控，初始化完成")
            await asyncio.sleep(1)
            await app.send_friend_message(
                BotConfig.master,
                MessageChain(f"[BiliBili推送] 将对 {sub_num} 个 UP 进行监控，初始化完成"),
            )
            BOT_Status["init"] = True
            BOT_Status["started"] = True

    else:
        logger.info("[BiliBili推送] 未使用登录模式，正在初始化")
        subid_list = get_all_uid()
        sub_sum = len(subid_list)
        BOT_Status["offset"] = {}
        if sub_sum == 0:
            await asyncio.sleep(1)
            logger.success("[BiliBili推送] 未订阅任何 UP ，初始化结束")
            BOT_Status["init"] = True
            return
        # 把所有账号分组，每组发送一次请求
        group_list = [
            subid_list[i : i + BotConfig.Bilibili.concurrency]
            for i in range(0, sub_sum, BotConfig.Bilibili.concurrency)
        ]
        logger.debug(f"Get {sub_sum} uid, split to {len(group_list)} groups")
        for group in group_list:
            logger.debug(f"Gathering {len(group)} uid")
            await asyncio.gather(*[init_dyn_id(uid) for uid in group])
        logger.success(f"[BiliBili推送] 将对 {sub_sum} 个 UP 进行监控，初始化完成")
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(f"[BiliBili推送] 将对 {sub_sum} 个 UP 进行监控，初始化完成"),
        )
        BOT_Status["init"] = True
        BOT_Status["started"] = True
