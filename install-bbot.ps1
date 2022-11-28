$PythonVersion = "3.9" # 填写可以兼容的最低 Python 版本
$installPathName = "bbot" # 填写安装路径名，可代指 bot 的名字
$gitRepo = "https://github.com/djkcyl/BBot-Graia.git" # 填写你的 bot 的 git 仓库地址
$gitBranch = "web" # 填写仓库分支
$mainFile = "main.py" # 填写你的 bot 的主文件名

# 以下内容请不要修改
$pythonPath = "python/Scripts/python.exe"
$needClear = $args[0] -eq "--clear"
$wingetInstalled = Get-Command winget -ErrorAction SilentlyContinue
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
$pythonVersionMinor = $pythonVersion.split(".")[1]

if ($needClear) {
    Write-Host "Clearing ./$installPathName"
    Remove-Item -Path $installPathName -Recurse -Force
}

if ($PSVersionTable.PSVersion.Major -lt 5 -or $PSVersionTable.PSVersion.Minor -lt 1) {
    Write-Host "This script only supports Windows 10 or Windows Server 2019 and above." -ForegroundColor Red
    exit
}

function InstallScoop {
    Write-Host "Installing Scoop"
    Invoke-Expression "& {$(Invoke-RestMethod get.scoop.sh)} -RunAsAdmin"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}


if ($gitInstalled) {
    Write-Host "Git is already installed"
}
else {
    if ($wingetInstalled) {
        Write-Host "Installing Git with winget"
        & winget install --id Git.Git
    }
    else {
        Write-Host "Installing Git with Scoop"
        if (!(Test-Path "$env:USERPROFILE\scoop")) {
            InstallScoop
        }
        & scoop install git
    }
}

Write-Host "Cloning $gitRepo"
& git clone $gitRepo -b $gitBranch $installPathName

function CreatePythonVenv {
    & python -m venv $installPathName/python
}


$pythonInstalledVersion = $pythonInstalled.Version
if ($pythonInstalled -and $pythonInstalled.Version.Major -eq 3 -and $pythonInstalled.Version.Minor -ge $pythonVersionMinor) {
    Write-Host "Python $pythonInstalledVersion is already installed"
    CreatePythonVenv
}
else {
    if ($wingetInstalled) {
        Write-Host "Installing Python $pythonVersion with winget"
        & winget install --id Python.Python.$pythonVersion
        CreatePythonVenv
    }
    else {
        Write-Host "Installing Python $pythonVersion with Scoop"
        & scoop install python
        CreatePythonVenv
    }
}

Write-Host "Installing dependencies"
& $installPathName/$pythonPath -m pip install -r ./$installPathName/requirements.txt


$script = "`$runingProcess = Get-Process -Name 'python' -ErrorAction SilentlyContinue
if (`$runingProcess) {
    `$runingProcess | Format-Table -AutoSize
    `$choice = Read-Host -Prompt 'There are currently Python processes running, choose whether to continue? (y/n)'
    if (!(`$choice -eq 'y')) {
        exit
    }
}

function Update {
    & git pull
    & $pythonPath -m pip install -r ./requirements.txt --upgrade
}

function Uninstall {
    Remove-Item -Path ./$installPathName -Recurse -Force
}

function Start {
    & $pythonPath ./$mainFile
}

if ($args[0] -eq '--update') {
    Update
}
elseif ($args[0] -eq '--uninstall') {
    Uninstall
}
elseif ($args[0] -eq '--start') {
    Start
}
else {
    Write-Host 'Usage: ./$installPathName.ps1 [--update|--uninstall|--start]'
}"

Set-Content -Path ./$installPathName/$installPathName.ps1 -Value $script