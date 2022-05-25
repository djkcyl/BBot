import time
import httpx
import base64
import urllib
import random
import hashlib

from loguru import logger
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from graia.saya import Channel, Saya
from graia.ariadne import get_running
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.broadcast.interrupt import InterruptControl

from core.bot_config import BotConfig

saya = Saya.current()
channel = Channel.current()
inc = InterruptControl(saya.broadcast)


@Waiter.create_using_function(listening_events=[FriendMessage])
async def waiter(friend: Friend, message: MessageChain):
    app = get_running(Ariadne)
    if friend.id == BotConfig.master:
        message = message.asDisplay()
        if message.isdigit():
            if len(message) == 6:
                return message
            else:
                await app.sendFriendMessage(
                    BotConfig.master,
                    MessageChain.create("请输入正确的验证码"),
                )
        else:
            await app.sendFriendMessage(
                BotConfig.master,
                MessageChain.create("请输入正确的验证码"),
            )


class bilibiliMobile:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = httpx.AsyncClient()
        self.__initialize()

    """登录函数"""

    async def login(self):
        app = get_running(Ariadne)
        # 加密
        response = await self.session.get(self.key_url)
        hash_value, public_key = (
            response.json()["data"]["hash"],
            response.json()["data"]["key"],
        )
        public_key = RSA.importKey(public_key)
        password = hash_value + self.password
        cipher = PKCS1_v1_5.new(public_key)
        password = str(
            base64.b64encode(cipher.encrypt(password.encode("utf-8"))), "utf-8"
        )
        # 模拟登录
        data = {
            "captcha": "",
            "challenge": "",
            "cookies": "",
            "password": password,
            "permission": "ALL",
            "seccode": "",
            "subid": "1",
            "username": self.username,
            "validate": "",
            "access_key": "",
            "actionKey": "appkey",
            "appkey": "783bbb7264451d82",
            "build": "6700300",
            "channel": "yingyongbao",
            "device": "phone",
            "device_name": "OnePlusKB2000",
            "device_platform": "Android12OnePlusKB2000",
            "mobi_app": "android",
            "platform": "android",
            "from_pv": "main.my-information.my-login.0.click",
            "from_url": "bilibili://user_center/mine",
            "c_locale": "zh_CN",
            "ts": str(int(time.time())),
        }
        keys = sorted(data.keys())
        data_sorted = {key: data[key] for key in keys}
        data = data_sorted
        sign = self.calcSign(data)
        data["sign"] = sign
        response = await self.session.post(
            self.login_url, data=data, headers=self.headers
        )
        response_json = response.json()
        # 判断是否存在安全风险
        if (
            "passport.bilibili.com/account/mobile/security/managephone/phone/verify"
            in response.text
        ):
            response_json = await self.loginbysms()
        # 登录成功
        if response_json["code"] == 0 and response_json["data"].get("status", 0) == 0:
            for cookie in response_json["data"]["cookie_info"]["cookies"]:
                self.session.cookies.set(
                    cookie["name"], cookie["value"], domain=".bilibili"
                )
            logger.info(f"[BiliBili推送] {self.username} 登录成功")
            infos_return = {"username": self.username}
            infos_return |= response_json
            app = get_running(Ariadne)
            await app.sendFriendMessage(
                BotConfig.master,
                MessageChain.create(f"[BiliBili推送] {self.username} 登录成功"),
            )
            return infos_return
        elif response_json["code"] == -629:
            await app.sendFriendMessage(
                BotConfig.master,
                MessageChain.create(f"[BiliBili推送] {self.username} 登录失败，账号或密码错误"),
            )
            raise RuntimeError(f"[BiliBili推送] {self.username} 登录失败，账号或密码错误")
        else:
            await app.sendFriendMessage(
                BotConfig.master,
                MessageChain.create(f"[BiliBili推送] {self.username} 登录失败，详细信息请查看日志"),
            )
            raise RuntimeError(response_json.get("data", {}))

    """计算sign值"""

    def calcSign(self, param, salt="2653583c8873dea268ab9386918b1d65"):
        param = urllib.parse.urlencode(param)
        sign = hashlib.md5(f"{param}{salt}".encode("utf-8"))
        return sign.hexdigest()

    """伪造buvid"""

    def fakebuvid(self):
        mac_list = []
        for _ in range(1, 7):
            rand_str = "".join(random.sample("0123456789abcdef", 2))
            mac_list.append(rand_str)
        rand_mac = ":".join(mac_list)
        md5 = hashlib.md5()
        md5.update(rand_mac.encode())
        md5_mac_str = md5.hexdigest()
        md5_mac = list(md5_mac_str)
        return f"XY{md5_mac[2]}{md5_mac[12]}{md5_mac[22]}{md5_mac_str}".upper()

    """通过SMS登录"""

    async def loginbysms(self) -> dict:
        default = {
            "access_key": "",
            "actionKey": "appkey",
            "appkey": "783bbb7264451d82",
            "build": "6590300",
            "channel": "yingyongbao",
            "device": "phone",
            "mobi_app": "android",
            "platform": "android",
            "ts": str(int(time.time())),
        }
        # 发送验证码
        data = {
            "cid": "86",
            "tel": self.username,
            "statistics": '{"appId":1,"platform":3,"version":"6.70.0","abtest":""}',
        }
        data, data_sorted = data | default, {}
        for key in sorted(data.keys()):
            data_sorted[key] = data[key]
        data = data_sorted
        sign = self.calcSign(data)
        data["sign"] = sign
        response = await self.session.post(self.send_url, headers=self.headers, data=data)
        # 验证登录
        if response.json()["code"] == 0:
            captcha_key = response.json()["data"]["captcha_key"]
            app = get_running(Ariadne)
            await app.sendFriendMessage(
                BotConfig.master,
                MessageChain.create("[BiliBili推送] 验证码已发送至您的手机，请在 2 分钟内完成验证"),
            )
            code = await inc.wait(waiter)
            data_sms = {
                "captcha_key": captcha_key,
                "cid": data["cid"],
                "tel": data["tel"],
                "statistics": data["statistics"],
                "code": code,
            }
            data_sms, data_sms_sorted = data_sms | default, {}
            for key in sorted(data_sms.keys()):
                data_sms_sorted[key] = data_sms[key]
            data_sms = data_sms_sorted
            sign = self.calcSign(data_sms)
            data_sms["sign"] = sign
            response = await self.session.post(
                self.sms_url, headers=self.headers, data=data_sms
            )
            # 返回
            return response.json()
        else:
            logger.error(f"[BiliBili推送] {self.username} 验证码发送失败\n{response.json()}")
            await app.sendFriendMessage(
                BotConfig.master,
                MessageChain.create(
                    f"[BiliBili推送] {self.username} 验证码发送失败，BBot 已关闭\n{response.json()}"
                ),
            )
            exit()

    """初始化"""

    def __initialize(self):  # sourcery skip: remove-unnecessary-cast
        self.login_url = "https://passport.bilibili.com/x/passport-login/oauth2/login"
        self.key_url = "https://passport.bilibili.com/x/passport-login/web/key"
        self.send_url = "https://passport.bilibili.com//x/passport-login/sms/send"
        self.sms_url = "https://passport.bilibili.com/x/passport-login/login/sms"
        self.nav_url = "https://api.bilibili.com/x/web-interface/nav"
        self.headers = {
            "env": "prod",
            "APP-KEY": "android",
            "Buvid": self.fakebuvid(),
            "Accept": "*/*",
            "Accept-Encoding": "gzip",
            "Accept-Language": "zh-cn",
            "Connection": "keep-alive",
            "User-Agent": str(
                "Mozilla/5.0 BiliDroid/6.70.0 (bbcallen@gmail.com) "
                "os/android model/KB2000 mobi_app/android build/6700300 "
                "channel/yingyongbao innerVer/6700310 osVer/12 network/2"
            ),
        }
