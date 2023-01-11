#!/bin/bash

pythonVersion=3.9
pythonFullVersion=3.9.15
installPath=./bbot
name=bbot
gitRepo=https://github.com/djkcyl/BBot-Graia.git
gitBranch=web
mainFile=main.py

pythonPath=python/bin/python

if [ -z "$BASH_VERSION" ]; then
    echo "请使用 bash 执行此脚本"
    exit 1
fi

pythonIsRunning() {
    if [ -z "$(ps -ef | grep -v grep | grep -i python)" ]; then
        return 1
    else
        return 0
    fi
}

if pythonIsRunning; then
    read -p "检测到系统内有其他 python 正在运行，是否继续？[y/N] " -r
    if [[ $REPLY =~ [Yy] ]]; then
        echo "正在继续"
    else
        echo "安装终止"
        exit 1
    fi
fi

if [[ $* == *--clear* ]]; then
    rm -rf ./bbot
fi

if [ -d "./bbot" ]; then
    read -p "检测到已存在 bbot，是否删除？[y/N] " -r
    if [[ $REPLY =~ [Yy] ]]; then
        echo "正在删除已存在的 bbot"
        rm -rf ./bbot
    else
        echo "安装终止"
        exit 1
    fi
fi

if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        echo "此脚本仅支持 Ubuntu 系统"
        exit 1
    fi
else
    echo "此脚本仅支持 Ubuntu 系统"
    exit 1
fi

deactivate 2>/dev/null

if ! command -v python3.9 &>/dev/null; then
    if ! command -v python3.10 &>/dev/null; then
        echo "未检测到 python3.9 或 python3.10"
        echo "正在安装 python3.9"
        sudo apt update
        sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev
        wget https://www.python.org/ftp/python/$pythonFullVersion/Python-$pythonFullVersion.tgz
        tar -xf Python-$pythonFullVersion.tgz
        cd Python-$pythonFullVersion
        ./configure --enable-optimizations
        sudo make -j $(nproc)
        sudo make altinstall
        cd ..
        rm -rf Python-$pythonFullVersion.tgz Python-$pythonFullVersion
        echo "python$pythonFullVersion 安装完成"
    else
        echo "检测到已安装 python3.10"
        pythonVersion=3.10
        pythonFullVersion=3.10.0
    fi
else
    echo "检测到已安装 python3.9"
fi

# 检测是否安装了 git
if ! command -v git &>/dev/null; then
    echo "未检测到 git"
    echo "正在安装 git"
    sudo apt install -y git
fi

git clone -b $gitBranch $gitRepo $installPath
cd $installPath

# 创建虚拟环境
echo "正在创建虚拟环境"
python$pythonVersion -m venv python
# 如果报错，尝试使用下面的命令
if [ $? -ne 0 ]; then
    sudo apt install -y python$pythonVersion-venv
    python$pythonVersion -m venv python
fi

# 安装依赖
echo "正在安装依赖"
$pythonPath -m pip install -r requirements.txt

# 创建使用脚本
echo "正在创建使用脚本"
cat >$name.sh <<EOF
#!/bin/bash
if [ -z "\$BASH_VERSION" ]; then
    echo "请使用 bash 执行此脚本"
    exit 1
fi

pythonIsRunning() {
    if [ -z "$(ps -ef | grep -v grep | grep -i python)" ]; then
        return 1
    else
        return 0
    fi
}

if pythonIsRunning; then
    read -p "检测到系统内有其他 python 正在运行，是否继续？[y/N] " -r
    if [[ \$REPLY =~ [Yy] ]]; then
        echo "正在继续"
    else
        echo "安装终止"
        exit 1
    fi
fi


if [ "\$1" == "start" ]; then
    python/bin/python main.py
elif [ "\$1" == "update" ]; then
    echo "正在更新 bbot"
    git pull
    python/bin/python -m pip install -r requirements.txt --upgrade
    echo "bbot 更新完成"
elif [ "\$1" == "uninstall" ]; then
    cd ..
    rm -rf ./bbot
    echo "卸载完成"
else
    echo "参数错误，用法：./bbot.sh [start|update|uninstall]"
fi


EOF
chmod +x $name.sh
chown -R $USER:$USER ../$installPath

echo "已将 $name 安装到 $(pwd)"
echo "使用方法：./$name.sh [start|update|uninstall]"
