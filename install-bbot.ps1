$pythonVersion = "3.9.13"

$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if ($gitInstalled) {
    Write-Host "Git is already installed"
}
else {
    $wingetInstalled = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetInstalled) {
        Write-Host "Installing Git with winget"
        & winget install --id Git.Git
    }
    else {
        Write-Host "Installing Git with Scoop"
        if (!(Test-Path "$env:USERPROFILE\scoop")) {
            Write-Host "Installing Scoop"
            Invoke-Expression "& {$(Invoke-RestMethod get.scoop.sh)} -RunAsAdmin"
        }
        & scoop install git
    }
}

Write-Host "Cloning BBot"
& git clone https://github.com/djkcyl/BBot-Graia.git

# 判断是否已安装 Python 3.9
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
$pythonInstalledVersion = $pythonInstalled.Version
if ($pythonInstalled -and $pythonInstalled.Version.Major -eq 3 -and ($pythonInstalled.Version.Minor -eq 9 -or $pythonInstalled.Version.Minor -eq 10)) {
    Write-Host "Python $pythonInstalledVersion is already installed"
    & python -m venv python
    $pythonPath = "python/Scripts/python.exe"
}
else {
    $pythonZip = ".\python-$pythonVersion-embed-amd64.zip"
    $pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-amd64.zip"
    Write-Host "Downloading Python $pythonVersion"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip
    Write-Host "Extracting Python $pythonVersion"
    Expand-Archive -Path $pythonZip -DestinationPath ".\python" -Force
    $pythonPath = ".\python\python.exe"
    Write-Host "Installing pip"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "get-pip.py"
    & $pythonPath ./get-pip.py
    (Get-Content -Path ./python/python39._pth -Raw) -replace "#import site", "import site" | Set-Content -Path ./python/python39._pth
    & "$pythonEmbed -m pip install --upgrade pip"
    Remove-Item -Path $pythonZip
    Remove-Item -Path ./get-pip.py
}


Write-Host "Installing dependencies"
& $pythonPath -m pip install -r ./BBot-Graia/requirements.txt


# 写入启动脚本
$script = "cd ./BBot-Graia
../$pythonPath ./main.py"
Set-Content -Path ./start-bbot.ps1 -Value $script

# 写入更新脚本
$script = "`$process = Get-Process -Name 'python' -ErrorAction SilentlyContinue
if (`$process) {
    `$process | Format-Table -AutoSize
    `$choice = Read-Host -Prompt 'There are currently Python processes running, choose whether to force close all Python processes and update? (y/n)'
    if (`$choice -eq 'y') {
        `$process | Stop-Process -Force
    }
    else {
        exit
    }
}
& cd ./BBot-Graia
& git pull
& ../$pythonPath -m pip install -r ./requirements.txt --upgrade"
Set-Content -Path ./update-bbot.ps1 -Value $script

# 写入卸载脚本
$script = "`$process = Get-Process -Name 'python' -ErrorAction SilentlyContinue
if (`$process) {
    `$process | Format-Table -AutoSize
    `$choice = Read-Host -Prompt 'There are currently Python processes running, choose whether to force close all Python processes and update? (y/n)'
    if (`$choice -eq 'y') {
        `$process | Stop-Process -Force
    }
    else {
        exit
    }
}
Remove-Item -Path ./BBot-Graia -Recurse -Force
Remove-Item -Path ./start-bbot.ps1 -Force
Remove-Item -Path ./update-bbot.ps1 -Force
Remove-Item -Path ./uninstall-bbot.ps1 -Force"
Set-Content -Path ./uninstall-bbot.ps1 -Value $script

Write-Host "Installation completed"
Write-Host "Run start-bbot.ps1 to start the bot"
Write-Host "Run update-bbot.ps1 to update the bot"
Write-Host "Run uninstall-bbot.ps1 to uninstall the bot"
