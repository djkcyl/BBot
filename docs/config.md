# 配置项

通常情况下，配置项位于项目根目录的 `data` 文件夹下，名为 `bot_config.yaml`。

在未能成功找到配置文件的情况下，程序将会以 `bot_config.exp.yaml` 为模板创建一个新的配置文件并退出，你也可以通过手动复制该文件并重命名为 `bot_config.yaml` 来创建配置文件。

默认的配置项包含如下内容。

```yaml
Mirai:
  mirai_host:        # **需要** 填入 mirai-api-http 的监听地址
  verify_key:        # **需要** 填入 mirai 的密钥
  account:           # **需要** 填入 bot 的 qq 号
Debug:
  enable: false      # 是否开启 debug
  groups:            # 若开启 debug 则 **需要** 填入群号, list 和 int 均可
Bilibili:
  use_login: false   # 是否登录 BiliBili 账号
  username:          # 若登录 BiliBili 账号, 则 **需要** 填入账号
  password:          # 若登录 BiliBili 账号, 则 **需要** 填入密码
  mobile_style: true # 是否采用手机的 Web 样式进行渲染
  concurrency: 5     # 未登录时发送 gRPC 请求的并发数量(1 ~ 50)
Event:
  mute: true         # 是否向管理员发送被禁言的事件提醒。
  permchange: true   # 是否向管理员发送权限变更的事件提醒。
log_level: INFO      # 控制台输出的日志等级
name: BBot           # bot 的自称
access_control: true # 是否开启白名单模式
master:              # **需要** 填入 bot 主人的 qq 号
admins:              # 可以填入 bot 管理员的 qq 号, list 和 int 均可
```

>Warning
v0.3.0 及之前的版本的配置文件可自动向后兼容，但不支持自动向前兼容。若需要降级使用，可手动将 `Mirai`、`Debug`、`Bilibili`、`Event` 替换为 `mirai`、`debug`、`bilibili`、`event`。

## Mirai

与 `mirai-api-http` 的连接设定，可参考 [平台适配 - QQ](./platform_adaptation.md#qq) 进行设置。

### Mirai/mirai_host

- **类型**: `str`
- **默认值**: `无`

`mirai-api-http` 的监听地址，需要与 `mirai-api-http` 的配置保持一致。

### Mirai/verify_key

- **类型**: `str`
- **默认值**: `无`

`mirai-api-http` 的连接密钥，需要与 `mirai-api-http` 的配置保持一致。

### Mirai/account

- **类型**: `int`
- **默认值**: `无`

需要绑定的登录于 `mirai-api-http` 的 QQ 号。

## Debug

debug 相关设置。

### Debug/enable

- **类型**: `bool`
- **默认值**: `false`

是否开启 `debug` 模式。

### Debug/groups

- **类型**: `list[int] | int`
- **默认值**: `无`

开启 `debug` 模式的群。

## Bilibili

BiliBili 相关设置。

### Bilibili/use_login

- **类型**: `bool`
- **默认值**: `false`

是否登录 BiliBili 账号，若为 `false` 则 `username` 与 `password` 将被忽略，若为 `true` 将会尝试使用 `username` 与 `password` 进行登录。

### Bilibili/username

- **类型**: `int`
- **默认值**: `无`

BiliBili 用户名，若 `use_login` 为 `false` 将被忽略。

### Bilibili/password

- **类型**: `str`
- **默认值**: `无`

BiliBili 密码，若 `use_login` 为 `false` 将被忽略。

### Bilibili/mobile_style

- **类型**: `bool`
- **默认值**: `true`

是否采用手机的 Web 样式进行渲染。

### Bilibili/concurrency

- **类型**: `int`
- **默认值**: `5`

BiliBili 账号未登录的情况下发送 gRPC 请求的并发数量（1 ~ 50）。

## Event

事件配置

### Event/mute

- **类型**: `bool`
- **默认值**: `true`

是否向管理员发送被禁言的事件提醒。

### Event/permchange

- **类型**: `bool`
- **默认值**: `true`

是否向管理员发送权限变更的事件提醒。

## log_level

- **类型**: `str`
- **默认值**: `INFO`

控制台输出的日志等级，可选等级包含 `TRACE` `DEBUG` `INFO` `SUCCESS` `WARNING` `ERROR` `CRITICAL`，可参考 [loguru 官方文档](https://loguru.readthedocs.io/) 以获取更多信息。

## name

- **类型**: `str`
- **默认值**: `BBot`

BBot 在群内自称的名称。

## access_control

- **类型**: `bool`
- **默认值**: `true`

权限控制，开启后将增加对群的白名单控制，BBot 将不在同意非白名单群的入群邀请。

## master

- **类型**: `int`
- **默认值**: `xxxxxxx`

主人 QQ 号。

## admins

- **类型**: `list[int]`
- **默认值**: `[xxxxxxx]`

管理员 QQ 号列表。

## max_subsubscribe

- **类型**: `int`
- **默认值**: `4`

非 vip 群聊最大可订阅数量，设置为 0 时将无法订阅 up 主。
