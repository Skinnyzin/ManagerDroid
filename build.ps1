$ErrorActionPreference = "Stop"
py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --windowed --name DroidControl main.py
Write-Host ""
Write-Host "Build concluído. Executável em dist\DroidControl\DroidControl.exe"
Write-Host "Observação: mantenha DroidControl-Helper.apk ao lado do executável se o código precisar localizar esse arquivo em tempo de execução."
Write-Host "ADB/fastboot/scrcpy devem estar no PATH ou nas pastas esperadas pelo programa."
