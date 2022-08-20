# 配置项

通常情况下，配置项位于项目根目录的 `data` 文件夹下，名为 `bot_config.yaml`。

在未能成功找到配置文件的情况下，程序将会以 `bot_config.exp.yaml` 为模板创建一个新的配置文件并退出，你也可以通过手动复制该文件并重命名为 `bot_config.yaml` 来创建配置文件。

默认的配置项包含如下内容。

```yaml
mirai:
  mirai_host: http://xxxxxxx:xxxx
  verify_key: xxxxxxx
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

## mirai

与 `mirai-api-http` 的连接设定，可参考 [平台适配 - QQ](./platform_adaptation.md#qq) 进行设置。

### mirai/mirai_host

- **类型**: `str`
- **默认值**: `http://xxxxxxx:xxxx`

`mirai-api-http` 的监听地址，需要与 `mirai-api-http` 的配置保持一致。

### mirai/verify_key

- **类型**: `str`
- **默认值**: `xxxxxxx`

`mirai-api-http` 的连接密钥，需要与 `mirai-api-http` 的配置保持一致。

### mirai/account

- **类型**: `int`
- **默认值**: `xxxxxxx`

略

## debug

debug 相关设置。

### debug/enable

- **类型**: `bool`
- **默认值**: `false`

是否开启 `debug` 模式。

### debug/groups

- **类型**: `set[int]`
- **默认值**: `[xxxxxxx]`

开启 `debug` 模式的群。

## bilibili

bilibili 相关设置。

### bilibili/use_login

- **类型**: `bool`
- **默认值**: `false`

用户是否登录，若为 `false` 则 `username` 与 `password` 将被忽略，若为 `true` 将会尝试使用 `username` 与 `password` 进行登录。

### bilibili/username

- **类型**: `int`
- **默认值**: `xxxxxxx`

bilibili 用户名，若 `use_login` 为 `false` 将被忽略

### bilibili/password

- **类型**: `str`
- **默认值**: `xxxxxxx`

bilibili 密码，若 `use_login` 为 `false` 将被忽略

### bilibili/mobile_style

- **类型**: `bool`
- **默认值**: `true`

是否采用手机模式进行渲染。

### bilibili/concurrency

- **类型**: `int`
- **默认值**: `5`
