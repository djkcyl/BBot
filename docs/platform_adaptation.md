# 平台适配

目前 BBot 仅适配了 QQ 平台，~~但有可能会适配其他平台~~。

## QQ

QQ 平台的推送，我们使用的是 Mirai ，并通过 mirai-api-http 插件与之连接。

详细的部署教程可查看 [graiaX 文档](https://graiax.cn/before/install_mirai.html) 进行部署，在此不多赘述。本节将会重点介绍文档中 [配置 Mirai Api Http 参数](https://graiax.cn/before/install_mirai.html#%E9%85%8D%E7%BD%AE-mirai-api-http-%E5%8F%82%E6%95%B0) 在 BBot 下如何配置。

我们先来查看一下文档中提供的默认配置、

```yaml
adapters:
  - http
  - ws
debug: false
enableVerify: true
verifyKey: GraiaxVerifyKey # 你可以自己设定，这里作为示范
singleMode: false
cacheSize: 4096
adapterSettings:
  http:
    host: localhost
    port: 8080
    cors: [*]
  ws:
    host: localhost
    port: 8080
    reservedSyncId: -1
```

由于 BBot 使用的通讯协议为 http 协议，我们仅需要在适配器中注册 http 协议即可，无需注册 ws 协议。

同时，`verify_key` 参数的设定可以需要和配置项中的 [`mirai/verify_key`](./config.md#miraiverifykey) 参数置保持一致。

`adapterSettings/http` 中的 `host` 以及 `port`，在按照 `http://host:port` 的格式拼接之后，需要与配置项中的 [`mirai/mirai_host`](./config.md#miraimirai_host) 保持一致。

例如，下方便是一个合法的 `mirai-api-http` 配置文件：

```yaml title=setting.yml
adapters:
  - http
debug: false
enableVerify: true
verifyKey: BBotVerifyKey # 需要匹配的对象
singleMode: false
cacheSize: 4096
adapterSettings:
  http:
    host: localhost # 需要匹配的对象
    port: 34986     # 需要匹配的对象
    cors: [*]
  ws:
    host: localhost # 需要匹配的对象，需要与 `http` 中的 `host` 保持一致
    port: 34986     # 需要匹配的对象，需要与 `http` 中的 `port` 保持一致
    reservedSyncId: -1
```

与之对应的 BBot 配置文件中需要匹配的参数应如下设置：

```yaml title=bot_config.yaml
mirai:
  mirai_host: http://localhost:34986 # 需要匹配的对象
  verify_key: BBotVerifyKey          # 需要匹配的对象
  account: xxxxxxx
debug:
  enable: false
  groups:
    - xxxxxxx
bilibili:
  use_login: false
  username: xxxxxxx
  password: xxxxxxx
  mobile_style: true
  concurrency: 5
event:
  mute: true
  permchange: true
name: xxxxxxx
access_control: true
master: xxxxxxx
admins:
  - xxxxxxx
```

>警告
其他配置项请参考 [配置项](./config.md) 中的介绍进行填写。
