$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$icon = "icone.ico"
if (-not (Test-Path $icon)) { throw "Arquivo $icon não encontrado na pasta do projeto." }

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller

# --icon: ícone do .exe | --add-data: inclui o .ico dentro do programa (ícone da janela)
py -m PyInstaller --noconfirm --clean --windowed --name ManagerDroid `
    --icon $icon --add-data "$icon;." main.py

Write-Host ""
Write-Host "Build concluído. Executável em dist\ManagerDroid\ManagerDroid.exe"
Write-Host "O ADB e o scrcpy são baixados automaticamente na primeira vez que forem necessários."
