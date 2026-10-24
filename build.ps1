$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$icon = "icone.ico"
if (-not (Test-Path $icon)) { throw "Arquivo $icon não encontrado na pasta do projeto." }

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller

# --onefile: um único .exe, sem pasta _internal
# --windowed: sem janela de console | --icon: ícone do .exe | --add-data: .ico embutido (ícone da janela)
py -m PyInstaller --noconfirm --clean --onefile --windowed --name ManagerDroid `
    --icon $icon --add-data "$icon;." --add-data "android_fallback.png;." main.py

Write-Host ""
Write-Host "Build concluído. Executável em dist\ManagerDroid.exe"
Write-Host "O ADB e o scrcpy são baixados automaticamente na primeira vez que forem necessários."
