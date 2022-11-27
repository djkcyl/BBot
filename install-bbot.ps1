$pythonVersion = "3.9"
$installPathName = "bbot"
$gitRepo = "https://github.com/djkcyl/BBot-Graia.git"
$gitBranch = "web"
$mainFile = "main.py"


$pythonPath = "python/Scripts/python.exe"
$needClear = $args[0] -eq "--clear"
$wingetInstalled = Get-Command winget -ErrorAction SilentlyContinue
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue

if ($needClear) {
    Write-Host "Clearing ./$installPathName"
    Remove-Item -Path $installPathName -Recurse -Force
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
if ($pythonInstalled -and $pythonInstalled.Version.Major -eq 3 -and ($pythonInstalled.Version.Minor -eq 9 -or $pythonInstalled.Version.Minor -eq 10)) {
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
        & scoop install python@$pythonVersion
        CreatePythonVenv
    }
}

Write-Host "Installing dependencies"
& $installPathName/$pythonPath -m pip install -r ./$installPathName/requirements.txt


$script = "Set-Location ./$installPathName
$pythonPath ./$mainFile
Set-Location .."
Set-Content -Path "./start-$installPathName.ps1" -Value $script

$script = "`$process = Get-Process -Name 'python' -ErrorAction SilentlyContinue
if (`$process) {
    `$process | Format-Table -AutoSize
    `$choice = Read-Host -Prompt 'There are currently Python processes running, choose whether to force an update? (y/n)'
    if !(`$choice -eq 'y') {
        exit
    }
}
& Set-Location ./$installPathName
& git pull
& $pythonPath -m pip install -r ./requirements.txt --upgrade
Set-Location .."
Set-Content -Path "./update-$installPathName.ps1" -Value $script

$script = "`$process = Get-Process -Name 'python' -ErrorAction SilentlyContinue
if (`$process) {
    `$process | Format-Table -AutoSize
    `$choice = Read-Host -Prompt 'There are currently Python processes running, choose whether to force an update? (y/n)'
    if !(`$choice -eq 'y') {
        exit
    }
}
Remove-Item -Path ./$installPathName -Recurse -Force
Remove-Item -Path ./start-$installPathName.ps1 -Force
Remove-Item -Path ./update-$installPathName.ps1 -Force
Remove-Item -Path ./uninstall-$installPathName.ps1 -Force"
Set-Content -Path "./uninstall-$installPathName.ps1" -Value $script

Write-Host "Installation completed"
Write-Host "Run start-$installPathName.ps1 to start the $installPathName"
Write-Host "Run update-$installPathName.ps1 to update the $installPathName"
Write-Host "Run uninstall-$installPathName.ps1 to uninstall the $installPathName"
