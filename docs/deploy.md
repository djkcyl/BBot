# 部署 BBot

在部署之前，你需要知道以下两点：

- 本项目仅在 Ubuntu20.04LTS 及 Windows10 平台上进行测试，如果在使用其他平台时出现兼容性问题，请自行更换平台或为项目提交贡献进行适配。
- 仅凭 BBot 是无法完成消息推送的，BBot 需要对应平台的无头客户端或API才可正常工作！详情请参考 [平台适配](./platform_adaptation.md) 进行配置。

## 使用二进制包（推荐）

如果你不需要对项目源码进行任何修改，同时使用项目推荐的平台，那么你可以使用 [releases](https://github.com/djkcyl/BBot-Graia/releases) 中发布的二进制包进行部署。

如果您决定使用此方法，可在下载二进制包后跳转至 [运行BBot](#运行BBot) 继续。

## 使用源码部署

如果你在项目推荐的平台上无法正常部署，请尝试二进制包版进行验证。若二进制包可以正常工作，那么大概率是你的部署流程上出现了问题。若二进制包无法正常工作，那么大概率是部署平台出现了问题，请考虑重装系统或修复平台。

### 安装python

>警告
该项目需求 Python >= 3.9 ，请确保你所使用的平台兼容该版本的 python。

Windows 用户可前往 [python官方网站](https://www.python.org/downloads/windows/) 下载对应平台的的安装包，并进行安装（注意添加至环境变量）。

Linux 用户可直接通过对应平台的包管理工具进行安装，例如 `apt install python3.9`。

### 获取源码

#### 使用git获取（推荐）

我们推荐使用 git 来获取源码，这将很大程度上便于项目的更新以及后续维护。

Windows 用户可前往 [git官方网站](https://git-scm.com/download/win) 下载 git 并安装（注意添加至环境变量）。

Linux 用户可使用对应平台的包管理工具进行安装，可参考 [git官方网站](https://git-scm.com/download/linux)。

在 git 安装完成后，使用 `git clone https://github.com/djkcyl/BBot-Graia.git` 下载项目。

#### 使用其他方式获取

我们可以使用其他方式来获取源码。

### 安装依赖

本项目使用 [poetry](https://python-poetry.org/) 虚拟环境对项目的环境进行管理。

首先，请参考 [poetry官方文档](https://python-poetry.org/docs/#installation) 安装 poetry。

在**项目的根目录**中，使用 `poetry install` 进行虚拟环境的创建及依赖的获取。

>提示
我们可以在虚拟环境创建前使用 `poetry config virtualenvs.in-project true` 命令将虚拟环境创建至项目根目录。

取决于您的网络或其他因素，该过程可能会消耗较长时间，请耐心等待。

## 运行 BBot

如果您使用的是二进制包，可直接在项目目录下运行该文件。Windows 用户可以直接双击运行，ubuntu用户可以在控制台输入 `./bbot-ubuntu-版本号` 例如 `./bbot-ubuntu-0.3.0` 以运行（注意，此文件需要可执行权限才可直接运行，可使用 `chmod` 指令来更改文件的访问权限）。

源码用户可以使用 `poetry run python main.py` 指令来使用虚拟环境运行。

在运行 BBot 后，程序会首先寻找配置文件，如果未能找到将会创建一个新的配置文件并退出，请查看 [配置项](./config.md) 对配置项进行填写后再次运行。

同时，你也需要部署对应的平台适配来帮助 BBot 讲消息发送到对应平台，例如使用 mah 将消息推送到 QQ。请查看 [平台适配](./platform_adaptation.md) 进行对应平台适配器的部署。
