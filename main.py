"""
DroidControl — gerenciador Android para Windows 10/11 (PT/EN).
Requer Android Platform Tools (adb/fastboot) e, opcionalmente, scrcpy.
"""
from __future__ import annotations
import os, re, sys, json, shutil, subprocess, tempfile, zipfile, threading, time, functools, urllib.request
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal, QSize, QByteArray, QTimer, QObject
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QGuiApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QLineEdit, QPlainTextEdit, QCheckBox, QProgressBar, QFrame,
    QSpinBox, QHeaderView, QAbstractItemView, QScrollArea, QListWidget,
    QListWidgetItem, QStackedWidget, QMenu, QDialog, QDialogButtonBox
)

APP_NAME = "DroidControl"
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DATA_DIR = Path(__file__).resolve().parent
LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "droidcontrol.log"
CACHE_DIR = DATA_DIR / "cache"
LABEL_CACHE = CACHE_DIR / "app_labels.json"
ICON_CACHE = CACHE_DIR / "icons"
SETTINGS_FILE = CACHE_DIR / "settings.json"
CACHE_VERSION = 4
APP_VERSION = "20"
HELPER_PKG = "com.droidcontrol.helper"
HELPER_ACTION = "com.droidcontrol.helper.EXPORT"
HELPER_REMOTE = "/sdcard/DroidControl"

# ---------------------------------------------------------------- ícones SVG (embutidos)
ICON_SVGS = {
    'mobile': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M288-48q-29.7 0-50.85-21.15Q216-90.3 216-120v-720q0-33 19.5-52.5T288-912h384q29.7 0 50.85 21.15Q744-869.7 744-840v144q20 0 34 14t14 34v96q0 20-14 34t-34 14v384q0 29.7-21.15 50.85Q701.7-48 672-48H288Zm0-72h384v-720H288v720Zm0 0v-720 720Zm217.5-610.29q10.5-10.29 10.5-25.5t-10.29-25.71q-10.29-10.5-25.5-10.5t-25.71 10.29q-10.5 10.29-10.5 25.5t10.29 25.71q10.29 10.5 25.5 10.5t25.71-10.29Z"/></svg>',
    'apps': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M213-213.21q-21-21.21-21-51T213.21-315q21.21-21 51-21T315-314.79q21 21.21 21 51T314.79-213q-21.21 21-51 21T213-213.21Zm216 0q-21-21.21-21-51T429.21-315q21.21-21 51-21T531-314.79q21 21.21 21 51T530.79-213q-21.21 21-51 21T429-213.21Zm216 0q-21-21.21-21-51T645.21-315q21.21-21 51-21T747-314.79q21 21.21 21 51T746.79-213q-21.21 21-51 21T645-213.21Zm-432-216q-21-21.21-21-51T213.21-531q21.21-21 51-21T315-530.79q21 21.21 21 51T314.79-429q-21.21 21-51 21T213-429.21Zm216 0q-21-21.21-21-51T429.21-531q21.21-21 51-21T531-530.79q21 21.21 21 51T530.79-429q-21.21 21-51 21T429-429.21Zm216 0q-21-21.21-21-51T645.21-531q21.21-21 51-21T747-530.79q21 21.21 21 51T746.79-429q-21.21 21-51 21T645-429.21Zm-432-216q-21-21.21-21-51T213.21-747q21.21-21 51-21T315-746.79q21 21.21 21 51T314.79-645q-21.21 21-51 21T213-645.21Zm216 0q-21-21.21-21-51T429.21-747q21.21-21 51-21T531-746.79q21 21.21 21 51T530.79-645q-21.21 21-51 21T429-645.21Zm216 0q-21-21.21-21-51T645.21-747q21.21-21 51-21T747-746.79q21 21.21 21 51T746.79-645q-21.21 21-51 21T645-645.21Z"/></svg>',
    'build': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M666-163 475-354q-20 8-43.5 12.5T384-337q-99 0-169.5-70T144-576q0-37.78 9.5-71.89T182-711l144 144 70-70-144-144q29-17 62.5-26t69.5-9q100 0 170 71t70 170.19q0 22.81-4.5 42.31Q615-513 607-493l195 194q14 14.35 14 34.67Q816-244 802-230l-68 67q-14.09 14-34.04 14Q680-149 666-163Zm34-68 35-34-215-213q20-24 26-52.5t6-44.5q0-66.85-47.5-116.42Q457-741 390-744l82 81q11 11.18 11 26.09t-11.29 26.12L351.29-491.21Q340-480 325.82-480T301-491l-85-85q0 69 49.5 118T384-409q17 0 47-7t56-28l213 213ZM476-488Z"/></svg>',
    'code': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M336-240 96-480l240-240 51 51-189 189 189 189-51 51Zm288 0-51-51 189-189-189-189 51-51 240 240-240 240Z"/></svg>',
    'refresh': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M480-192q-120 0-204-84t-84-204q0-120 84-204t204-84q65 0 120.5 27t95.5 72v-99h72v240H528v-72h131q-29-44-76-70t-103-26q-90 0-153 63t-63 153q0 90 63 153t153 63q84 0 144-55.5T693-456h74q-9 112-91 188t-196 76Z"/></svg>',
    'storage': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M96-192v-144h768v144H96Zm72-36h72v-72h-72v72ZM96-624v-144h768v144H96Zm72-36h72v-72h-72v72ZM96-408v-144h768v144H96Zm72-36h72v-72h-72v72Z"/></svg>',
    'crop_square': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M204-120q-34.65 0-59.32-24.68Q120-169.35 120-204v-552q0-34.65 24.68-59.33Q169.35-840 204-840h552q34.65 0 59.33 24.67Q840-790.65 840-756v552q0 34.65-24.67 59.32Q790.65-120 756-120H204Zm0-84h552v-552H204v552Zm0 0v-552 552Z"/></svg>',
    'dark_mode': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M479.96-144Q340-144 242-242t-98-238q0-140 97.93-238t237.83-98q13.06 0 25.65 1 12.59 1 25.59 3-39 29-62 72t-23 92q0 85 58.5 143.5T648-446q49 0 92-23t72-62q2 13 3 25.59t1 25.65q0 139.9-98.04 237.83t-238 97.93Zm.04-72q82 0 148.78-47.07Q695.55-310.15 727-386q-20 5-39.67 8.5Q667.67-374 648-374q-113.86 0-193.93-80.07Q374-534.14 374-648q0-19.67 3.5-39.33Q381-707 386-727q-75.85 31.45-122.93 98.22Q216-562 216-480q0 110 77 187t187 77Zm-14-250Z"/></svg>',
    'light_mode': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M565-395q35-35 35-85t-35-85q-35-35-85-35t-85 35q-35 35-35 85t35 85q35 35 85 35t85-35Zm-221 51q-56-56-56-136t56-136q56-56 136-56t136 56q56 56 56 136t-56 136q-56 56-136 56t-136-56ZM216-444H48v-72h168v72Zm696 0H744v-72h168v72ZM444-744v-168h72v168h-72Zm0 696v-168h72v168h-72ZM269-642 166-742l51-55 102 104-50 51Zm474 475L642-268l49-51 103 101-51 51ZM640-691l102-101 51 49-100 103-53-51ZM163-217l105-99 49 47-98 104-56-52Zm317-263Z"/></svg>',
    'delete': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M312-144q-29.7 0-50.85-21.15Q240-186.3 240-216v-480h-48v-72h192v-48h192v48h192v72h-48v479.57Q720-186 698.85-165T648-144H312Zm336-552H312v480h336v-480ZM384-288h72v-336h-72v336Zm120 0h72v-336h-72v336ZM312-696v480-480Z"/></svg>',
    'download': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M480-336 288-528l51-51 105 105v-342h72v342l105-105 51 51-192 192ZM263.72-192Q234-192 213-213.15T192-264v-72h72v72h432v-72h72v72q0 29.7-21.16 50.85Q725.68-192 695.96-192H263.72Z"/></svg>',
    'memory': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M384-384v-192h192v192H384Zm72-72h48v-48h-48v48Zm-96 312v-96h-48q-29 0-50.5-21.5T240-312v-48h-96v-72h96v-96h-96v-72h96v-48q0-29 21.5-50.5T312-720h48v-96h72v96h96v-96h72v96h48q29 0 50.5 21.5T720-648v48h96v72h-96v96h96v72h-96v48q0 29-21.5 50.5T648-240h-48v96h-72v-96h-96v96h-72Zm288-168v-336H312v336h336ZM480-480Z"/></svg>',
    'mobile_off': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M803-56 56-803l51-50 746 746-50 51Zm-59-261-72-72v-451H216q0-29 21.5-50.5T288-912h384q29.7 0 50.85 21.15Q744-869.7 744-840v144q20 0 34 14t14 34v96q0 20-14 34t-34 14v187ZM505.5-730.29q10.5-10.29 10.5-25.5t-10.29-25.71q-10.29-10.5-25.5-10.5t-25.71 10.29q-10.5 10.29-10.5 25.5t10.29 25.71q10.29 10.5 25.5 10.5t25.71-10.29ZM288-48q-29.7 0-50.85-21.15Q216-90.3 216-120v-624l72 72v552h384v-168l72 72v96q0 32-22.5 52T672-48H288Zm147-348Zm117-112Z"/></svg>',
    'toggle_off': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M288-240q-100 0-170-70T48-480q0-100 70-170t170-70h384q100 0 170 70t70 170q0 100-70 170t-170 70H288Zm0-72h384q70 0 119-49t49-119q0-70-49-119t-119-49H288q-70 0-119 49t-49 119q0 70 49 119t119 49Zm85-83q35-35 35-85t-35-85q-35-35-85-35t-85 35q-35 35-35 85t35 85q35 35 85 35t85-35Zm107-85Z"/></svg>',
    'toggle_on': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M288-240q-100 0-170-70T48-480q0-100 70-170t170-70h384q100 0 170 70t70 170q0 100-70 170t-170 70H288Zm0-72h384q70 0 119-49t49-119q0-70-49-119t-119-49H288q-70 0-119 49t-49 119q0 70 49 119t119 49Zm469-83q35-35 35-85t-35-85q-35-35-85-35t-85 35q-35 35-35 85t35 85q35 35 85 35t85-35Zm-277-85Z"/></svg>',
    'battery': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M336-96q-20.4 0-34.2-13.8Q288-123.6 288-144v-600q0-20.4 13.8-34.2Q315.6-792 336-792h72v-72h144v72h72q20.4 0 34.2 13.8Q672-764.4 672-744v600q0 20.4-13.8 34.2Q644.4-96 624-96H336Zm24-456h240v-168H360v168Z"/></svg>',
    'language': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M331-126q-70-30-122.5-82.5T126-331q-30-70-30-149.5t30-149q30-69.5 82.5-122T331-834q70-30 149.5-30t149 30q69.5 30 122 82.5t82.5 122q30 69.5 30 149T834-331q-30 70-82.5 122.5t-122 82.5q-69.5 30-149 30T331-126Zm149-45q17-17 34-63.5T540-336H420q9 55 26 101.5t34 63.5Zm-91-10q-14-30-24.5-69T347-336H204q29 57 77 97.5T389-181Zm182 0q60-17 108-57.5t77-97.5H613q-7 47-17.5 86T571-181ZM177-408h161q-2-19-2.5-37.5T335-482q0-18 .5-35.5T338-552H177q-5 19-7 36.5t-2 35.5q0 18 2 35.5t7 36.5Zm234 0h138q2-20 2.5-37.5t.5-34.5q0-17-.5-35t-2.5-37H411q-2 19-2.5 37t-.5 35q0 17 .5 35t2.5 37Zm211 0h161q5-19 7-36.5t2-35.5q0-18-2-36t-7-36H622q2 19 2.5 37.5t.5 36.5q0 18-.5 35.5T622-408Zm-9-216h143q-29-57-77-97.5T571-779q14 30 24.5 69t17.5 86Zm-193 0h120q-9-55-26-101.5T480-789q-17 17-34 63.5T420-624Zm-216 0h143q7-47 17.5-86t24.5-69q-60 17-108 57.5T204-624Z"/></svg>',
}

# ---------------------------------------------------------------- configurações e idioma
def load_settings() -> dict:
    try: data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception: data = {}
    data.setdefault("lang", "pt"); data.setdefault("dark", True); data.setdefault("monitor_s", 5)
    data.setdefault("scrcpy", ""); data.setdefault("aapt", ""); data.setdefault("backup_dir", "")
    return data

def save_settings(data: dict):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass

SETTINGS = load_settings()
LANG = SETTINGS["lang"]

def t(text: str) -> str:
    """Traduz um texto estático ou com {placeholders}. Textos sem tradução ficam em português."""
    if LANG == "en":
        return TR.get(text, text)
    return text

TR = {
    # geral
    "Visão geral": "Overview", "Aplicativos": "Apps", "Ferramentas": "Tools", "Console": "Console",
    "Dispositivo": "Device", "Alternar tema claro/escuro": "Toggle light/dark theme",
    "Trocar idioma": "Change language", "Atualizar lista de dispositivos": "Refresh device list",
    "{n} autorizado(s)": "{n} authorized", "Nenhum dispositivo": "No device",
    "ADB não encontrado": "ADB not found", "Erro no ADB": "ADB error", "Pronto": "Ready",
    "Sim": "Yes", "Não": "No", "Cancelar": "Cancel", "Concluído.": "Done.",
    "Operação concluída.": "Operation completed.", "Operação falhou": "Operation failed",
    "Erro": "Error", "Aviso": "Warning", "Selecione um dispositivo autorizado.": "Select an authorized device.",
    "adb não encontrado. Instale o Platform Tools ou coloque adb.exe na pasta platform-tools/.":
        "adb not found. Install Platform Tools or put adb.exe in the platform-tools/ folder.",
    "fastboot não encontrado. Coloque fastboot.exe na pasta platform-tools/.":
        "fastboot not found. Put fastboot.exe in the platform-tools/ folder.",
    "Não foi possível ler as informações": "Could not read device information",
    "RAM indisponível": "RAM unavailable",
    # visão geral
    "Modelo": "Model", "Versão do Android": "Android version", "Número de série": "Serial number",
    "Armazenamento": "Storage", "Memória RAM": "Memory (RAM)", "Bateria": "Battery",
    "Temperatura da bateria": "Battery temperature", "Ações": "Actions",
    "Espelhamento usa o scrcpy; reinício envia o comando ao aparelho.":
        "Mirroring uses scrcpy; restart sends the command to the device.",
    "Espelhar tela": "Mirror screen", "Captura de tela": "Screenshot",
    "Atualizar informações": "Refresh info", "Reiniciar para:": "Restart to:", "Reiniciar": "Restart",
    "Sistema normal": "Normal system", "Recovery": "Recovery", "Bootloader": "Bootloader",
    "Confirmar reinicialização": "Confirm restart", "Reiniciar o dispositivo para: {label}?":
        "Restart the device to: {label}?",
    "Reiniciando": "Restarting", "Comando enviado. A conexão pode cair durante o reinício.":
        "Command sent. The connection may drop during restart.",
    "{used} MB usados de {total} MB": "{used} MB used of {total} MB",
    "{used} GB usados de {total} GB": "{used} GB used of {total} GB",
    "Captura salva em {path}": "Screenshot saved to {path}",
    "Salvar captura de tela": "Save screenshot", "O Android não retornou uma imagem PNG.":
        "Android did not return a PNG image.",
    "scrcpy não encontrado. Coloque scrcpy.exe na pasta tools/ ou no PATH.":
        "scrcpy not found. Put scrcpy.exe in the tools/ folder or on PATH.",
    "scrcpy iniciado": "scrcpy started", "Terminal ADB aberto": "ADB terminal opened",
    "Não foi possível abrir o terminal: {e}": "Could not open the terminal: {e}",
    "Bateria: {level}% · {temp} °C": "Battery: {level}% · {temp} °C",
    # aplicativos
    "Buscar por nome ou pacote…": "Search by name or package…",
    "Todos": "All", "Ativados": "Enabled", "Desativados": "Disabled", "Excluídos": "Removed",
    "Atualizar": "Refresh", "Nomes e ícones": "Names and icons",
    "Busca o nome e o ícone reais de cada app (requer aapt)": "Fetches each app's real name and icon (requires aapt)",
    "Limpar cache de todos": "Clear cache for all",
    "Remove o cache de todos os aplicativos do aparelho": "Removes the cache of all apps on the device",
    "Ícone": "Icon", "Aplicativo": "App", "Pacote": "Package", "Tamanho": "Size", "Estado: {state}": "State: {state}",
    "Ações nos selecionados": "Actions on selected",
    "Marque os apps na coluna ✔ (ou selecione linhas).": "Check apps in the ✔ column (or select rows).",
    "Nenhum app marcado.": "No app selected.", "{n} app(s) marcado(s)": "{n} app(s) selected",
    "Forçar parada": "Force stop", "Desativar": "Disable", "Reativar": "Enable",
    "Salvar APK no PC": "Save APK to PC", "Backup de dados": "Data backup",
    "Desinstalar para usuário": "Uninstall for user",
    "Abrir app": "Open app", "Copiar nome do app": "Copy app name", "Copiar nome do pacote": "Copy package name",
    "Nome copiado.": "Name copied.", "Pacote copiado.": "Package copied.",
    "Carregue os aplicativos primeiro.": "Load the apps first.",
    "Marque (ou selecione) pelo menos um aplicativo.": "Check (or select) at least one app.",
    "Carregando aplicativos…": "Loading apps…", "{n} aplicativos carregados": "{n} apps loaded",
    "Carregando nomes e ícones ({done}/{total} apps)": "Loading names and icons ({done}/{total} apps)",
    "Nomes e ícones atualizados.": "Names and icons updated.",
    "Para nomes e ícones reais, coloque aapt.exe (Android SDK Build-Tools) na pasta tools/.":
        "For real names and icons, put aapt.exe (Android SDK Build-Tools) in the tools/ folder.",
    "{title}: {n} aplicativo(s)…": "{title}: {n} app(s)…",
    "Desinstalar para o usuário atual": "Uninstall for current user",
    "Desinstalar {n} aplicativo(s)?": "Uninstall {n} app(s)?",
    "Isso pode remover dados locais. Apps de sistema podem não ser removíveis.":
        "This may remove local data. System apps may not be removable.",
    "Desativar {n} aplicativo(s)?": "Disable {n} app(s)?",
    "Isso pode afetar funções do sistema.": "This may affect system functions.",
    "Limpar cache de todos os apps": "Clear cache for all apps",
    "Isso remove o cache de TODOS os aplicativos do aparelho.\n\nOs dados dos apps (login, configurações, mensagens) são mantidos. A operação pode levar alguns minutos.":
        "This removes the cache of ALL apps on the device.\n\nApp data (logins, settings, messages) is kept. This may take a few minutes.",
    "Limpando cache de todos os apps…": "Clearing cache of all apps…",
    "Cache limpo.": "Cache cleared.", "Salvar APK em…": "Save APK to…",
    "Nenhum APK encontrado.": "No APK found.", "salvo em {dest}": "saved to {dest}",
    "parado": "stopped", "Abrindo {pkg}…": "Opening {pkg}…",
    "Não foi possível abrir {pkg}: {e}": "Could not open {pkg}: {e}",
    "Backup de dados (adb backup)": "Data backup (adb backup)",
    "Escolha a pasta para os backups…": "Choose the folder for backups…",
    "O Android pedirá confirmação no aparelho para cada backup. Confirme na tela do celular quando aparecer. Continuar?":
        "Android will ask for confirmation on the device for each backup. Confirm on the phone screen when it appears. Continue?",
    "backup salvo em {dest}": "backup saved to {dest}",
    "Os apps de sistema só são buscados quando aparecem na tela.": "System apps are only fetched when they appear on screen.",
    # ferramentas
    "Instalar APK / XAPK": "Install APK / XAPK",
    "Aceita APK, XAPK e APKS. Vários arquivos são instalados um a um.":
        "Accepts APK, XAPK and APKS. Multiple files are installed one by one.",
    "Nenhum arquivo escolhido": "No file selected", "Escolher pacotes": "Choose packages",
    "Instalar como pacote dividido (split)": "Install as split package", "Escolher…": "Choose…",
    "Instalar": "Install", "Confirmar instalação": "Confirm installation",
    "Instalar {n} arquivo(s) em {dev}?": "Install {n} file(s) on {dev}?",
    "Escolha arquivos existentes.": "Choose existing files.", "Instalando": "Installing",
    "Arquivos": "Files", "Envie para o aparelho ou baixe um arquivo dele.": "Send to the device or download a file from it.",
    "Arquivo no computador": "File on this computer",
    "Caminho no Android, ex.: /sdcard/Download/": "Path on Android, e.g. /sdcard/Download/",
    "Escolher arquivo para enviar": "Choose file to send",
    "Escolha um arquivo e informe o destino no Android.": "Choose a file and enter the destination on Android.",
    "Enviar ao celular": "Send to phone", "Baixar do celular": "Download from phone",
    "Enviando": "Sending", "Baixando": "Downloading", "Salvar arquivo baixado": "Save downloaded file",
    "Informe o caminho no Android.": "Enter the path on Android.",
    "Tela": "Screen", "A resolução e o DPI atuais são lidos automaticamente ao conectar o aparelho.":
        "Current resolution and DPI are read automatically when connecting.",
    "Predefinição de largura (mantém a proporção):": "Width preset (keeps aspect ratio):",
    "Largura": "Width", "Altura": "Height", "Restaurar padrão": "Restore default", "Aplicar": "Apply",
    "Aplicar tela": "Apply screen", "Aplicar {w}×{h} e {dpi} dpi?": "Apply {w}×{h} and {dpi} dpi?",
    "Restaurar tela": "Restore screen", "Restaurar resolução e DPI padrão do Android?":
        "Restore Android's default resolution and DPI?",
    "Restaurando": "Restoring", "Aplicando resolução e DPI": "Applying resolution and DPI",
    "Não foi possível interpretar a resolução ou o DPI.": "Could not read resolution or DPI.",
    "Não foi possível ler a resolução atual.": "Could not read the current resolution.",
    "Formato não suportado: {name}": "Unsupported format: {name}",
    "Nenhum APK dentro de {name}": "No APK inside {name}",
    "Operação": "Operation",
    # console
    "Execute comandos ADB ou Fastboot. Digite com ou sem o prefixo (“pm list packages” ou “adb shell pm list packages”). “shell” abre um terminal interativo. Cada execução fica registrada no log.":
        "Run ADB or Fastboot commands, with or without the prefix (“pm list packages” or “adb shell pm list packages”). “shell” opens an interactive terminal. Each run is logged.",
    "Ex.: adb shell pm list packages": "e.g. adb shell pm list packages",
    "Executar": "Run", "Abrir terminal ADB": "Open ADB terminal", "Limpar log": "Clear log",
    "Abrir pasta de logs": "Open log folder",
    "Os comandos executados e suas saídas aparecerão aqui.": "Executed commands and their output will appear here.",
    "Nenhum log ainda.": "No log yet.", "Comando concluído sem saída.": "Command finished with no output.",
    "Use um comando por vez; operadores de shell não são aceitos.": "Use one command at a time; shell operators are not allowed.",
    "Comando potencialmente destrutivo": "Potentially destructive command",
    "Executar {mode}: {raw}?\n\nPode apagar dados ou alterar o firmware.":
        "Run {mode}: {raw}?\n\nThis may erase data or change the firmware.",
    "Logs": "Logs",
    "Selecione um dispositivo autorizado para continuar.": "Select an authorized device to continue.",
    "Idioma": "Language",
}

TR.update({
    "Configurações": "Settings", "Caminho do scrcpy.exe": "scrcpy.exe path", "Caminho do aapt.exe": "aapt.exe path",
    "Pasta padrão de backups": "Default backup folder", "Intervalo do monitoramento (segundos)": "Monitoring interval (seconds)",
    "Configurações salvas.": "Settings saved.", "Escolher": "Choose", "Salvar": "Save", "Fechar": "Close",
    "Executáveis (*.exe);;Todos (*.*)": "Executables (*.exe);;All (*.*)",
    "Histórico (últimos 5 min)": "History (last 5 min)", "Patch de segurança": "Security patch",
    "IP do Wi-Fi": "Wi-Fi IP", "RAM": "RAM", "Bateria": "Battery", "Agora": "Now", "-5 min": "-5 min",
    "Permissões": "Permissions", "Ver permissões": "View permissions", "Nenhuma permissão encontrada.": "No permissions found.",
    "Todos os tipos": "All types", "Usuário": "User", "Sistema": "System", "Mín.": "Min.", "Tamanho mínimo": "Minimum size",
    "Iniciar gravação": "Start recording", "Parar e salvar": "Stop and save", "Gravação de tela": "Screen recording",
    "Grava a tela do aparelho (máximo de 3 minutos por gravação).": "Records the device screen (3 minutes max per recording).",
    "Gravação iniciada.": "Recording started.", "Salvar gravação": "Save recording",
    "Gravação salva em {dest}": "Recording saved to {dest}",
    "Gravação finalizada pelo aparelho. Clique em Parar e salvar.": "Recording ended by the device. Click Stop and save.",
    "Conexão sem fio (ADB Wi-Fi)": "Wireless connection (ADB Wi-Fi)",
    "Ative a depuração por TCP/IP com o cabo conectado (porta 5555), depois conecte pelo IP do aparelho.":
        "Enable TCP/IP debugging with the cable connected (port 5555), then connect using the device IP.",
    "Ativar TCP/IP": "Enable TCP/IP", "Conectar": "Connect", "Desconectar": "Disconnect",
    "Informe o IP:porta.": "Enter IP:port.", "Ativando TCP/IP": "Enabling TCP/IP", "Conectando": "Connecting",
    "Desconectando": "Disconnecting", "Dispositivos conectados": "Connected devices",
    "Clique para selecionar o aparelho que será controlado.": "Click to select the device to control.",
    "Dispositivo desconectado: {serial}": "Device disconnected: {serial}",
    "Tempo de resposta registrado no log": "Response time logged",
    "Abrir pasta de logs": "Open log folder",
})

TR.update({
    "Debloat Android": "Android Debloat", "Compara os pacotes instalados com a lista comunitária Universal Debloater. Recomendações são orientativas; revise a descrição e faça backup antes de remover apps.": "Compares installed packages with the community Universal Debloater list. Recommendations are guidance only; review descriptions and back up before removing apps.",
    "Buscar nome, pacote ou descrição…": "Search name, package or description…", "Todos os riscos": "All risk levels", "Recomendado": "Recommended", "Atenção": "Caution", "Especialista": "Expert", "Inseguro": "Unsafe", "Não listado": "Unlisted",
    "Escanear novamente": "Scan again", "Conecte um Android autorizado e clique em Escanear novamente.": "Connect an authorized Android device and click Scan again.", "Pacote": "Package", "Recomendação": "Recommendation", "Origem": "Source", "Descrição": "Description", "Marcar recomendados": "Select recommended", "Desmarcar todos": "Clear selection", "Desinstalar selecionados": "Uninstall selected",
    "Escaneando pacotes e carregando a lista de recomendações…": "Scanning packages and loading recommendations…", "Falha ao escanear: {error}": "Scan failed: {error}", "{n} pacotes encontrados · lista: {source}": "{n} packages found · list: {source}", "Sem descrição na base comunitária.": "No description in community database.", "Marque os pacotes que deseja desinstalar.": "Select the packages you want to uninstall.", "A remoção de pacotes de sistema pode quebrar funções do aparelho ou impedir a inicialização. Faça backup e remova poucos por vez.": "Removing system packages may break device features or prevent boot. Back up and remove only a few at a time.", "Confirmar desinstalação": "Confirm uninstall", "Resultado": "Result", "Resultado: {ok}/{total} removidos.": "Result: {ok}/{total} removed.",
})

# ---------------------------------------------------------------- paleta e estilos
TR.update({
    "Proporção automática": "Automatic ratio", "Proporção automática: a largura define altura e DPI (clique para desativar)":
        "Automatic ratio: width sets height and DPI (click to disable)",
    "Escolha um arquivo para enviá-lo à pasta Download do aparelho.": "Choose a file to send it to the device's Download folder.",
    "Escolher arquivo e enviar": "Choose file and send", "Enviado para {dest}": "Sent to {dest}",
    "Ative 'Instalar via USB' nas opções do desenvolvedor do aparelho.": "Enable 'Install via USB' in the device's developer options.",
    "Permissão de arquivos não concedida ao helper. Abra o DroidControl Helper no aparelho e toque em 'Permitir acesso a arquivos'.":
        "File permission not granted to the helper. Open DroidControl Helper on the device and tap 'Allow file access'.",
    "Atualiza a lista e os nomes e ícones (pelo DroidControl Helper).": "Refreshes the list and names and icons (via DroidControl Helper).",
    "Busca nomes e ícones pelo app DroidControl Helper (ou pelo modo lento, com aapt)": "Fetches names and icons via the DroidControl Helper app (or slow mode, with aapt)",
    "Instalando... ({i}/{n})": "Installing... ({i}/{n})",
    "Exportando nomes e ícones pelo helper…": "Exporting names and icons via the helper…",
    "Não foi possível obter nomes e ícones pelo helper: {e}": "Could not get names and icons from the helper: {e}",
    "Helper indisponível, usando modo lento: {e}": "Helper unavailable, using slow mode: {e}",
    "Ativando TCP/IP": "Enabling TCP/IP", "Ativar TCP/IP": "Enable TCP/IP",
    "Ative a depuração por TCP/IP com o cabo conectado (porta 5555), depois conecte pelo IP do aparelho.":
        "Enable TCP/IP debugging with the cable connected (port 5555), then connect using the device IP.",
    "Atualização": "Update", "Caminho do aapt.exe": "aapt.exe path", "Caminho do scrcpy.exe": "scrcpy.exe path",
    "Clique para selecionar o aparelho que será controlado.": "Click to select the device to control.",
    "Conectando": "Connecting", "Conectar": "Connect", "Conexão sem fio (ADB Wi-Fi)": "Wireless connection (ADB Wi-Fi)",
    "Configurações": "Settings", "Configurações salvas.": "Settings saved.",
    "Configure a URL de atualização nas configurações.": "Set the update URL in settings.",
    "Desconectando": "Disconnecting", "Desconectar": "Disconnect",
    "Dispositivo desconectado durante a operação.": "Device disconnected during the operation.",
    "Dispositivo desconectado: {serial}": "Device disconnected: {serial}",
    "Dispositivos conectados": "Connected devices", "Escolher": "Choose",
    "Executáveis (*.exe);;Todos (*.*)": "Executables (*.exe);;All files (*.*)", "Fastboot": "Fastboot",
    "IP do Wi-Fi": "Wi-Fi IP", "Informe o IP:porta.": "Enter IP:port.",
    "Intervalo do monitoramento (segundos)": "Monitoring interval (seconds)", "Mín.": "Min.",
    "Nenhuma permissão encontrada.": "No permission found.",
    "Nova versão disponível: {v}. {url}": "New version available: {v}. {url}",
    "Não foi possível verificar a atualização: {e}": "Could not check for updates: {e}",
    "Pasta padrão de backups": "Default backup folder", "Patch de segurança": "Security patch",
    "Permissões": "Permissions", "Sistema": "System", "Tamanho mínimo": "Minimum size",
    "Todos os tipos": "All types", "URL de verificação de atualização (opcional)": "Update check URL (optional)",
    "Usuário": "User", "Ver permissões": "View permissions", "Verificar atualização": "Check for updates",
    "Você já está com a versão mais recente.": "You already have the latest version.",
    "{ok} de {n} concluído(s).": "{ok} of {n} completed.",
})

PALETTES = {
    "light": dict(bg="#F7F5FC", surface="#FFFFFF", surface2="#F3F0FA", border="#E6E0F3",
                  text="#221A33", muted="#756B8A", accent="#7C3AED", accent_hover="#6D28D9",
                  accent_text="#FFFFFF", accent_soft="#EFE8FD", danger="#DC2626",
                  danger_soft="#FDECEC", success="#15803D"),
    "dark": dict(bg="#0F0C17", surface="#17132A", surface2="#1E1936", border="#2C2547",
                 text="#EFEBFA", muted="#A097BD", accent="#A78BFA", accent_hover="#C4B5FD",
                 accent_text="#140F26", accent_soft="#2B2248", danger="#F87171",
                 danger_soft="#3A1F2A", success="#4ADE80"),
}

STYLE = """
QMainWindow, QWidget#Root { background: @bg; }
QWidget { color: @text; font-family: "Segoe UI", sans-serif; font-size: 10pt; }
QWidget#TopBar { background: @surface; border-bottom: 1px solid @border; }
QLabel#Brand { font-size: 15pt; font-weight: 800; color: @accent; }
QLabel#PageTitle { font-size: 16pt; font-weight: 800; color: @accent; }
QLabel#Muted { color: @muted; }
QLabel#Pill { background: @accent_soft; color: @accent; border-radius: 11px; padding: 4px 10px; font-weight: 600; }
QLabel#CardTitle { font-size: 11pt; font-weight: 700; color: @text; }
QLabel#CardHint { color: @muted; font-size: 9pt; }
QLabel#StatLabel { color: @muted; font-size: 9pt; }
QLabel#StatValue { font-size: 11pt; font-weight: 700; color: @text; }
QLabel#BigValue { font-size: 18pt; font-weight: 800; color: @text; }
QLabel#Info { background: @accent_soft; color: @accent; border-radius: 10px; padding: 9px 12px; }

QFrame#Card { background: @surface; border: 1px solid @border; border-radius: 14px; }
QFrame#Tile { background: @surface2; border: 1px solid @border; border-radius: 12px; }

QListWidget#Sidebar { background: @surface; border: 0; border-right: 1px solid @border; outline: 0; padding: 12px 10px; }
QListWidget#Sidebar::item { color: @muted; padding: 11px 14px; border-radius: 10px; margin: 2px 0; font-weight: 600; }
QListWidget#Sidebar::item:hover { color: @text; background: @surface2; }
QListWidget#Sidebar::item:selected { color: @accent; background: @accent_soft; }

QPushButton { background: @surface2; color: @text; border: 1px solid @border; border-radius: 9px;
              padding: 8px 14px; font-weight: 600; }
QPushButton:hover { border-color: @accent; color: @accent; }
QPushButton:pressed { background: @accent_soft; }
QPushButton:disabled { color: @muted; }
QPushButton#Primary { background: @accent; color: @accent_text; border: 0; }
QPushButton#Primary:hover { background: @accent_hover; color: @accent_text; }
QPushButton#Danger { background: @danger_soft; color: @danger; border: 1px solid transparent; }
QPushButton#Danger:hover { border-color: @danger; color: @danger; }
QPushButton#Ghost { background: transparent; border: 0; color: @muted; padding: 8px 10px; }
QPushButton#Ghost:hover { color: @accent; background: @accent_soft; }
QPushButton#Icon { padding: 8px; min-width: 18px; }
QPushButton#SideAction { text-align: left; padding: 9px 14px; font-weight: 500; }

QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {
    background: @surface; color: @text; border: 1px solid @border; border-radius: 9px;
    padding: 7px 10px; selection-background-color: @accent_soft; selection-color: @text;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus { border: 1px solid @accent; }
QComboBox::drop-down { border: 0; width: 24px; }
QComboBox QAbstractItemView { background: @surface; color: @text; border: 1px solid @border;
    selection-background-color: @accent_soft; selection-color: @accent; outline: 0; padding: 4px; }
QSpinBox::up-button, QSpinBox::down-button { width: 16px; border: 0; background: transparent; }

QCheckBox { spacing: 8px; color: @text; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 5px; border: 1px solid @border; background: @surface; }
QCheckBox::indicator:checked { background: @accent; border-color: @accent; }

QTableWidget { background: @surface; alternate-background-color: @surface2; border: 1px solid @border;
    border-radius: 12px; gridline-color: transparent; selection-background-color: @accent_soft;
    selection-color: @text; outline: 0; }
QTableWidget::item { padding: 4px 6px; border: 0; }
QTableWidget::item:selected { background: @accent_soft; color: @text; }
QHeaderView::section { background: @surface2; color: @muted; padding: 8px; border: 0;
    border-bottom: 1px solid @border; font-weight: 600; }
QTableCornerButton::section { background: @surface2; border: 0; }

QProgressBar { background: @surface2; border: 0; border-radius: 6px; min-height: 10px; max-height: 10px; }
QProgressBar::chunk { background: @accent; border-radius: 6px; }
QStatusBar { background: @surface; color: @muted; border-top: 1px solid @border; }
QToolTip { background: @surface; color: @text; border: 1px solid @border; padding: 6px; }
QDialog, QMessageBox { background: @surface; }
QDialog QLabel, QMessageBox QLabel { color: @text; background: transparent; }
QMenu { background: @surface; color: @text; border: 1px solid @border; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 8px 22px; border-radius: 6px; }
QMenu::item:selected { background: @accent_soft; color: @accent; }
QMenu::separator { height: 1px; background: @border; margin: 4px 8px; }
QScrollArea { background: transparent; border: 0; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: @border; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: @muted; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: @border; border-radius: 4px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
"""

# ---------------------------------------------------------------- utilitários
ICON_SVGS.update({
    'lock': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M263.72-96Q234-96 213-117.15T192-168v-384q0-29.7 21.15-50.85Q234.3-624 264-624h24v-96q0-79.68 56.23-135.84 56.22-56.16 136-56.16Q560-912 616-855.84q56 56.16 56 135.84v96h24q29.7 0 50.85 21.15Q768-581.7 768-552v384q0 29.7-21.16 50.85Q725.68-96 695.96-96H263.72Zm.28-72h432v-384H264v384Zm267-141.21q21-21.21 21-51T530.79-411q-21.21-21-51-21T429-410.79q-21 21.21-21 51T429.21-309q21.21 21 51 21T531-309.21ZM360-624h240v-96q0-50-35-85t-85-35q-50 0-85 35t-35 85v96Zm-96 456v-384 384Z"/></svg>',
    'lock_open': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M264-624h336v-96q0-50-35-85t-85-35q-50 0-85 35t-35 85h-72q0-80 56.23-136 56.22-56 136-56Q560-912 616-855.84q56 56.16 56 135.84v96h24q29.7 0 50.85 21.15Q768-581.7 768-552v384q0 29.7-21.16 50.85Q725.68-96 695.96-96H263.72Q234-96 213-117.15T192-168v-384q0-29.7 21.15-50.85Q234.3-624 264-624Zm0 456h432v-384H264v384Zm267-141.21q21-21.21 21-51T530.79-411q-21.21-21-51-21T429-410.79q-21 21.21-21 51T429.21-309q21.21 21 51 21T531-309.21ZM264-168v-384 384Z"/></svg>',
})

ICON_SVGS.update({
    'checkbox_checked': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="m429-336 238-237-51-51-187 186-85-84-51 51 136 135ZM216-144q-29.7 0-50.85-21.15Q144-186.3 144-216v-528q0-29.7 21.15-50.85Q186.3-816 216-816h528q29.7 0 50.85 21.15Q816-773.7 816-744v528q0 29.7-21.15 50.85Q773.7-144 744-144H216Zm0-72h528v-528H216v528Zm0-528v528-528Z"/></svg>',
    'checkbox_outline': '<svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="48 -912 864 864" width="18px" fill="#e3e3e3"><path d="M216-144q-29.7 0-50.85-21.15Q144-186.3 144-216v-528q0-29.7 21.15-50.85Q186.3-816 216-816h528q29.7 0 50.85 21.15Q816-773.7 816-744v528q0 29.7-21.15 50.85Q773.7-144 744-144H216Zm0-72h528v-528H216v528Z"/></svg>',
})

def log(message: str) -> str:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}"
    try:
        LOG_DIR.mkdir(exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    return line

def find_tool(name: str) -> str | None:
    if name == "scrcpy" and SETTINGS.get("scrcpy") and Path(SETTINGS["scrcpy"]).exists(): return SETTINGS["scrcpy"]
    for candidate in (DATA_DIR / "platform-tools" / f"{name}.exe", DATA_DIR / "tools" / f"{name}.exe"):
        if candidate.exists(): return str(candidate)
    return shutil.which(name) or shutil.which(name + ".exe")

def run_command(args, timeout=90) -> str:
    """Executa sem shell (evita injeção) e devolve a saída; levanta erro se falhar."""
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    out, err = (p.stdout or "").strip(), (p.stderr or "").strip()
    if p.returncode != 0:
        raise RuntimeError(err or out or f"Comando falhou (código {p.returncode})")
    return out

CONNECTION_ERRORS = ("device offline", "no devices", "device not found", "device '", "unauthorized",
                     "cannot connect", "more than one device", "error: closed")

def is_connection_error(message: str) -> bool:
    low = (message or "").lower()
    return any(k in low for k in CONNECTION_ERRORS)

def check_install_output(out: str) -> str:
    low = (out or "").lower()
    if "failure" in low or "install_failed" in low or ("error" in low and "success" not in low):
        hint = ""
        if "user_restricted" in low:
            hint = "\n" + t("Ative 'Instalar via USB' nas opções do desenvolvedor do aparelho.")
        raise RuntimeError((out or "") + hint)
    return out

def parse_devices(output: str) -> list:
    return [tuple(l.split()[:2]) for l in (output or "").splitlines()[1:] if len(l.split()) >= 2]

def parse_meminfo(text: str):
    vals = {}
    for line in (text or "").splitlines():
        if ":" in line:
            try: vals[line.split(":", 1)[0]] = int(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError): pass
    if "MemTotal" not in vals: return None
    total = vals["MemTotal"] // 1024
    avail = vals.get("MemAvailable", vals.get("MemFree", 0)) // 1024
    return (max(0, total - avail), total)

def parse_battery(text: str):
    lvl = re.search(r"level:\s*(\d+)", text or "")
    tmp = re.search(r"temperature:\s*(-?\d+)", text or "")
    return (int(lvl.group(1)) if lvl else None, int(tmp.group(1)) / 10 if tmp else None)

def parse_helper_entries(text: str) -> list:
    """Lê formatos conhecidos do apps.json do Helper e normaliza pacote/nome."""
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("apps", data.get("packages", data.get("items", [])))
    if not isinstance(data, list):
        raise ValueError("Formato apps.json inválido: esperava uma lista de aplicativos.")
    entries = []
    for item in data:
        if not isinstance(item, dict):
            continue
        pkg = item.get("pkg") or item.get("packageName") or item.get("package") or item.get("package_name")
        if not pkg:
            continue
        label = item.get("label") or item.get("name") or item.get("appName") or pkg
        entries.append((str(pkg).strip(), str(label).strip() or str(pkg).strip()))
    return entries

def helper_export(adb, timeout=180):
    """Pede ao helper no aparelho que exporte nomes e ícones, e baixa tudo de uma vez.
    Retorna None se o helper não estiver instalado; senão, lista de (pacote, nome, caminho_do_icone)."""
    if HELPER_PKG not in run_command(adb + ["shell", "pm", "list", "packages", HELPER_PKG], 30):
        return None
    # Concede o acesso a arquivos ao helper pelo adb (Android 11+), sem precisar tocar no aparelho
    try: run_command(adb + ["shell", "appops", "set", HELPER_PKG, "MANAGE_EXTERNAL_STORAGE", "allow"], 20)
    except Exception: pass
    try:
        status = run_command(adb + ["shell", "appops", "get", HELPER_PKG, "MANAGE_EXTERNAL_STORAGE"], 20)
        if "MANAGE_EXTERNAL_STORAGE" in status and "allow" not in status.lower():
            raise PermissionError(t("Permissão de arquivos não concedida ao helper. Abra o DroidControl Helper no aparelho e toque em 'Permitir acesso a arquivos'.") + f" [{status}]")
    except PermissionError: raise
    except Exception: pass
    run_command(adb + ["shell", "rm", "-f", f"{HELPER_REMOTE}/apps.json", f"{HELPER_REMOTE}/error.txt"], 30)
    run_command(adb + ["shell", "am", "broadcast", "-a", HELPER_ACTION, "-p", HELPER_PKG], 30)
    deadline, text = time.time() + timeout, ""
    while time.time() < deadline:
        time.sleep(1)
        err = ""
        try: err = run_command(adb + ["shell", f"if [ -f {HELPER_REMOTE}/error.txt ]; then cat {HELPER_REMOTE}/error.txt; fi"], 15)
        except Exception: pass
        if err: raise RuntimeError(err)
        try: text = run_command(adb + ["shell", f"if [ -f {HELPER_REMOTE}/apps.json ]; then cat {HELPER_REMOTE}/apps.json; fi"], 60)
        except Exception: text = ""
        if text.strip(): break
    else:
        raise RuntimeError("o helper não respondeu a tempo")
    tmp = Path(tempfile.mkdtemp(prefix="dc_helper_"))
    try:
        pull_out = run_command(adb + ["pull", HELPER_REMOTE, str(tmp)], 600)
        log(f"HELPER PULL: {pull_out}")
        # ADB/platform-tools variam no layout criado por `adb pull`.
        entries = []
        helper_entries = parse_helper_entries(text)
        for pkg, label in helper_entries:
            icon = ""
            candidates = []
            for ext in ("png", "webp", "jpg", "jpeg"):
                candidates.extend(tmp.rglob(f"{pkg}.{ext}"))
            # Alguns builds salvam ícones com nome de pacote escapado ou em diretório próprio.
            png = next((candidate for candidate in candidates if candidate.is_file() and candidate.stat().st_size > 0), None)
            if png:
                try:
                    from PySide6.QtGui import QImage
                    image = QImage(str(png))
                    if not image.isNull():
                        ICON_CACHE.mkdir(parents=True, exist_ok=True)
                        dest = ICON_CACHE / f"{pkg}.png"
                        if png.suffix.lower() == ".png":
                            shutil.copyfile(png, dest)
                        else:
                            if not image.save(str(dest), "PNG"):
                                raise RuntimeError("não foi possível converter o ícone para PNG")
                        icon = str(dest)
                except Exception as e:
                    log(f"Ícone helper inválido {pkg}: {e}")
            entries.append((pkg, label, icon))
        if not entries:
            raise RuntimeError("O Helper respondeu, mas apps.json não contém pacotes reconhecíveis.")
        log(f"HELPER EXPORT: {len(entries)} apps; {sum(bool(icon) for _, _, icon in entries)} ícones válidos")
        return entries
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", str(v))) or (0,)

def fmt_size(size) -> str:
    if size is None: return "—"
    if size >= 1024 ** 3: return f"{size / 1024 ** 3:.2f} GB"
    if size >= 1024 ** 2: return f"{size / 1024 ** 2:.1f} MB"
    return f"{size / 1024:.0f} KB"

@functools.lru_cache(maxsize=512)
def svg_pixmap(name: str, color: str, size: int = 18) -> QPixmap | None:
    raw = ICON_SVGS.get(name)
    if not raw: return None
    svg = re.sub(r"#[eE]3[eE]3[eE]3", color, raw)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size * 2, size * 2); pix.fill(Qt.transparent)
    painter = QPainter(pix); renderer.render(painter); painter.end()
    return pix

def svg_icon(name: str, color: str, size: int = 18) -> QIcon:
    pix = svg_pixmap(name, color, size)
    return QIcon(pix) if pix else QIcon()

def load_label_cache() -> dict:
    try: return json.loads(LABEL_CACHE.read_text(encoding="utf-8"))
    except Exception: return {}

def save_label_cache(data: dict):
    try:
        LABEL_CACHE.parent.mkdir(parents=True, exist_ok=True)
        LABEL_CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass

def find_aapt() -> str | None:
    if SETTINGS.get("aapt") and Path(SETTINGS["aapt"]).exists(): return SETTINGS["aapt"]
    for c in (shutil.which("aapt2"), shutil.which("aapt"),
              str(DATA_DIR / "tools" / "aapt2.exe"), str(DATA_DIR / "tools" / "aapt.exe")):
        if c and Path(c).exists(): return c
    sdk = Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "build-tools"
    if sdk.exists():
        for bt in sorted(sdk.iterdir(), reverse=True):
            for name in ("aapt2.exe", "aapt.exe"):
                if (bt / name).exists(): return str(bt / name)
    return None

def pick_icon_entry(names, icons):
    """Escolhe o PNG do ícone; para ícones XML adaptativos procura PNGs relacionados ao launcher."""
    name_set = set(names)
    for _, inner in sorted(icons, reverse=True):
        if inner.lower().endswith(".png") and inner in name_set:
            return inner
    base = Path(sorted(icons, reverse=True)[0][1].replace("\\", "/")).stem.lower() if icons else "ic_launcher"
    def related(n):
        stem = Path(n).stem.lower()
        return base in stem or "launcher" in stem or "icon" in stem
    candidates = [n for n in names if n.lower().endswith(".png") and n.startswith("res/") and related(n)]
    if not candidates: return None
    def score(n):
        stem = Path(n).stem.lower()
        return ("xxxhdpi" in n, "xxhdpi" in n, stem == base, base in stem, "launcher" in stem, "foreground" not in stem)
    return max(candidates, key=score)

def fetch_app_info(adb_cmd, aapt, pkg):
    """Baixa o APK temporariamente e lê nome e ícone PNG reais via aapt."""
    out = run_command(adb_cmd + ["shell", "pm", "path", pkg], 30)
    remote = next((l.split(":", 1)[1].strip() for l in out.splitlines() if l.startswith("package:")), None)
    if not remote: return "", ""
    with tempfile.TemporaryDirectory() as td:
        apk = Path(td) / "app.apk"
        run_command(adb_cmd + ["pull", remote, str(apk)], 180)
        badging = run_command([aapt, "dump", "badging", str(apk)], 60)
        m = re.search(r"application-label:'([^']*)'", badging)
        label = m.group(1) if m else ""
        icons = [(int(d), p) for d, p in re.findall(r"application-icon-(\d+):'([^']+)'", badging)]
        icon_path = ""
        with zipfile.ZipFile(apk) as z:
            inner = pick_icon_entry(z.namelist(), icons)
            if inner:
                ICON_CACHE.mkdir(parents=True, exist_ok=True)
                dest = ICON_CACHE / f"{pkg}.png"
                dest.write_bytes(z.read(inner))
                icon_path = str(dest)
    return label, icon_path

KNOWN_NAMES = {
    "com.android.settings": "Configurações", "com.android.chrome": "Google Chrome",
    "com.google.android.youtube": "YouTube", "com.google.android.gms": "Google Play Services",
    "com.android.vending": "Google Play Store", "com.google.android.gm": "Gmail",
    "com.google.android.apps.maps": "Google Maps", "com.whatsapp": "WhatsApp",
    "com.facebook.katana": "Facebook", "com.instagram.android": "Instagram",
    "com.spotify.music": "Spotify", "com.netflix.mediaclient": "Netflix",
    "com.microsoft.emmx": "Microsoft Edge", "com.google.android.apps.photos": "Google Fotos",
}

# ---------------------------------------------------------------- threads e widgets
class Worker(QThread):
    done = Signal(object, object)  # resultado, erro (None em caso de sucesso)
    def __init__(self, fn):
        super().__init__(); self.fn = fn
    def run(self):
        try: self.done.emit(self.fn(), None)
        except Exception as e: self.done.emit(None, str(e) or repr(e))

class AppInfoWorker(QThread):
    """Um worker com 2 threads. A fila pode ser reordenada sem criar novos processos."""
    item = Signal(str, str, str, int, int)  # pacote, nome, ícone, concluídos, total
    PARALLEL = 2
    def __init__(self, adb_cmd, aapt):
        super().__init__()
        self.adb_cmd, self.aapt = adb_cmd, aapt
        self._queue: list = []
        self._lock = threading.Lock()
        self._stop = False
        self._done = 0
    def set_queue(self, packages):
        with self._lock: self._queue = list(packages)
    def stop(self):
        self._stop = True
    def _next(self):
        with self._lock:
            return self._queue.pop(0) if self._queue else None
    def _loop(self):
        idle_since = None
        while not self._stop:
            pkg = self._next()
            if pkg is None:
                # Encerra quando a fila permanece vazia; evita threads daemon
                # eternas que deixam o worker preso como "em execução".
                if idle_since is None: idle_since = time.monotonic()
                if time.monotonic() - idle_since >= 0.75: break
                time.sleep(0.1)
                continue
            idle_since = None
            t0 = time.time()
            try: label, icon = fetch_app_info(self.adb_cmd, self.aapt, pkg)
            except Exception as e:
                label, icon = "", ""
                log(f"ERRO nome/ícone {pkg}: {e}")
            log(f"TEMPO {pkg}: {time.time() - t0:.2f}s")
            with self._lock:
                self._done += 1; done = self._done; pending = len(self._queue)
            self.item.emit(pkg, label, icon, done, done + pending)
    def run(self):
        threads = [threading.Thread(target=self._loop, daemon=True) for _ in range(self.PARALLEL)]
        for th in threads: th.start()
        for th in threads: th.join()

class InstallBridge(QObject):
    """Leva mensagens da thread de instalação para a interface (sinal entre threads)."""
    text = Signal(str)

class SizeItem(QTableWidgetItem):
    """Ordena pelo valor numérico guardado em Qt.UserRole + 2."""
    def __lt__(self, other):
        return (self.data(Qt.UserRole + 2) or 0) < (other.data(Qt.UserRole + 2) or 0)

class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event): event.ignore()

class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event): event.ignore()

def make_card(title: str, hint: str = ""):
    frame = QFrame(); frame.setObjectName("Card")
    lay = QVBoxLayout(frame); lay.setContentsMargins(18, 16, 18, 16); lay.setSpacing(10)
    head = QLabel(title); head.setObjectName("CardTitle"); lay.addWidget(head)
    if hint:
        h = QLabel(hint); h.setObjectName("CardHint"); h.setWordWrap(True); lay.addWidget(h)
    return frame, lay

def make_tile(caption: str):
    frame = QFrame(); frame.setObjectName("Tile")
    lay = QVBoxLayout(frame); lay.setContentsMargins(14, 12, 14, 12); lay.setSpacing(2)
    cap = QLabel(caption); cap.setObjectName("StatLabel")
    val = QLabel("—"); val.setObjectName("StatValue"); val.setWordWrap(True)
    lay.addWidget(cap); lay.addWidget(val)
    return frame, val

def make_button(text="", object_name="", tooltip=""):
    b = QPushButton(text)
    if object_name: b.setObjectName(object_name)
    if tooltip: b.setToolTip(tooltip)
    b.setCursor(Qt.PointingHandCursor)
    return b

class TextDialog(QDialog):
    def __init__(self, parent, title, text):
        super().__init__(parent); self.setWindowTitle(title); self.resize(640, 480)
        lay = QVBoxLayout(self)
        view = QPlainTextEdit(); view.setReadOnly(True); view.setPlainText(text); lay.addWidget(view)
        bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(self.reject); lay.addWidget(bb)

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent); self.setWindowTitle(t("Configurações")); self.setMinimumWidth(560)
        lay = QVBoxLayout(self); grid = QGridLayout(); grid.setSpacing(8)
        self.fields: dict = {}
        for i, (key, label, kind) in enumerate([("scrcpy", t("Caminho do scrcpy.exe"), "file"),
                                                ("aapt", t("Caminho do aapt.exe"), "file"),
                                                ("backup_dir", t("Pasta padrão de backups"), "dir")]):
            grid.addWidget(QLabel(label), i * 2, 0, 1, 2)
            edit = QLineEdit(str(SETTINGS.get(key, ""))); self.fields[key] = edit
            btn = make_button(t("Escolher"))
            btn.clicked.connect(lambda _=False, e=edit, k=kind: self._browse(e, k))
            grid.addWidget(edit, i * 2 + 1, 0); grid.addWidget(btn, i * 2 + 1, 1)
        grid.addWidget(QLabel(t("Intervalo do monitoramento (segundos)")), 6, 0, 1, 2)
        self.monitor = NoWheelSpinBox(); self.monitor.setRange(2, 60); self.monitor.setValue(int(SETTINGS.get("monitor_s", 5)))
        grid.addWidget(self.monitor, 7, 0)
        grid.addWidget(QLabel(t("URL de verificação de atualização (opcional)")), 8, 0, 1, 2)
        self.update_url = QLineEdit(str(SETTINGS.get("update_url", ""))); grid.addWidget(self.update_url, 9, 0, 1, 2)
        upd = make_button(t("Verificar atualização")); upd.clicked.connect(parent.check_update)
        grid.addWidget(upd, 10, 0, 1, 2)
        lay.addLayout(grid)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._save); bb.rejected.connect(self.reject); lay.addWidget(bb)
    def _browse(self, edit, kind):
        if kind == "dir":
            path = QFileDialog.getExistingDirectory(self, t("Escolher"), edit.text())
        else:
            path, _ = QFileDialog.getOpenFileName(self, t("Escolher"), edit.text(), t("Executáveis (*.exe);;Todos (*.*)"))
        if path: edit.setText(path)
    def _save(self):
        for key, edit in self.fields.items(): SETTINGS[key] = edit.text().strip()
        SETTINGS["monitor_s"] = self.monitor.value(); SETTINGS["update_url"] = self.update_url.text().strip()
        save_settings(SETTINGS); self.accept()

# ---------------------------------------------------------------- janela principal
class DroidControl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 780); self.setMinimumSize(1020, 660)
        self.dark = bool(SETTINGS.get("dark", True))
        self.device: str | None = None
        self.workers: list[QThread] = []
        self.info_worker: AppInfoWorker | None = None
        self._icon_widgets: list[tuple] = []
        self._app_rows: dict = {}
        self._app_state: dict = {}
        self._app_user: dict = {}
        self._label_cache: dict = {}
        self._last_rows: list | None = None
        self._apps_loaded_for = None
        self._apps_loading = False
        self._display_baseline = None
        self._monitor_busy = False
        self._install_bridge = InstallBridge(); self._install_bridge.text.connect(self._set_install_status)
        self._helper_device = None; self._helper_absent = None; self._helper_busy = False
        self._helper_prompted_devices = set(); self._helper_check_busy = set()
        self._progress_timer = QTimer(self); self._progress_timer.setSingleShot(True)
        self._progress_timer.timeout.connect(self._update_progress)
        self._auto_guard = False; self._last_info = None
        self._entries = None; self._device_models: dict = {}
        self._dev_timer = QTimer(self); self._dev_timer.setInterval(10000); self._dev_timer.timeout.connect(self.refresh_devices)
        self._dev_timer.start()
        # timers criados uma única vez (sobrevivem à reconstrução da interface)
        self._sched_timer = QTimer(self); self._sched_timer.setSingleShot(True)
        self._sched_timer.timeout.connect(self.schedule_app_info)
        self._save_timer = QTimer(self); self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._flush_labels)
        self._monitor_timer = QTimer(self); self._monitor_timer.setInterval(int(SETTINGS.get("monitor_s", 5)) * 1000)
        self._monitor_timer.timeout.connect(self.monitor_tick)
        self._build_ui()
        self.apply_theme()
        self.refresh_devices()

    # ---------- construção (reconstruída ao trocar de idioma)
    def _build_ui(self):
        self._icon_widgets = []
        root = QWidget(); root.setObjectName("Root"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        top = QWidget(); top.setObjectName("TopBar"); top.setFixedHeight(64)
        tl = QHBoxLayout(top); tl.setContentsMargins(20, 0, 16, 0); tl.setSpacing(10)
        brand = QLabel(APP_NAME); brand.setObjectName("Brand"); tl.addWidget(brand)
        tl.addStretch(1)
        tl.addWidget(QLabel(t("Dispositivo")))
        self.device_combo = NoWheelComboBox(); self.device_combo.setMinimumWidth(300)
        self.device_combo.currentIndexChanged.connect(lambda _: self.on_device_changed())
        tl.addWidget(self.device_combo)
        self.refresh_btn = make_button("", "Icon", t("Atualizar lista de dispositivos"))
        self.refresh_btn.clicked.connect(lambda _=False: self.refresh_devices(force=True)); self._bind_icon(self.refresh_btn, "refresh")
        tl.addWidget(self.refresh_btn)
        self.device_pill = QLabel("—"); self.device_pill.setObjectName("Pill"); self.device_pill.setFixedHeight(26)
        self.device_pill.setAlignment(Qt.AlignCenter); tl.addWidget(self.device_pill)
        self.lang_btn = make_button("", "Icon", t("Trocar idioma"))
        self._bind_icon(self.lang_btn, "language")
        self.lang_btn.clicked.connect(self.toggle_language); tl.addWidget(self.lang_btn)
        settings_btn = make_button(t("Configurações"), "Ghost"); settings_btn.clicked.connect(self.open_settings)
        tl.addWidget(settings_btn)
        self.theme_btn = make_button("", "Icon", t("Alternar tema claro/escuro"))
        self.theme_btn.clicked.connect(self.toggle_theme); tl.addWidget(self.theme_btn)
        outer.addWidget(top)

        body = QWidget(); bl = QHBoxLayout(body); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0)
        self.sidebar = QListWidget(); self.sidebar.setObjectName("Sidebar"); self.sidebar.setFixedWidth(190)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.stack = QStackedWidget()
        self._side_icon_names = ["mobile", "apps", "build", "code"]
        for title, page in [(t("Visão geral"), self._page_overview()), (t("Aplicativos"), self._page_apps()),
                            (t("Ferramentas"), self._page_tools()), (t("Console"), self._page_console())]:
            self.stack.addWidget(page)
            item = QListWidgetItem(title); item.setSizeHint(QSize(170, 42)); self.sidebar.addItem(item)
        self.sidebar.currentRowChanged.connect(self._page_changed)
        bl.addWidget(self.sidebar); bl.addWidget(self.stack, 1)
        outer.addWidget(body, 1)
        self.statusBar().showMessage(t("Pronto"))
        self._refresh_icons()

    def _scroll(self, widget):
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame); sc.setWidget(widget)
        return sc

    def _page_overview(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(24, 22, 24, 22); lay.setSpacing(16)
        head = QLabel(t("Visão geral")); head.setObjectName("PageTitle"); lay.addWidget(head)
        grid = QGridLayout(); grid.setSpacing(12)
        self.tiles = {}
        for i, (key, caption) in enumerate([("model", t("Modelo")), ("android", t("Versão do Android")),
                                            ("serial", t("Número de série")), ("storage", t("Armazenamento")),
                                            ("security", t("Patch de segurança")), ("ip", t("IP do Wi-Fi"))]):
            frame, val = make_tile(caption); self.tiles[key] = val
            grid.addWidget(frame, i // 2, i % 2)
        lay.addLayout(grid)

        mon = QHBoxLayout(); mon.setSpacing(12)
        ram_card, rl = make_card(t("Memória RAM"))
        rh = QHBoxLayout(); rh.setSpacing(8)
        self.ram_icon = QLabel(); self._bind_icon_label(self.ram_icon, "memory")
        self.ram_label = QLabel("—"); self.ram_label.setObjectName("BigValue")
        rh.addWidget(self.ram_icon); rh.addWidget(self.ram_label); rh.addStretch(1)
        rl.addLayout(rh)
        self.ram_bar = QProgressBar(); self.ram_bar.setRange(0, 100); self.ram_bar.setValue(0); self.ram_bar.setTextVisible(False)
        rl.addWidget(self.ram_bar)
        mon.addWidget(ram_card, 1)

        batt_card, bl2 = make_card(t("Bateria"))
        bh = QHBoxLayout(); bh.setSpacing(8)
        self.batt_icon = QLabel(); self._bind_icon_label(self.batt_icon, "battery")
        self.batt_label = QLabel("—"); self.batt_label.setObjectName("BigValue")
        bh.addWidget(self.batt_icon); bh.addWidget(self.batt_label); bh.addStretch(1)
        bl2.addLayout(bh)
        self.temp_label = QLabel(t("Temperatura da bateria") + ": —"); self.temp_label.setObjectName("CardHint")
        bl2.addWidget(self.temp_label)
        mon.addWidget(batt_card, 1)
        lay.addLayout(mon)

        actions, al = make_card(t("Ações"), t("Espelhamento usa o scrcpy; reinício envia o comando ao aparelho."))
        row = QHBoxLayout(); row.setSpacing(10)
        mirror = make_button(t("Espelhar tela"), "Primary"); mirror.clicked.connect(self.launch_scrcpy)
        self._bind_icon(mirror, "mobile", "accent_text")
        shot = make_button(t("Captura de tela")); shot.clicked.connect(self.take_screenshot)
        self._bind_icon(shot, "download")
        refresh = make_button(t("Atualizar informações")); refresh.clicked.connect(self.refresh_device_details)
        self._bind_icon(refresh, "refresh")
        for b in (mirror, shot, refresh): row.addWidget(b)
        row.addStretch(1); al.addLayout(row)
        rr = QHBoxLayout(); rr.setSpacing(10)
        self.reboot_mode = NoWheelComboBox()
        for label, mode in [(t("Sistema normal"), ""), (t("Recovery"), "recovery"),
                            (t("Bootloader"), "bootloader"), (t("Fastboot"), "fastboot")]:
            self.reboot_mode.addItem(label, mode)
        self.reboot_mode.setMinimumWidth(200)
        reboot = make_button(t("Reiniciar"), "Danger")
        reboot.clicked.connect(lambda: self.reboot(self.reboot_mode.currentData()))
        rr.addWidget(QLabel(t("Reiniciar para:"))); rr.addWidget(self.reboot_mode); rr.addWidget(reboot); rr.addStretch(1)
        al.addLayout(rr)
        lay.addWidget(actions)
        lay.addStretch(1)
        return self._scroll(w)

    def _page_apps(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(24, 22, 24, 22); lay.setSpacing(12)
        head = QLabel(t("Aplicativos")); head.setObjectName("PageTitle"); lay.addWidget(head)
        bar = QHBoxLayout(); bar.setSpacing(8)
        self.app_filter = QLineEdit(); self.app_filter.setPlaceholderText(t("Buscar por nome ou pacote…"))
        self.app_filter.textChanged.connect(self.filter_apps); bar.addWidget(self.app_filter, 1)
        self.app_state = NoWheelComboBox()
        self.app_state_keys = ["Todos", "Ativados", "Desativados", "Excluídos"]
        self.app_state.addItems([t(k) for k in self.app_state_keys])
        self.app_state.setMinimumWidth(130); self.app_state.currentIndexChanged.connect(self.filter_apps)
        bar.addWidget(self.app_state)
        self.app_type = NoWheelComboBox(); self.app_type.addItems([t("Todos os tipos"), t("Usuário"), t("Sistema")])
        self.app_type.setMinimumWidth(130); self.app_type.currentIndexChanged.connect(self.filter_apps)
        bar.addWidget(self.app_type)
        self.app_min = NoWheelSpinBox(); self.app_min.setRange(0, 10240); self.app_min.setSuffix(" MB")
        self.app_min.setToolTip(t("Tamanho mínimo")); self.app_min.setPrefix(t("Mín.") + " ")
        self.app_min.valueChanged.connect(self.filter_apps); bar.addWidget(self.app_min)
        self.apps_refresh_btn = make_button("", tooltip=t("Atualiza os aplicativos, nomes, ícones e recomendações."))
        self.apps_refresh_btn.setAccessibleName(t("Atualizar")); self.apps_refresh_btn.setFixedWidth(40)
        self.apps_refresh_btn.clicked.connect(self.refresh_apps_and_recommendations)
        self._bind_icon(self.apps_refresh_btn, "refresh"); bar.addWidget(self.apps_refresh_btn)
        clear_btn = make_button(t("Limpar cache de todos"), "Danger", t("Remove o cache de todos os aplicativos do aparelho"))
        clear_btn.clicked.connect(self.clear_cache_all); self._bind_icon(clear_btn, "delete", "danger")
        bar.addWidget(clear_btn)
        lay.addLayout(bar)

        self.apps_progress_wrap = QWidget(); pw = QHBoxLayout(self.apps_progress_wrap); pw.setContentsMargins(0, 0, 0, 0)
        self.apps_progress_label = QLabel(""); self.apps_progress_label.setObjectName("Muted")
        self.apps_progress = QProgressBar(); self.apps_progress.setTextVisible(False)
        pw.addWidget(self.apps_progress_label); pw.addWidget(self.apps_progress, 1)
        self.apps_progress_wrap.hide(); lay.addWidget(self.apps_progress_wrap)

        body = QHBoxLayout(); body.setSpacing(12)
        self.apps_table = QTableWidget(0, 6)
        # A primeira célula do cabeçalho funciona como o controle "Selecionar todos",
        # ficando exatamente junto dos títulos da tabela.
        self.apps_table.setHorizontalHeaderLabels(["", t("Ícone"), t("Aplicativo"), t("Pacote"), t("Tamanho"), t("Recomendação")])
        select_header = self.apps_table.horizontalHeaderItem(0)
        select_header.setIcon(svg_icon("checkbox_outline", PALETTES["dark" if self.dark else "light"]["text"], 18))
        select_header.setToolTip(t("Selecionar ou desmarcar todos os aplicativos visíveis"))
        self._select_all_header_item = select_header
        hh = self.apps_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.sectionClicked.connect(lambda section: self.check_all_visible() if section == 0 else None)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        vh = self.apps_table.verticalHeader(); vh.setDefaultSectionSize(40); vh.setVisible(False)
        self.apps_table.setShowGrid(False)
        self.apps_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.apps_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.apps_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.apps_table.setIconSize(QSize(32, 32)); self.apps_table.setAlternatingRowColors(True)
        self.apps_table.setColumnWidth(0, 38)
        self.apps_table.setColumnWidth(1, 48)
        self.apps_table.verticalHeader().setDefaultSectionSize(42)
        self.apps_table.setSortingEnabled(True)
        self.apps_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.apps_table.customContextMenuRequested.connect(self.app_context_menu)
        self.apps_table.cellClicked.connect(self._apps_cell_clicked)
        self.apps_table.itemChanged.connect(self._update_selection_hint)
        self.apps_table.itemDoubleClicked.connect(self._show_app_recommendation)
        self.apps_table.verticalScrollBar().valueChanged.connect(lambda _: self._sched_timer.start(500))
        body.addWidget(self.apps_table, 1)

        side, sl = make_card(t("Ações nos selecionados"),
                             t("Marque os apps na coluna ✔ (ou selecione linhas).") + " " +
                             t("Os apps de sistema só são buscados quando aparecem na tela."))
        self.apps_side_hint = QLabel(t("Nenhum app marcado.")); self.apps_side_hint.setObjectName("Info")
        sl.addWidget(self.apps_side_hint)
        for label, icon, role, cb in [
            (t("Forçar parada"), "crop_square", "text", self.force_stop),
            (t("Desativar"), "toggle_off", "text", self.disable_app),
            (t("Reativar"), "toggle_on", "text", self.enable_app),
            (t("Salvar APK no PC"), "download", "text", self.backup_apk),
            (t("Backup de dados"), "download", "text", self.data_backup),
            (t("Desinstalar para usuário"), "delete", "danger", self.uninstall_app),
        ]:
            b = make_button(label, "Danger" if role == "danger" else "SideAction")
            b.clicked.connect(cb); self._bind_icon(b, icon, role); sl.addWidget(b)
        sl.addStretch(1)
        side.setFixedWidth(270)
        body.addWidget(side)
        lay.addLayout(body, 1)
        if self._last_rows is not None:
            self._apps_result(self._last_rows, None)
        return w

    def _page_debloat(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(24, 22, 24, 22); lay.setSpacing(12)
        head = QLabel(t("Debloat Android")); head.setObjectName("PageTitle"); lay.addWidget(head)
        hint = QLabel(t("Compare os aplicativos com a lista comunitária. Clique duas vezes em um cartão para ler a descrição completa. Aplicativos classificados como Inseguro não podem ser selecionados para remoção."))
        hint.setObjectName("Info"); hint.setWordWrap(True); lay.addWidget(hint)
        bar = QHBoxLayout(); bar.setSpacing(8)
        self.debloat_filter = QLineEdit(); self.debloat_filter.setPlaceholderText(t("Buscar nome, pacote ou descrição…"))
        self.debloat_filter.textChanged.connect(self.filter_debloat); bar.addWidget(self.debloat_filter, 1)
        self.debloat_risk = NoWheelComboBox(); self.debloat_risk.addItems([t("Todos os riscos"), t("Recomendado"), t("Atenção"), t("Especialista"), t("Inseguro"), t("Não listado")])
        self.debloat_risk.currentIndexChanged.connect(self.filter_debloat); bar.addWidget(self.debloat_risk)
        scan = make_button(t("Escanear novamente"), "Primary"); scan.clicked.connect(self.scan_debloat); bar.addWidget(scan)
        lay.addLayout(bar)
        statusrow = QHBoxLayout()
        self.debloat_status = QLabel(t("Conecte um Android autorizado e clique em Escanear novamente.")); self.debloat_status.setObjectName("CardHint")
        self.debloat_count = QLabel(t("Selecionados: 0")); self.debloat_count.setObjectName("CardHint")
        statusrow.addWidget(self.debloat_status, 1); statusrow.addWidget(self.debloat_count); lay.addLayout(statusrow)
        self.debloat_grid = QListWidget(); self.debloat_grid.setViewMode(QListWidget.IconMode)
        self.debloat_grid.setResizeMode(QListWidget.Adjust); self.debloat_grid.setMovement(QListWidget.Static)
        self.debloat_grid.setWrapping(True); self.debloat_grid.setWordWrap(True); self.debloat_grid.setSpacing(10)
        self.debloat_grid.setGridSize(QSize(180, 132)); self.debloat_grid.setIconSize(QSize(48, 48))
        self.debloat_grid.setSelectionMode(QAbstractItemView.NoSelection)
        self.debloat_grid.itemChanged.connect(self._update_debloat_count)
        self.debloat_grid.itemDoubleClicked.connect(self._show_debloat_description)
        lay.addWidget(self.debloat_grid, 1)
        foot = QHBoxLayout(); self.debloat_select_recommended = make_button(t("Marcar recomendados")); self.debloat_select_recommended.clicked.connect(self.select_debloat_recommended)
        self.debloat_clear = make_button(t("Desmarcar todos")); self.debloat_clear.clicked.connect(self.clear_debloat_selection)
        self.debloat_remove = make_button(t("Desinstalar selecionados"), "Danger"); self.debloat_remove.clicked.connect(self.remove_debloat_selected)
        foot.addWidget(self.debloat_select_recommended); foot.addWidget(self.debloat_clear); foot.addStretch(1); foot.addWidget(self.debloat_remove); lay.addLayout(foot)
        self._debloat_rows = []
        return w

    def scan_debloat(self):
        """Carrega a base comunitária em segundo plano e aplica recomendações na aba Aplicativos."""
        if getattr(self, "_recommendations_loading", False): return
        self._recommendations_loading = True
        if hasattr(self, "apps_refresh_btn"):
            self.apps_refresh_btn.setToolTip(t("Carregando recomendações…"))
        def work():
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            list_path = CACHE_DIR / "uad_lists.json"
            try:
                req = urllib.request.Request("https://raw.githubusercontent.com/Universal-Debloater-Alliance/universal-android-debloater-next-generation/main/resources/assets/uad_lists.json", headers={"User-Agent": "DroidControl"})
                with urllib.request.urlopen(req, timeout=8) as response:
                    raw = response.read(8 * 1024 * 1024 + 1)
                if len(raw) > 8 * 1024 * 1024: raise ValueError("Lista de recomendações excedeu o limite de tamanho.")
                parsed = json.loads(raw.decode("utf-8"))
                if not isinstance(parsed, dict): raise ValueError("Formato inesperado da lista.")
                list_path.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
                source = "online"
            except Exception:
                if list_path.exists():
                    try: parsed = json.loads(list_path.read_text(encoding="utf-8")); source = "cache"
                    except Exception: parsed = {}; source = "indisponível"
                else: parsed = {}; source = "indisponível"
            rows = []
            for pkg, entry in (parsed.items() if isinstance(parsed, dict) else []):
                entry = entry if isinstance(entry, dict) else {}
                rows.append({"pkg": pkg, "removal": str(entry.get("removal", "Unlisted")),
                             "source": str(entry.get("list", "—")),
                             "description": str(entry.get("description", "Sem descrição na base comunitária."))})
            return {"rows": rows, "source": source}
        self.run_async(work, self._debloat_scan_done)

    def _debloat_scan_done(self, result, error):
        self._recommendations_loading = False
        if hasattr(self, "apps_refresh_btn"):
            self.apps_refresh_btn.setToolTip(t("Atualiza os aplicativos, nomes, ícones e recomendações."))
        if error:
            self.statusBar().showMessage(t("Falha ao carregar recomendações: {error}").format(error=error), 8000)
            return
        self._debloat_rows = result["rows"]
        self._recommendation_map = {row["pkg"]: row for row in self._debloat_rows}
        if hasattr(self, "apps_table"):
            # Suspende redesenho enquanto a coluna é atualizada em listas grandes.
            self.apps_table.setUpdatesEnabled(False)
            self.apps_table.blockSignals(True)
            sorting = self.apps_table.isSortingEnabled()
            self.apps_table.setSortingEnabled(False)
            for r in range(self.apps_table.rowCount()):
                pkg_item = self.apps_table.item(r, 3)
                if not pkg_item: continue
                pkg = pkg_item.text()
                rec = self._recommendation_map.get(pkg, {"pkg": pkg, "removal": "Unlisted", "source": "—", "description": t("Sem descrição na base comunitária.")})
                risk = self._debloat_risk(rec.get("removal", "Unlisted"))
                item = QTableWidgetItem(risk); item.setData(Qt.UserRole, pkg); item.setData(Qt.UserRole + 1, rec)
                item.setToolTip(t("Clique duas vezes para ver a descrição completa."))
                if risk == t("Inseguro"): item.setForeground(QColor("#d84a4a"))
                self.apps_table.setItem(r, 5, item)
            self.apps_table.blockSignals(False)
            self.apps_table.setSortingEnabled(sorting)
            self.apps_table.setUpdatesEnabled(True)
        self.statusBar().showMessage(t("Recomendações carregadas: {n} pacotes · origem: {source}").format(n=len(self._debloat_rows), source=result["source"]), 7000)
        self.filter_apps()
        self._update_selection_hint()

    def _show_app_recommendation(self, item):
        row = item.row()
        pkg_item = self.apps_table.item(row, 3)
        if not pkg_item: return
        pkg = pkg_item.text()
        data = self._recommendation_map.get(pkg, {"pkg": pkg, "removal": "Unlisted", "source": "—", "description": t("Sem descrição na base comunitária.")})
        risk = self._debloat_risk(data.get("removal", "Unlisted"))
        name = self.apps_table.item(row, 2).text() if self.apps_table.item(row, 2) else pkg
        body = f"{name}\n{pkg}\n\n{t('Recomendação')}: {risk}\n{t('Origem')}: {data.get('source', '—')}\n\n{t('Descrição')}:\n{data.get('description') or t('Sem descrição na base comunitária.')}"
        TextDialog(self, name, body).exec()

    @staticmethod
    def _debloat_risk(removal):
        return {"Recommended": t("Recomendado"), "Advanced": t("Atenção"), "Expert": t("Especialista"), "Unsafe": t("Inseguro")}.get(removal, t("Não listado"))

    def filter_debloat(self, *_):
        if not hasattr(self, "debloat_grid"): return
        query = self.debloat_filter.text().strip().casefold(); selected = self.debloat_risk.currentText()
        self.debloat_grid.blockSignals(True); self.debloat_grid.clear()
        cache = getattr(self, "_label_cache", {})
        for data in self._debloat_rows:
            risk = self._debloat_risk(data["removal"])
            if selected != t("Todos os riscos") and selected != risk: continue
            label_info = cache.get(data["pkg"], {}) if isinstance(cache, dict) else {}
            name = label_info.get("label") or label_info.get("name") or KNOWN_NAMES.get(data["pkg"], data["pkg"])
            desc = data["description"] or t("Sem descrição na base comunitária.")
            if query and query not in (data["pkg"] + " " + name + " " + desc + " " + data["source"]).casefold(): continue
            item = QListWidgetItem(f"{name}\n{data['pkg']}\n{risk}")
            item.setData(Qt.UserRole, data["pkg"]); item.setData(Qt.UserRole + 1, data)
            item.setToolTip(t("Clique duas vezes para ver a descrição completa."))
            icon_path = label_info.get("icon")
            if icon_path and Path(icon_path).is_file():
                pix = QPixmap(str(icon_path))
                if not pix.isNull(): item.setIcon(QIcon(pix))
                else: item.setIcon(svg_icon("apps", "#9CA3AF", 48))
            else: item.setIcon(svg_icon("apps", "#9CA3AF", 48))
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | (Qt.ItemIsUserCheckable if risk != t("Inseguro") else Qt.ItemIsSelectable))
            if risk != t("Inseguro"):
                item.setCheckState(Qt.Unchecked)
            else:
                item.setToolTip(t("Bloqueado: classificação Inseguro.\nClique duas vezes para ler a descrição."))
                item.setForeground(QColor("#d84a4a"))
            self.debloat_grid.addItem(item)
        self.debloat_grid.blockSignals(False); self._update_debloat_count()

    def _show_debloat_description(self, item):
        data = item.data(Qt.UserRole + 1) or {}
        risk = self._debloat_risk(data.get("removal", "Unlisted"))
        title = item.text().splitlines()[0] if item.text() else data.get("pkg", "Aplicativo")
        body = (f"{title}\n{data.get('pkg', '')}\n\n{t('Recomendação')}: {risk}\n{t('Origem')}: {data.get('source', '—')}\n\n{t('Descrição')}:\n{data.get('description') or t('Sem descrição na base comunitária.')}")
        TextDialog(self, title, body).exec()

    def _update_debloat_count(self, *_):
        if not hasattr(self, "debloat_grid"): return
        n = sum(1 for i in range(self.debloat_grid.count()) if self.debloat_grid.item(i).checkState() == Qt.Checked and self._debloat_risk((self.debloat_grid.item(i).data(Qt.UserRole + 1) or {}).get("removal", "Unlisted")) != t("Inseguro"))
        self.debloat_count.setText(t("Selecionados: {n}").format(n=n))

    def select_debloat_recommended(self):
        self.debloat_grid.blockSignals(True)
        for i in range(self.debloat_grid.count()):
            item = self.debloat_grid.item(i)
            if self._debloat_risk((item.data(Qt.UserRole + 1) or {}).get("removal", "Unlisted")) == t("Recomendado"):
                item.setCheckState(Qt.Checked)
        self.debloat_grid.blockSignals(False); self._update_debloat_count()

    def clear_debloat_selection(self):
        self.debloat_grid.blockSignals(True)
        for i in range(self.debloat_grid.count()):
            item = self.debloat_grid.item(i)
            if item.flags() & Qt.ItemIsUserCheckable: item.setCheckState(Qt.Unchecked)
        self.debloat_grid.blockSignals(False); self._update_debloat_count()

    def remove_debloat_selected(self):
        pkgs = []
        for i in range(self.debloat_grid.count()):
            item = self.debloat_grid.item(i)
            data = item.data(Qt.UserRole + 1) or {}
            if item.checkState() == Qt.Checked and self._debloat_risk(data.get("removal", "Unlisted")) != t("Inseguro"):
                pkgs.append(item.data(Qt.UserRole))
        if not pkgs:
            QMessageBox.information(self, t("Debloat Android"), t("Marque os pacotes que deseja desinstalar.")); return
        # Defesa em profundidade: nunca permitir remover pacote classificado como Unsafe.
        unsafe = {row["pkg"] for row in self._debloat_rows if self._debloat_risk(row.get("removal", "Unlisted")) == t("Inseguro")}
        if any(pkg in unsafe for pkg in pkgs):
            QMessageBox.warning(self, t("Bloqueado"), t("Aplicativos classificados como Inseguro não podem ser desinstalados pelo Debloat Android.")); return
        # Nunca executa em lote sem confirmação explícita; recomenda-se remover poucos de cada vez.
        warning = t("A remoção de pacotes de sistema pode quebrar funções do aparelho ou impedir a inicialização. Faça backup e remova poucos por vez.")
        if not self.ask_confirm(t("Confirmar desinstalação"), warning + "\n\n" + "\n".join(pkgs[:20]) + (f"\n… +{len(pkgs)-20}" if len(pkgs)>20 else "")): return
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        self.debloat_remove.setEnabled(False)
        def work():
            results = []
            for pkg in pkgs:
                try:
                    out = run_command(adb + ["shell", "pm", "uninstall", "--user", "0", pkg], 120)
                    if any(x in out.lower() for x in ("failure", "error", "exception")): raise RuntimeError(out)
                    results.append((pkg, True, out or "Success"))
                except Exception as e: results.append((pkg, False, str(e)))
            return results
        def done(results, error):
            self.debloat_remove.setEnabled(True)
            if error: QMessageBox.critical(self, t("Erro"), str(error)); return
            ok = sum(1 for _p, success, _msg in results if success)
            self.debloat_status.setText(t("Resultado: {ok}/{total} removidos.").format(ok=ok, total=len(results)))
            details = "\n".join(("OK" if success else "FALHOU") + f" — {pkg}: {msg}" for pkg, success, msg in results)
            QMessageBox.information(self, t("Resultado"), details[:6000])
            self.scan_debloat()
        self.run_async(work, done)

    def _page_tools(self):
        w = QWidget(); outer = QVBoxLayout(w); outer.setContentsMargins(24, 22, 24, 22); outer.setSpacing(14)
        head = QLabel(t("Ferramentas")); head.setObjectName("PageTitle"); outer.addWidget(head)
        grid = QGridLayout(); grid.setSpacing(14)

        inst, il = make_card(t("Instalar APK / XAPK"),
                             t("Aceita APK, XAPK e APKS. Vários arquivos são instalados um a um."))
        self.install_path = QLineEdit(); self.install_path.setPlaceholderText(t("Nenhum arquivo escolhido"))
        self.install_path.setReadOnly(True); il.addWidget(self.install_path)
        self.install_multi = QCheckBox(t("Instalar como pacote dividido (split)")); il.addWidget(self.install_multi)
        self.install_status = QPlainTextEdit(); self.install_status.setObjectName("InstallStatus")
        self.install_status.setReadOnly(True); self.install_status.setMaximumHeight(112)
        self.install_status.setPlaceholderText(t("O andamento da instalação aparecerá aqui."))
        il.addWidget(self.install_status)
        r = QHBoxLayout()
        browse = make_button(t("Escolher…")); browse.clicked.connect(self.pick_install)
        go = make_button(t("Instalar"), "Primary"); go.clicked.connect(self.install_files)
        r.addWidget(browse); r.addStretch(1); r.addWidget(go); il.addLayout(r)
        grid.addWidget(inst, 0, 0)

        files, fl = make_card(t("Arquivos"), t("Escolha um arquivo para enviá-lo à pasta Download do aparelho."))
        send = make_button(t("Escolher arquivo e enviar"), "Primary"); send.clicked.connect(self.push_file)
        fl.addWidget(send); fl.addStretch(1)
        grid.addWidget(files, 0, 1)

        disp, dl = make_card(t("Tela"), t("A resolução e o DPI atuais são lidos automaticamente ao conectar o aparelho."))
        top = QHBoxLayout(); top.setSpacing(8)
        self.lock_btn = make_button("", "Icon", t("Proporção automática: a largura define altura e DPI (clique para desativar)"))
        self.lock_btn.setCheckable(True); self.lock_btn.setChecked(True)
        self.lock_btn.icon_fn = lambda: "lock" if self.lock_btn.isChecked() else "lock_open"
        self.lock_btn.toggled.connect(lambda _c: self._apply_icon(self.lock_btn, "lock", "text"))
        self._bind_icon(self.lock_btn, "lock")
        top.addWidget(QLabel(t("Proporção automática"))); top.addWidget(self.lock_btn); top.addStretch(1)
        dl.addLayout(top)
        spins = QHBoxLayout(); spins.setSpacing(8)
        self.res_w = NoWheelSpinBox(); self.res_w.setRange(320, 4096); self.res_w.setSuffix(" px")
        self.res_h = NoWheelSpinBox(); self.res_h.setRange(320, 4096); self.res_h.setSuffix(" px")
        self.dpi = NoWheelSpinBox(); self.dpi.setRange(80, 1000); self.dpi.setSuffix(" dpi")
        self.res_w.valueChanged.connect(self._on_width_changed)
        for label, sp in [(t("Largura"), self.res_w), (t("Altura"), self.res_h), ("DPI", self.dpi)]:
            col = QVBoxLayout(); col.addWidget(QLabel(label)); col.addWidget(sp); spins.addLayout(col)
        dl.addLayout(spins)
        dr = QHBoxLayout()
        reset = make_button(t("Restaurar padrão")); reset.clicked.connect(self.reset_display)
        apply_btn = make_button(t("Aplicar"), "Primary"); apply_btn.clicked.connect(self.set_resolution_and_density)
        dr.addWidget(reset); dr.addStretch(1); dr.addWidget(apply_btn); dl.addLayout(dr)
        grid.addWidget(disp, 1, 0, 1, 2)
        wifi, wl = make_card(t("Conexão sem fio (ADB Wi-Fi)"),
                             t("Ative a depuração por TCP/IP com o cabo conectado (porta 5555), depois conecte pelo IP do aparelho."))
        self.wifi_addr = QLineEdit(); self.wifi_addr.setPlaceholderText("192.168.0.10:5555"); wl.addWidget(self.wifi_addr)
        wr = QHBoxLayout(); wr.setSpacing(8)
        for label, kind, obj in [(t("Ativar TCP/IP"), "tcpip", ""), (t("Conectar"), "connect", "Primary"),
                                 (t("Desconectar"), "disconnect", "")]:
            b = make_button(label, obj); b.clicked.connect(lambda _=False, k=kind: self.wifi_action(k)); wr.addWidget(b)
        wr.addStretch(1); wl.addLayout(wr)
        grid.addWidget(wifi, 2, 0)
        outer.addLayout(grid)
        outer.addStretch(1)
        return self._scroll(w)

    def _page_console(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(24, 22, 24, 22); lay.setSpacing(12)
        head = QLabel(t("Console")); head.setObjectName("PageTitle"); lay.addWidget(head)
        hint = QLabel(t("Execute comandos ADB ou Fastboot. Digite com ou sem o prefixo (“pm list packages” ou “adb shell pm list packages”). “shell” abre um terminal interativo. Cada execução fica registrada no log."))
        hint.setObjectName("Info"); hint.setWordWrap(True); lay.addWidget(hint)
        row = QHBoxLayout(); row.setSpacing(8)
        self.console_mode = NoWheelComboBox(); self.console_mode.addItems(["ADB", "Fastboot"]); self.console_mode.setFixedWidth(120)
        self.console_command = QLineEdit(); self.console_command.setPlaceholderText(t("Ex.: adb shell pm list packages"))
        self.console_command.returnPressed.connect(self.run_console_command)
        run_btn = make_button(t("Executar"), "Primary"); run_btn.clicked.connect(self.run_console_command)
        row.addWidget(self.console_mode); row.addWidget(self.console_command, 1); row.addWidget(run_btn)
        lay.addLayout(row)
        acts = QHBoxLayout(); acts.setSpacing(8)
        shell_btn = make_button(t("Abrir terminal ADB")); shell_btn.clicked.connect(self.open_adb_terminal)
        clear = make_button(t("Limpar log"), "Ghost"); clear.clicked.connect(self.clear_logs)
        folder = make_button(t("Abrir pasta de logs"), "Ghost"); folder.clicked.connect(self.open_logs)
        acts.addWidget(shell_btn); acts.addStretch(1); acts.addWidget(clear); acts.addWidget(folder)
        lay.addLayout(acts)
        self.logs_view = QPlainTextEdit(); self.logs_view.setReadOnly(True)
        self.logs_view.setPlaceholderText(t("Os comandos executados e suas saídas aparecerão aqui."))
        lay.addWidget(self.logs_view, 1)
        self.refresh_log()
        return w

    # ---------- ícones que mudam com o tema
    def _bind_icon(self, widget, name, role="text"):
        self._icon_widgets.append((widget, name, role))
        self._apply_icon(widget, name, role)

    def _bind_icon_label(self, label: QLabel, name: str):
        self._icon_widgets.append((label, name, "accent"))
        self._apply_icon(label, name, "accent")

    def _apply_icon(self, widget, name, role):
        p = PALETTES["dark" if self.dark else "light"]
        if getattr(widget, "icon_fn", None): name = widget.icon_fn()
        color = {"text": p["text"], "danger": p["danger"], "accent_text": p["accent_text"],
                 "accent": p["accent"]}.get(role, p["text"])
        if isinstance(widget, QLabel):
            pix = svg_pixmap(name, color, 22)
            if pix: widget.setPixmap(pix)
        else:
            widget.setIcon(svg_icon(name, color)); widget.setIconSize(QSize(18, 18))

    def _refresh_icons(self):
        alive = []
        for widget, name, role in self._icon_widgets:
            try:
                self._apply_icon(widget, name, role); alive.append((widget, name, role))
            except RuntimeError:
                pass
        self._icon_widgets = alive
        p = PALETTES["dark" if self.dark else "light"]
        self.theme_btn.setIcon(svg_icon("light_mode" if self.dark else "dark_mode", p["text"]))
        self.theme_btn.setIconSize(QSize(18, 18))
        if getattr(self, "chart", None) is not None:
            try: self.chart.colors = p; self.chart.update()
            except RuntimeError: pass
        for i, name in enumerate(self._side_icon_names):
            self.sidebar.item(i).setIcon(svg_icon(name, p["text"], 18))
        if hasattr(self, "apps_table"):
            for row in range(self.apps_table.rowCount()):
                item = self.apps_table.item(row, 0)
                if item is not None:
                    item.setIcon(svg_icon("checkbox_checked" if bool(item.data(Qt.UserRole + 1)) else "checkbox_outline", p["text"], 18))
            self._update_select_all_header_icon()

    def apply_theme(self):
        p = PALETTES["dark" if self.dark else "light"]
        qss = STYLE
        for key in sorted(p, key=len, reverse=True):
            qss = qss.replace("@" + key, p[key])
        self.setStyleSheet(qss)
        self._refresh_icons()

    def toggle_theme(self):
        self.dark = not self.dark
        SETTINGS["dark"] = self.dark; save_settings(SETTINGS)
        self.apply_theme()

    def toggle_language(self):
        global LANG
        LANG = "en" if LANG == "pt" else "pt"
        SETTINGS["lang"] = LANG; save_settings(SETTINGS)
        current = self.sidebar.currentRow() if hasattr(self, "sidebar") else 0
        self._build_ui()
        self.sidebar.setCurrentRow(max(0, current))
        self._restore_devices()

    def _restore_devices(self):
        entries = self._entries or []
        self.device_combo.blockSignals(True); self.device_combo.clear()
        for serial, state in entries:
            self.device_combo.addItem(f"{serial}  ·  {state}", serial if state == "device" else None)
        index = next((i for i in range(self.device_combo.count()) if self.device_combo.itemData(i) == self.device), 0)
        if self.device_combo.count(): self.device_combo.setCurrentIndex(index)
        self.device_combo.blockSignals(False)
        authorized = sum(1 for _s, st in entries if st == "device")
        self.device_pill.setText(t("{n} autorizado(s)").format(n=authorized) if authorized else t("Nenhum dispositivo"))
        if self._last_info: self._device_details_result(self._last_info, None)

    # ---------- utilitários de execução
    def adb(self) -> list:
        tool = find_tool("adb")
        if not tool: raise RuntimeError(t("adb não encontrado. Instale o Platform Tools ou coloque adb.exe na pasta platform-tools/."))
        args = [tool]
        if self.device: args += ["-s", self.device]
        return args

    def fastboot(self) -> list:
        tool = find_tool("fastboot")
        if not tool: raise RuntimeError(t("fastboot não encontrado. Coloque fastboot.exe na pasta platform-tools/."))
        return [tool]

    def ensure_device(self):
        if not self.device: raise RuntimeError(t("Selecione um dispositivo autorizado."))

    def warn(self, title, message):
        QMessageBox.warning(self, t(title), t(message) if message in TR else message)

    def ask_confirm(self, title, message) -> bool:
        return QMessageBox.question(self, title, message, QMessageBox.Yes | QMessageBox.Cancel,
                                    QMessageBox.Cancel) == QMessageBox.Yes

    def run_async(self, fn, callback):
        worker = Worker(fn); self.workers.append(worker)
        worker.done.connect(callback)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.start()

    def note(self, text: str):
        log(text)
        self.statusBar().showMessage(text.splitlines()[0][:200] if text else "", 6000)

    def _connection_lost(self):
        self.statusBar().showMessage(t("Dispositivo desconectado durante a operação."), 8000)
        self.refresh_devices()

    def show_result(self, result, error):
        if error:
            if is_connection_error(error): self._connection_lost()
            self.statusBar().showMessage(t("Operação falhou"), 5000)
            QMessageBox.critical(self, t("Erro"), error)
        else:
            self.note(str(result) if result else t("Operação concluída."))

    def run_tool(self, label, fn):
        self.note(f"{label}…")
        self.run_async(fn, self.show_result)

    # ---------- dispositivos
    def refresh_devices(self, force=False):
        tool = find_tool("adb")
        if not tool:
            self.device_pill.setText(t("ADB não encontrado")); return
        try: output = run_command([tool, "devices"], 20)
        except Exception as e:
            self.device_pill.setText(t("Erro no ADB")); self.statusBar().showMessage(str(e), 6000); return
        entries = parse_devices(output)
        if entries == self._entries and not force: return
        previous = self.device
        gone = [s_ for s_, _ in (self._entries or []) if s_ not in {x for x, _ in entries}]
        self._entries = entries
        self.device_combo.blockSignals(True); self.device_combo.clear()
        for serial, state in entries:
            self.device_combo.addItem(f"{serial}  ·  {state}", serial if state == "device" else None)
        self.device_combo.blockSignals(False)
        index = next((i for i in range(self.device_combo.count()) if self.device_combo.itemData(i) == previous), 0)
        if self.device_combo.count(): self.device_combo.setCurrentIndex(index)
        for s_ in gone: self.note(t("Dispositivo desconectado: {serial}").format(serial=s_))
        self.on_device_changed()
        self._fill_devices_list()
        self._describe_devices(tool, entries)

    def _describe_devices(self, tool, entries):
        def work():
            models = {}
            for serial, state in entries:
                if state != "device": continue
                try: models[serial] = run_command([tool, "-s", serial, "shell", "getprop", "ro.product.model"], 10)
                except Exception: models[serial] = ""
            return models
        def done(models, error):
            if models:
                self._device_models.update(models); self._fill_devices_list()
        self.run_async(work, done)

    def _fill_devices_list(self):
        lst = getattr(self, "devices_list", None)
        if lst is None: return
        try:
            lst.clear()
            for serial, state in (self._entries or []):
                model = self._device_models.get(serial, "")
                item = QListWidgetItem(f"{model or serial}  ·  {serial}  ·  {state}")
                item.setData(Qt.UserRole, serial); lst.addItem(item)
                if serial == self.device: lst.setCurrentItem(item)
        except RuntimeError:
            pass

    def _select_device_item(self, item):
        serial = item.data(Qt.UserRole)
        idx = next((i for i in range(self.device_combo.count()) if self.device_combo.itemData(i) == serial), -1)
        if idx >= 0: self.device_combo.setCurrentIndex(idx)

    def on_device_changed(self):
        self.device = self.device_combo.currentData() if self.device_combo.count() else None
        authorized = sum(1 for i in range(self.device_combo.count()) if self.device_combo.itemData(i))
        self.device_pill.setText(t("{n} autorizado(s)").format(n=authorized) if authorized else t("Nenhum dispositivo"))
        self._apps_loaded_for = None
        self._apps_loading = False
        self._display_baseline = None
        if self.device:
            self.refresh_device_details(); self.read_display()
            self._check_helper_on_start(self.device)
            if self.stack.currentIndex() == 1: self.load_apps()
            self._page_changed(self.stack.currentIndex())
        else:
            self._monitor_timer.stop()
            for val in self.tiles.values(): val.setText("—")
            self.ram_label.setText("—"); self.ram_bar.setValue(0)
            self.batt_label.setText("—")
            self.apps_table.setRowCount(0)

    def _check_helper_on_start(self, serial):
        """Verifica o Helper em segundo plano e oferece instalação uma única vez por dispositivo."""
        if not serial or serial in self._helper_prompted_devices or serial in self._helper_check_busy:
            return
        tool = find_tool("adb")
        if not tool:
            return
        self._helper_check_busy.add(serial)
        adb = [tool, "-s", serial]
        def work():
            output = run_command(adb + ["shell", "pm", "list", "packages", HELPER_PKG], 20)
            return HELPER_PKG in output
        def done(installed, error):
            self._helper_check_busy.discard(serial)
            if error or self.device != serial:
                return
            if installed:
                self._helper_prompted_devices.add(serial)
                return
            self._helper_prompted_devices.add(serial)
            answer = QMessageBox.question(
                self, t("DroidControl Helper"),
                t("O DroidControl Helper não está instalado neste dispositivo. Deseja instalá-lo agora?"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if answer != QMessageBox.Yes:
                return
            apk = Path(__file__).resolve().parent / "DroidControl-Helper.apk"
            if not apk.is_file():
                QMessageBox.warning(self, t("DroidControl Helper"),
                    t("O arquivo DroidControl-Helper.apk não foi encontrado na mesma pasta do main.py."))
                return
            self.statusBar().showMessage(t("Instalando DroidControl Helper…"))
            def install_work():
                out = run_command(adb + ["install", "-r", str(apk)], 240)
                check_install_output(out)
                # Concede permissões runtime declaradas pelo APK; permissões não
                # declaradas/indisponíveis nessa versão do Android são ignoradas.
                for permission in (
                    "android.permission.READ_EXTERNAL_STORAGE",
                    "android.permission.WRITE_EXTERNAL_STORAGE",
                    "android.permission.READ_MEDIA_IMAGES",
                    "android.permission.READ_MEDIA_VIDEO",
                    "android.permission.READ_MEDIA_VISUAL_USER_SELECTED",
                ):
                    try: run_command(adb + ["shell", "pm", "grant", HELPER_PKG, permission], 12)
                    except Exception: pass
                try: run_command(adb + ["shell", "appops", "set", HELPER_PKG, "MANAGE_EXTERNAL_STORAGE", "allow"], 15)
                except Exception: pass
                return out or t("DroidControl Helper instalado.")
            def installed_done(result, install_error):
                if install_error:
                    QMessageBox.critical(self, t("Erro ao instalar DroidControl Helper"), str(install_error))
                    return
                QMessageBox.information(self, t("DroidControl Helper"),
                    t("DroidControl Helper instalado. Se o Android solicitar uma permissão especial, autorize-a no aparelho."))
                self._helper_absent = None
                if self.stack.currentIndex() == 1:
                    self.load_apps()
            self.run_async(install_work, installed_done)
        self.run_async(work, done)

    def _page_changed(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0 and self.device:
            self.monitor_tick(); self._monitor_timer.start()
        else:
            self._monitor_timer.stop()
        if index == 1:
            if self.device and self._apps_loaded_for != self.device: self.load_apps()
            if not getattr(self, "_debloat_rows", []) and not getattr(self, "_recommendations_loading", False): self.scan_debloat()
        if index == 3: self.refresh_log()

    def refresh_device_details(self):
        if not self.device: return
        try: adb = self.adb()
        except Exception as e: self.statusBar().showMessage(str(e), 6000); return
        def work():
            def sh(*a): return run_command(adb + ["shell", *a], 30)
            def prop(name):
                try: return sh("getprop", name) or "—"
                except Exception: return "—"
            info = {"model": f"{prop('ro.product.manufacturer')} {prop('ro.product.model')}".strip(),
                    "android": prop("ro.build.version.release"), "serial": prop("ro.serialno"), "storage": "—"}
            info["security"] = prop("ro.build.version.security_patch")
            try:
                ipout = sh("ip", "-4", "addr", "show", "wlan0")
                m_ip = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", ipout)
                info["ip"] = m_ip.group(1) if m_ip else "—"
            except Exception:
                info["ip"] = "—"
            try:
                df = sh("df", "-k", "/data").splitlines()
                cols = df[-1].split() if len(df) > 1 else []
                if len(cols) >= 4:
                    total, used, _avail = [int(x) for x in cols[1:4]]
                    info["storage"] = t("{used} GB usados de {total} GB").format(
                        used=f"{used / 1048576:.1f}", total=f"{total / 1048576:.1f}")
            except Exception: pass
            return info
        self.run_async(work, self._device_details_result)

    def _device_details_result(self, info, error):
        if info: self._last_info = info
        if error or not info:
            self.ram_label.setText(t("Não foi possível ler as informações")); return
        self.tiles["model"].setText(info["model"] or "—")
        self.tiles["android"].setText(info["android"])
        self.tiles["serial"].setText(info["serial"])
        self.tiles["storage"].setText(info["storage"])
        self.tiles["security"].setText(info.get("security") or "—")
        self.tiles["ip"].setText(info.get("ip") or "—")

    # ---------- monitoramento (RAM, bateria, temperatura) a cada 5 s
    def monitor_tick(self):
        if not self.device or self._monitor_busy: return
        try: adb = self.adb()
        except Exception: return
        self._monitor_busy = True
        def work():
            out = {}
            try: out["ram"] = parse_meminfo(run_command(adb + ["shell", "cat", "/proc/meminfo"], 15))
            except Exception: out["ram"] = None
            try: out["level"], out["temp"] = parse_battery(run_command(adb + ["shell", "dumpsys", "battery"], 15))
            except Exception: out["level"], out["temp"] = None, None
            return out
        def done(result, error):
            self._monitor_busy = False
            if error and is_connection_error(error): self._connection_lost(); return
            if error or not result: return
            ram_pct = None
            if result.get("ram"):
                used, total = result["ram"]
                self.ram_label.setText(f"{used}/{total}MB")
                ram_pct = round(used * 100 / total) if total else 0
                self.ram_bar.setValue(ram_pct)
            if result.get("level") is not None:
                temp = f"{result['temp']:.1f}" if result.get("temp") is not None else "—"
                self.batt_label.setText(f"{result['level']}%")
                self.temp_label.setText(t("Temperatura da bateria") + f": {temp} °C")
        self.run_async(work, done)

    # ---------- aplicativos
    def refresh_apps_and_recommendations(self):
        """Atualiza a lista local e a base comunitária em workers separados."""
        self.load_apps()
        self.scan_debloat()

    def load_apps(self):
        if getattr(self, "_apps_loading", False):
            return
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        self._apps_loading = True
        if hasattr(self, "apps_refresh_btn"): self.apps_refresh_btn.setEnabled(False)
        self._apps_loaded_for = self.device
        self._helper_device = None; self._helper_absent = None
        self.apps_table.setRowCount(0)
        self.statusBar().showMessage(t("Carregando aplicativos…"))
        def pm(*args): return run_command(adb + ["shell", "pm", "list", "packages", *args], 120)
        def work():
            installed = {}
            for line in pm("-f").splitlines():
                if line.startswith("package:") and "=" in line:
                    path, pkg = line[len("package:"):].rsplit("=", 1)
                    installed[pkg.strip()] = path.strip()
            disabled = {x.replace("package:", "").strip() for x in pm("-d").splitlines() if x.strip()}
            every = {x.replace("package:", "").strip() for x in pm("-u").splitlines() if x.strip()}
            user = {x.replace("package:", "").strip() for x in pm("-3").splitlines() if x.strip()}
            sizes, batch, length = {}, [], 0
            def flush():
                if not batch: return
                quoted = " ".join("'" + p.replace("'", "'\\''") + "'" for p in batch)
                out = run_command(adb + ["shell", f"stat -c '%s %n' {quoted} 2>/dev/null; exit 0"], 120)
                for line in out.splitlines():
                    parts = line.strip().split(" ", 1)
                    if len(parts) == 2 and parts[0].isdigit(): sizes[parts[1]] = int(parts[0])
            cached_info = load_label_cache()
            for pk, path in installed.items():
                ent = cached_info.get(pk, {})
                if ent.get("path") == path and ent.get("size") is not None: sizes[path] = ent["size"]
            for p in installed.values():
                if p in sizes: continue
                if length + len(p) > 300: flush(); batch, length = [], 0
                batch.append(p); length += len(p) + 3
            flush()
            rows = []
            for pkg in sorted(set(installed) | every):
                if pkg not in installed:
                    rows.append({"pkg": pkg, "state": "Excluídos", "size": None, "user": pkg in user})
                else:
                    state = "Desativados" if pkg in disabled else "Ativados"
                    rows.append({"pkg": pkg, "state": state, "size": sizes.get(installed[pkg]), "user": pkg in user, "path": installed[pkg]})
            return rows
        self.run_async(work, self._apps_result)

    def _apps_result(self, rows, error):
        self._apps_loading = False
        if hasattr(self, "apps_refresh_btn"): self.apps_refresh_btn.setEnabled(True)
        if error:
            QMessageBox.critical(self, t("Erro"), error)
            return
        if rows is not None: self._last_rows = rows
        if not hasattr(self, "apps_table") or rows is None: return
        self._app_rows, self._app_state = {}, {}
        self._label_cache = load_label_cache(); cache = self._label_cache
        self._recommendation_map = {row.get("pkg"): row for row in getattr(self, "_debloat_rows", []) if row.get("pkg")}
        self.apps_table.setSortingEnabled(False)
        self.apps_table.blockSignals(True)
        self.apps_table.setUpdatesEnabled(False)
        self.apps_table.setRowCount(len(rows))
        palette = PALETTES["dark" if self.dark else "light"]
        for r, row in enumerate(rows):
            pkg, state, size = row["pkg"], row["state"], row["size"]
            cached = cache.get(pkg, {})
            label = cached.get("label") or KNOWN_NAMES.get(pkg, pkg)
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check.setData(Qt.UserRole, pkg); check.setData(Qt.UserRole + 1, False)
            check.setIcon(svg_icon("checkbox_outline", palette["text"], 18))
            check.setToolTip(t("Clique para selecionar este aplicativo"))
            icon_item = QTableWidgetItem(); icon_item.setTextAlignment(Qt.AlignCenter)
            icon_item.setIcon(self._app_icon(label, cached.get("icon")))
            name_item = QTableWidgetItem(label); name_item.setToolTip(f"{pkg}\n{t('Estado: {state}').format(state=t(state))}")
            package_item = QTableWidgetItem(pkg)
            size_item = SizeItem(fmt_size(size)); size_item.setData(Qt.UserRole + 2, size or 0)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rec = self._recommendation_map.get(pkg, {"pkg": pkg, "removal": "Unlisted", "source": "—", "description": t("Sem descrição na base comunitária.")})
            risk_text = self._debloat_risk(rec.get("removal", "Unlisted"))
            risk_item = QTableWidgetItem(risk_text); risk_item.setData(Qt.UserRole, pkg)
            risk_item.setData(Qt.UserRole + 1, rec)
            risk_item.setToolTip(t("Clique duas vezes para ver a descrição completa."))
            if risk_text == t("Inseguro"): risk_item.setForeground(QColor("#d84a4a"))
            for c, item in enumerate([check, icon_item, name_item, package_item, size_item, risk_item]):
                self.apps_table.setItem(r, c, item)
            self._app_rows[pkg] = (check, icon_item, name_item)
            self._app_state[pkg] = state
        self._app_user = {r["pkg"]: r.get("user", False) for r in rows}
        for r_ in rows:
            if r_.get("size") is not None:
                ent = self._label_cache.setdefault(r_["pkg"], {})
                ent["size"] = r_["size"]; ent["path"] = r_.get("path", "")
        self._save_timer.start(2000)
        self.apps_table.setUpdatesEnabled(True)
        self.apps_table.blockSignals(False)
        self.apps_table.setSortingEnabled(True)
        self.filter_apps(); self._update_selection_hint()
        self.statusBar().showMessage(t("{n} aplicativos carregados").format(n=len(rows)), 5000)
        self.schedule_app_info()

    def _app_icon(self, label, icon_path=None) -> QIcon:
        if icon_path:
            try:
                path = Path(icon_path)
                if path.is_file():
                    candidate = QPixmap(str(path))
                    if not candidate.isNull():
                        return QIcon(candidate)
            except (OSError, ValueError):
                pass
        pix = QPixmap(32, 32); pix.fill(Qt.transparent)
        painter = QPainter(pix); painter.setRenderHint(QPainter.Antialiasing)
        palette = ["#7C3AED", "#A855F7", "#8B5CF6", "#6D28D9", "#9333EA", "#C026D3"]
        painter.setBrush(QColor(palette[sum(map(ord, label)) % len(palette)]))
        painter.setPen(Qt.NoPen); painter.drawRoundedRect(1, 1, 30, 30, 9, 9)
        painter.setPen(QColor("white")); painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(pix.rect(), Qt.AlignCenter, (label[:1] or "A").upper()); painter.end()
        return QIcon(pix)

    def refresh_app_info(self):
        if not self._app_rows:
            self.statusBar().showMessage(t("Carregue os aplicativos primeiro."), 4000); return
        self.schedule_app_info(force=True)

    def _visible_packages(self):
        table = self.apps_table
        first = table.rowAt(0)
        last = table.rowAt(table.viewport().height() - 1)
        first = 0 if first < 0 else max(0, first - 8)
        last = table.rowCount() - 1 if last < 0 else min(table.rowCount() - 1, last + 8)
        out = []
        for r in range(first, last + 1):
            item = table.item(r, 3)
            if item and not table.isRowHidden(r): out.append(item.text())
        return out

    def schedule_app_info(self, force=False):
        """Usa o helper do aparelho quando instalado (rápido); senão, o modo anterior."""
        if not self._app_rows or not hasattr(self, "apps_table"): return
        if not force and self._helper_device == self.device: return
        if self._helper_absent == self.device or self._helper_busy:
            return self._schedule_native(force)
        try: adb = self.adb()
        except Exception: return self._schedule_native(force)
        self._helper_busy = True
        self.apps_progress_wrap.show(); self.apps_progress.setRange(0, 0)
        self.apps_progress_label.setText(t("Exportando nomes e ícones pelo helper…"))
        def done(entries, error):
            self._helper_busy = False
            if error:
                # Helper instalado mas com erro: mostra o motivo real (não o aviso do aapt)
                self.apps_progress_wrap.hide()
                QMessageBox.warning(self, t("Aviso"), t("Não foi possível obter nomes e ícones pelo helper: {e}").format(e=error))
                return
            if entries is None:
                # Helper não instalado: usa o modo antigo (precisa do aapt)
                self._helper_absent = self.device
                self.apps_progress_wrap.hide()
                # O fluxo atual não depende de aapt: mantém os pacotes listados e
                # usa o identificador como nome até o Helper ser instalado.
                self.statusBar().showMessage(t("DroidControl Helper não instalado; nomes e ícones reais indisponíveis."), 8000)
                return
            self._helper_device = self.device
            n = len(entries)
            missing_icons = False
            sorting = self.apps_table.isSortingEnabled()
            self.apps_table.setSortingEnabled(False)
            self.apps_table.setUpdatesEnabled(False)
            try:
                for i, (pkg, label, icon) in enumerate(entries, 1):
                    self._on_app_info(pkg, label, icon, i, n)
                    if not icon or not Path(icon).is_file():
                        missing_icons = True
                        self._label_cache.setdefault(pkg, {})["v"] = 0
            finally:
                self.apps_table.setUpdatesEnabled(True)
                self.apps_table.setSortingEnabled(sorting)
            self.apps_progress_wrap.hide()
            if missing_icons:
                # O helper pode exportar nomes sem ícones; só então tenta o caminho AAPT.
                self._schedule_native(force=False)
            self.note(t("Nomes e ícones atualizados."))
        self.run_async(lambda: helper_export(adb), done)

    def _schedule_native(self, force=False):
        if not self._app_rows or not hasattr(self, "apps_table"): return
        aapt = find_aapt()
        if not aapt:
            self.statusBar().showMessage(t("Para nomes e ícones reais, coloque aapt.exe (Android SDK Build-Tools) na pasta tools/."), 10000)
            return
        try: adb = self.adb()
        except Exception: return
        cache = self._label_cache
        def needed(p):
            if self._app_state.get(p) == "Excluídos": return False
            entry = cache.get(p, {})
            icon = entry.get("icon")
            icon_ok = bool(icon and Path(icon).is_file())
            return force or entry.get("v") != CACHE_VERSION or not icon_ok
        visible = [p for p in self._visible_packages() if needed(p)]
        seen = set(visible)
        rest = [p for p in self._app_rows if needed(p) and p not in seen and (force or self._app_user.get(p))]
        rest.sort(key=lambda p: not self._app_user.get(p, False))
        order = visible + rest
        worker = self.info_worker
        if worker is None or not worker.isRunning():
            worker = AppInfoWorker(adb, aapt)
            worker.item.connect(self._on_app_info)
            self.info_worker = worker
            self._info_sorting_before = self.apps_table.isSortingEnabled()
            self.apps_table.setSortingEnabled(False)
            worker.set_queue(order)
            worker.finished.connect(self._app_info_worker_finished)
            worker.start()
        else:
            worker.set_queue(order)
        self._update_progress(visible_set=seen | set(self._visible_packages()))

    def _app_info_worker_finished(self):
        if hasattr(self, "apps_table"):
            self.apps_table.setSortingEnabled(bool(getattr(self, "_info_sorting_before", True)))
        if hasattr(self, "_progress_timer"):
            self._progress_timer.start(100)

    def _update_progress(self, visible_set=None):
        if not hasattr(self, "apps_progress_wrap"): return
        if visible_set is None: visible_set = set(self._visible_packages())
        cache = self._label_cache
        targets = [p for p in self._app_rows if self._app_state.get(p) != "Excluídos"
                   and (self._app_user.get(p) or p in visible_set)]
        total = len(targets)
        done = sum(1 for p in targets if cache.get(p, {}).get("v") == CACHE_VERSION)
        if total == 0 or done >= total:
            self.apps_progress_wrap.hide(); return
        self.apps_progress.setRange(0, total); self.apps_progress.setValue(done)
        self.apps_progress_label.setText(t("Carregando nomes e ícones ({done}/{total} apps)").format(done=done, total=total))
        self.apps_progress_wrap.show()

    def _flush_labels(self):
        save_label_cache(self._label_cache)

    def _on_app_info(self, pkg, label, icon, done, total):
        ent = self._label_cache.setdefault(pkg, {}); ent.update({"v": CACHE_VERSION, "label": label, "icon": icon})
        if not self._save_timer.isActive(): self._save_timer.start(2000)
        items = self._app_rows.get(pkg)
        if items:
            _, icon_item, name_item = items
            if label: name_item.setText(label)
            icon_item.setIcon(self._app_icon(label or pkg, icon))
        # Atualizar a barra para cada app força uma varredura de toda a tabela e
        # congela a interface em aparelhos com centenas/milhares de pacotes.
        if not self._progress_timer.isActive():
            self._progress_timer.start(120)

    def filter_apps(self):
        if not hasattr(self, "app_filter"): return
        term = self.app_filter.text().lower()
        wanted = {0: None, 1: "Ativados", 2: "Desativados", 3: "Excluídos"}[self.app_state.currentIndex()]
        typ = self.app_type.currentIndex()
        min_bytes = self.app_min.value() * 1024 * 1024
        for r in range(self.apps_table.rowCount()):
            name_item, pkg_item, size_item = self.apps_table.item(r, 2), self.apps_table.item(r, 3), self.apps_table.item(r, 4)
            if not name_item or not pkg_item: continue
            pkg = pkg_item.text()
            size = (size_item.data(Qt.UserRole + 2) or 0) if size_item else 0
            user = self._app_user.get(pkg, False)
            ok_text = not term or term in f"{name_item.text()} {pkg}".lower()
            ok_state = wanted is None or self._app_state.get(pkg) == wanted
            ok_type = typ == 0 or (typ == 1 and user) or (typ == 2 and not user)
            ok_size = size >= min_bytes
            self.apps_table.setRowHidden(r, not (ok_text and ok_state and ok_type and ok_size))
        self._update_select_all_header_icon()

    def _apps_cell_clicked(self, row, column):
        if column != 0:
            return
        item = self.apps_table.item(row, 0)
        if item is None:
            return
        self._set_app_item_checked(item, not bool(item.data(Qt.UserRole + 1)))
        self._update_selection_hint()

    def _set_app_item_checked(self, item, checked):
        item.setData(Qt.UserRole + 1, bool(checked))
        palette = PALETTES["dark" if self.dark else "light"]
        item.setIcon(svg_icon("checkbox_checked" if checked else "checkbox_outline", palette["text"], 18))

    def check_all_visible(self):
        visible_items = [self.apps_table.item(r, 0) for r in range(self.apps_table.rowCount())
                         if not self.apps_table.isRowHidden(r) and self.apps_table.item(r, 0)]
        should_check = not visible_items or not all(bool(item.data(Qt.UserRole + 1)) for item in visible_items)
        self.apps_table.setUpdatesEnabled(False)
        self.apps_table.blockSignals(True)
        try:
            for item in visible_items:
                self._set_app_item_checked(item, should_check)
        finally:
            self.apps_table.blockSignals(False)
            self.apps_table.setUpdatesEnabled(True)
        self._update_selection_hint()
        self._update_select_all_header_icon()

    def _update_select_all_header_icon(self):
        header_item = getattr(self, "_select_all_header_item", None)
        if header_item is None or not hasattr(self, "apps_table"):
            return
        visible_items = [self.apps_table.item(r, 0) for r in range(self.apps_table.rowCount())
                         if not self.apps_table.isRowHidden(r) and self.apps_table.item(r, 0)]
        checked = bool(visible_items) and all(bool(item.data(Qt.UserRole + 1)) for item in visible_items)
        palette = PALETTES["dark" if self.dark else "light"]
        header_item.setIcon(svg_icon("checkbox_checked" if checked else "checkbox_outline", palette["text"], 18))

    def open_selected(self):
        r = self.apps_table.currentRow()
        item = self.apps_table.item(r, 3) if r >= 0 else None
        if item: self.open_app(item.text())

    def show_permissions(self, pkg):
        try: adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        def work():
            out = run_command(adb + ["shell", "dumpsys", "package", pkg], 60)
            lines = [l.strip() for l in out.splitlines() if "permission" in l.lower()]
            return "\n".join(lines[:400]) or t("Nenhuma permissão encontrada.")
        def done(result, error):
            if error: QMessageBox.warning(self, t("Aviso"), error); return
            TextDialog(self, f"{t('Permissões')} — {pkg}", result).exec()
        self.run_async(work, done)

    def checked_packages(self) -> list:
        out = []
        for r in range(self.apps_table.rowCount()):
            item = self.apps_table.item(r, 0)
            if item and bool(item.data(Qt.UserRole + 1)): out.append(item.data(Qt.UserRole))
        return out

    def _update_selection_hint(self, *_):
        if not hasattr(self, "apps_side_hint"): return
        n = len(self.checked_packages())
        self.apps_side_hint.setText(t("{n} app(s) marcado(s)").format(n=n) if n else t("Nenhum app marcado."))
        self._update_select_all_header_icon()

    def target_packages(self) -> list:
        pkgs = self.checked_packages()
        if not pkgs:
            rows = sorted(set(i.row() for i in self.apps_table.selectedIndexes()))
            pkgs = [self.apps_table.item(r, 0).data(Qt.UserRole) for r in rows if self.apps_table.item(r, 0)]
        if not pkgs: raise RuntimeError(t("Marque (ou selecione) pelo menos um aplicativo."))
        return pkgs

    def _app_name(self, pkg):
        items = self._app_rows.get(pkg)
        return items[2].text() if items else pkg

    def _confirm_text(self, action, pkgs, extra=""):
        lines = [f"• {self._app_name(p)}  ({p})" for p in pkgs[:12]]
        more = f"\n… +{len(pkgs) - 12}" if len(pkgs) > 12 else ""
        return action + "\n\n" + "\n".join(lines) + more + (f"\n\n{extra}" if extra else "")

    @staticmethod
    def _pm_result(out):
        low = (out or "").lower()
        if "failure" in low or "error" in low or "exception" in low: raise RuntimeError(out)
        return out or "ok"

    def _bulk(self, title, pkgs, action, confirm_text=None, refresh=False):
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        if confirm_text is not None and not self.ask_confirm(title, confirm_text): return
        self.note(t("{title}: {n} aplicativo(s)…").format(title=title, n=len(pkgs)))
        def work():
            results = []
            for pkg in pkgs:
                try: results.append((pkg, True, action(adb, pkg)))
                except Exception as e: results.append((pkg, False, str(e).strip()))
            return results
        self.run_async(work, lambda r, e: self._bulk_done(title, r, e, refresh))

    def _bulk_done(self, title, results, error, refresh):
        if error:
            self.note("ERRO: " + error); QMessageBox.critical(self, title, error); return
        ok = [r for r in results if r[1]]
        lines = [f"OK — {pkg}: {msg}" if okk else f"FALHOU — {pkg}: {msg}" for pkg, okk, msg in results]
        summary = t("{ok} de {n} concluído(s).").format(ok=len(ok), n=len(results))
        self.statusBar().showMessage(summary, 6000)
        body = (summary + "\n\n" + "\n".join(lines))[:3500]
        (QMessageBox.information if len(ok) == len(results) else QMessageBox.warning)(self, title, body)
        if refresh and ok: self.load_apps()

    def uninstall_app(self):
        try: pkgs = self.target_packages()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        unsafe = {p for p, rec in getattr(self, "_recommendation_map", {}).items()
                  if self._debloat_risk(rec.get("removal", "Unlisted")) == t("Inseguro")}
        blocked = [p for p in pkgs if p in unsafe]
        if blocked:
            QMessageBox.warning(self, t("Bloqueado"), t("Não é possível desinstalar aplicativos classificados como Inseguro:") + "\n" + "\n".join(blocked[:20]))
            return
        self._bulk(t("Desinstalar para usuário"), pkgs,
                   lambda adb, p: self._pm_result(run_command(adb + ["shell", "pm", "uninstall", "--user", "0", p], 120)),
                   confirm_text=self._confirm_text(t("Desinstalar {n} aplicativo(s)?").format(n=len(pkgs))
                       + " " + t("Desinstalar para o usuário atual"),
                       pkgs, t("Isso pode remover dados locais. Apps de sistema podem não ser removíveis.")),
                   refresh=True)

    def disable_app(self):
        try: pkgs = self.target_packages()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        self._bulk(t("Desativar"), pkgs,
                   lambda adb, p: self._pm_result(run_command(adb + ["shell", "pm", "disable-user", "--user", "0", p], 60)),
                   confirm_text=self._confirm_text(t("Desativar {n} aplicativo(s)?").format(n=len(pkgs)),
                       pkgs, t("Isso pode afetar funções do sistema.")), refresh=True)

    def enable_app(self):
        try: pkgs = self.target_packages()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        self._bulk(t("Reativar"), pkgs,
                   lambda adb, p: self._pm_result(run_command(adb + ["shell", "pm", "enable", p], 60)), refresh=True)

    def force_stop(self):
        try: pkgs = self.target_packages()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        self._bulk(t("Forçar parada"), pkgs,
                   lambda adb, p: run_command(adb + ["shell", "am", "force-stop", p], 60) or t("parado"))

    def backup_apk(self):
        try: pkgs = self.target_packages()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        folder = QFileDialog.getExistingDirectory(self, t("Salvar APK em…"), SETTINGS.get("backup_dir") or str(Path.home()))
        if not folder: return
        def save(adb, pkg):
            paths = [x.replace("package:", "").strip() for x in run_command(adb + ["shell", "pm", "path", pkg], 60).splitlines() if x.strip()]
            if not paths: raise RuntimeError(t("Nenhum APK encontrado."))
            dest = Path(folder) / pkg; dest.mkdir(parents=True, exist_ok=True)
            for i, remote in enumerate(paths):
                run_command(adb + ["pull", remote, str(dest / ("base.apk" if i == 0 else f"split_{i}.apk"))], 180)
            return t("salvo em {dest}").format(dest=dest)
        self._bulk(t("Salvar APK no PC"), pkgs, save)

    def data_backup(self):
        try: pkgs = self.target_packages()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        folder = QFileDialog.getExistingDirectory(self, t("Escolha a pasta para os backups…"), SETTINGS.get("backup_dir") or str(Path.home()))
        if not folder: return
        if not self.ask_confirm(t("Backup de dados (adb backup)"),
                                t("O Android pedirá confirmação no aparelho para cada backup. Confirme na tela do celular quando aparecer. Continuar?")):
            return
        def backup(adb, pkg):
            target = Path(folder) / f"{pkg}.ab"
            run_command(adb + ["backup", "-f", str(target), pkg], 900)
            return t("backup salvo em {dest}").format(dest=target)
        self._bulk(t("Backup de dados (adb backup)"), pkgs, backup)

    def app_context_menu(self, pos):
        item = self.apps_table.itemAt(pos)
        if item is None: return
        row = item.row()
        name_item = self.apps_table.item(row, 2); pkg_item = self.apps_table.item(row, 3)
        if not name_item or not pkg_item: return
        pkg, name = pkg_item.text(), name_item.text()
        menu = QMenu(self)
        menu.addAction(t("Abrir app"), lambda: self.open_app(pkg))
        menu.addSeparator()
        menu.addAction(t("Copiar nome do app"), lambda: self._copy(name, t("Nome copiado.")))
        menu.addAction(t("Copiar nome do pacote"), lambda: self._copy(pkg, t("Pacote copiado.")))
        menu.addAction(t("Ver permissões"), lambda: self.show_permissions(pkg))
        menu.exec(self.apps_table.viewport().mapToGlobal(pos))

    def _copy(self, text, message):
        QGuiApplication.clipboard().setText(text)
        self.statusBar().showMessage(message, 3000)

    def open_app(self, pkg):
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        def work():
            out = run_command(adb + ["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], 30)
            if "No activities found" in out or "monkey aborted" in out.lower():
                raise RuntimeError(t("Não foi possível abrir {pkg}: {e}").format(pkg=pkg, e=out))
            return t("Abrindo {pkg}…").format(pkg=pkg)
        def done(r, e):
            if e: QMessageBox.warning(self, t("Aviso"), e)
            else: self.statusBar().showMessage(r or "", 4000)
        self.run_async(work, done)

    def clear_cache_all(self):
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        if not self.ask_confirm(t("Limpar cache de todos os apps"),
                t("Isso remove o cache de TODOS os aplicativos do aparelho.\n\nOs dados dos apps (login, configurações, mensagens) são mantidos. A operação pode levar alguns minutos.")):
            return
        self.statusBar().showMessage(t("Limpando cache de todos os apps…"))
        self.run_async(lambda: run_command(adb + ["shell", "pm", "trim-caches", "1000000000000"], 900) or t("Cache limpo."),
                       self.show_result)

    # ---------- ferramentas: instalação e arquivos
    def pick_install(self):
        files, _ = QFileDialog.getOpenFileNames(self, t("Escolher pacotes"), "", "Pacotes Android (*.apk *.xapk *.apks);;Todos os arquivos (*.*)")
        if files: self.install_path.setText("|".join(files))

    def install_files(self):
        try: self.ensure_device()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        paths = [Path(p) for p in self.install_path.text().split("|") if p.strip()]
        if not paths or any(not p.exists() for p in paths):
            QMessageBox.warning(self, t("Aviso"), t("Escolha arquivos existentes.")); return
        if not self.ask_confirm(t("Confirmar instalação"),
                                t("Instalar {n} arquivo(s) em {dev}?").format(n=len(paths), dev=self.device)): return
        self.install_status.clear()
        self._set_install_status("⟳  Iniciando instalação…")
        self.run_async(lambda: self._install_work([str(p) for p in paths], self.install_multi.isChecked(),
                                                   self._install_bridge.text.emit), self._install_done)

    def _set_install_status(self, text):
        # QPlainTextEdit keeps every status update instead of replacing the prior one.
        self.install_status.appendPlainText(text)
        self.install_status.verticalScrollBar().setValue(self.install_status.verticalScrollBar().maximum())
        if text.startswith("✓"):
            self.install_status.setStyleSheet("QPlainTextEdit { color: #22c55e; font-weight: 700; }")
        elif text.startswith(("⟳", "⏳")):
            self.install_status.setStyleSheet("QPlainTextEdit { color: #a78bfa; font-weight: 600; }")
        elif text.startswith("✗"):
            self.install_status.setStyleSheet("QPlainTextEdit { color: #ef4444; font-weight: 700; }")
        self.statusBar().showMessage(text, 6000)

    def _install_done(self, result, error):
        if error:
            self._set_install_status(f"✗  Falha na instalação: {error}")
            if is_connection_error(error):
                self._connection_lost()
            QMessageBox.critical(self, t("Erro na instalação"), str(error))
            return
        self._set_install_status("✓  Processo de instalação concluído!")
        if result:
            self.statusBar().showMessage(str(result).splitlines()[-1], 6000)

    def _install_work(self, path_strings, split, emit=None):
        installed = []
        adb = self.adb()
        with tempfile.TemporaryDirectory(prefix="droidcontrol_") as temp:
            groups = []
            for s in path_strings:
                p = Path(s)
                if p.suffix.lower() == ".apk":
                    groups.append([p])
                elif p.suffix.lower() in (".xapk", ".apks"):
                    outdir = Path(temp) / p.stem; outdir.mkdir()
                    with zipfile.ZipFile(p) as z:
                        root = outdir.resolve()
                        for member in z.infolist():
                            target = (outdir / member.filename).resolve()
                            if target != root and root not in target.parents:
                                raise RuntimeError(f"Arquivo compactado inválido: {p.name}")
                            if member.is_dir():
                                target.mkdir(parents=True, exist_ok=True)
                            else:
                                target.parent.mkdir(parents=True, exist_ok=True)
                                with z.open(member) as src, target.open("wb") as dst:
                                    shutil.copyfileobj(src, dst)
                    apks = sorted(outdir.rglob("*.apk"), key=lambda x: (x.name.lower() != "base.apk", x.name.lower()))
                    if not apks: raise RuntimeError(t("Nenhum APK dentro de {name}").format(name=p.name))
                    groups.append(apks)
                else:
                    raise RuntimeError(t("Formato não suportado: {name}").format(name=p.name))
            total = len(groups)
            for idx, group in enumerate(groups, 1):
                apk_name = group[0].name
                if emit:
                    emit(f"⟳  Instalando {apk_name}… ({idx}/{total})")
                if len(group) == 1 and not split:
                    out = check_install_output(run_command(adb + ["install", "-r", str(group[0])], 180))
                else:
                    out = check_install_output(run_command(adb + ["install-multiple", "-r"] + [str(x) for x in group], 240))
                installed.append(f"{apk_name}: {out or 'OK'}")
                if emit:
                    emit(f"✓  Concluído! — {apk_name}")
        return "\n".join(installed)

    def push_file(self):
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        path, _ = QFileDialog.getOpenFileName(self, t("Escolher arquivo para enviar"))
        if not path: return
        remote = "/sdcard/Download/" + Path(path).name
        def transfer():
            output = run_command(adb + ["push", path, remote], 600)
            if output and re.search(r"\bfailed\b|\berror\b|\bno such file\b", output, re.I):
                raise RuntimeError(output)
            return {"dest": remote, "output": output}
        def transfer_done(result, error):
            if error:
                QMessageBox.critical(self, t("Falha na transferência"), str(error)); return
            QMessageBox.information(self, t("Transferência concluída"), t("O arquivo foi transferido com êxito para o Android.\n\nDestino: {dest}").format(dest=result["dest"]))
            if result.get("output"): self.note(result["output"])
        self.note(t("Enviando") + "…")
        self.run_async(transfer, transfer_done)

    # ---------- ferramentas: tela
    @staticmethod
    def parse_wm_size(text):
        m = re.findall(r"(\d+)x(\d+)", text or "")
        return tuple(map(int, m[-1])) if m else None

    @staticmethod
    def parse_wm_density(text):
        m = re.findall(r"(\d+)", text or "")
        return int(m[-1]) if m else None

    def read_display(self):
        if not self.device: return
        try: adb = self.adb()
        except Exception: return
        def work():
            size = self.parse_wm_size(run_command(adb + ["shell", "wm", "size"]))
            dpi = self.parse_wm_density(run_command(adb + ["shell", "wm", "density"]))
            if not size or not dpi: raise RuntimeError(t("Não foi possível interpretar a resolução ou o DPI."))
            return {"width": size[0], "height": size[1], "dpi": dpi}
        self.run_async(work, self._display_read_result)

    def _display_read_result(self, data, error):
        if error or not data:
            self.statusBar().showMessage(t("Não foi possível ler a resolução atual."), 5000); return
        self._display_baseline = (data["width"], data["height"], data["dpi"])
        self._auto_guard = True
        try:
            self.res_w.setValue(data["width"]); self.res_h.setValue(data["height"]); self.dpi.setValue(data["dpi"])
        finally:
            self._auto_guard = False

    def _on_width_changed(self, width):
        if self._auto_guard or self._display_baseline is None or not self.lock_btn.isChecked() or width <= 0:
            return
        base_w, base_h, base_dpi = self._display_baseline
        self._auto_guard = True
        try:
            self.res_h.setValue(max(320, min(4096, round(width * base_h / base_w))))
            self.dpi.setValue(max(80, min(1000, round(base_dpi * width / base_w))))
        finally:
            self._auto_guard = False

    def set_resolution_and_density(self):
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        w, h, dpi = self.res_w.value(), self.res_h.value(), self.dpi.value()
        if not self.ask_confirm(t("Aplicar tela"), t("Aplicar {w}×{h} e {dpi} dpi?").format(w=w, h=h, dpi=dpi)): return
        def work():
            a = run_command(adb + ["shell", "wm", "size", f"{w}x{h}"])
            b = run_command(adb + ["shell", "wm", "density", str(dpi)])
            return (a + "\n" + b).strip() or t("Operação concluída.")
        self.run_tool(t("Aplicando resolução e DPI"), work)

    def reset_display(self):
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        if not self.ask_confirm(t("Restaurar tela"), t("Restaurar resolução e DPI padrão do Android?")): return
        self.run_tool(t("Restaurando"), lambda: (run_command(adb + ["shell", "wm", "size", "reset"]) + "\n" +
                                               run_command(adb + ["shell", "wm", "density", "reset"])).strip())

    # ---------- visão geral: captura, espelhamento, reinício
    def take_screenshot(self):
        try: self.ensure_device()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        path, _ = QFileDialog.getSaveFileName(self, t("Salvar captura de tela"), str(Path.home() / "Pictures" / "DroidControl.png"), "PNG (*.png)")
        if not path: return
        if not path.lower().endswith(".png"): path += ".png"
        try:
            args = [find_tool("adb")] + (["-s", self.device] if self.device else [])
            proc = subprocess.run(args + ["exec-out", "screencap", "-p"], capture_output=True, timeout=30,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if proc.returncode != 0 or not proc.stdout.startswith(b"\x89PNG"):
                raise RuntimeError(proc.stderr.decode("utf-8", "replace") or t("O Android não retornou uma imagem PNG."))
            Path(path).write_bytes(proc.stdout)
            self.statusBar().showMessage(t("Captura salva em {path}").format(path=path), 5000)
        except Exception as e: QMessageBox.critical(self, t("Erro"), str(e))

    def launch_scrcpy(self):
        try: self.ensure_device()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        tool = find_tool("scrcpy")
        if not tool:
            QMessageBox.warning(self, "scrcpy", t("scrcpy não encontrado. Coloque scrcpy.exe na pasta tools/ ou no PATH.")); return
        try:
            subprocess.Popen([tool, "-s", self.device], cwd=str(BASE_DIR), creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            self.statusBar().showMessage(t("scrcpy iniciado"), 4000)
        except Exception as e: QMessageBox.critical(self, "scrcpy", str(e))

    def reboot(self, mode=""):
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
        label = self.reboot_mode.currentText()
        if not self.ask_confirm(t("Confirmar reinicialização"), t("Reiniciar o dispositivo para: {label}?").format(label=label)): return
        args = adb + ["reboot"] + ([mode] if mode else [])
        self.run_tool(t("Reiniciando"), lambda: run_command(args, 60) or t("Comando enviado. A conexão pode cair durante o reinício."))

    # ---------- console
    def open_adb_terminal(self):
        try: self.ensure_device(); adb = self.adb()
        except Exception as e: QMessageBox.warning(self, "ADB", str(e)); return
        try:
            subprocess.Popen(adb + ["shell"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.statusBar().showMessage(t("Terminal ADB aberto"), 4000)
        except Exception as e:
            QMessageBox.warning(self, "ADB", t("Não foi possível abrir o terminal: {e}").format(e=e))

    def run_console_command(self):
        raw = self.console_command.text().strip()
        if not raw: return
        mode = self.console_mode.currentText()
        if mode == "ADB" and raw.lower().startswith("adb "): raw = raw[4:].strip()
        if mode == "Fastboot" and raw.lower().startswith("fastboot "): raw = raw[9:].strip()
        if mode == "ADB" and raw.lower() == "shell":
            self.console_command.clear(); self.open_adb_terminal(); return
        if any(x in raw for x in ["&&", "||", ";", "|", ">", "<", "\n", "\r"]):
            QMessageBox.warning(self, "Console", t("Use um comando por vez; operadores de shell não são aceitos.")); return
        import shlex
        try: args = shlex.split(raw, posix=False)
        except ValueError as e: QMessageBox.warning(self, "Console", str(e)); return
        try: command = (self.adb() if mode == "ADB" else self.fastboot()) + args
        except Exception as e: QMessageBox.warning(self, "Console", str(e)); return
        dangerous = any(x.lower() in {"flash", "erase", "format", "flashing", "unlock", "lock", "wipe"} for x in args)
        if dangerous and not self.ask_confirm(t("Comando potencialmente destrutivo"),
                t("Executar {mode}: {raw}?\n\nPode apagar dados ou alterar o firmware.").format(mode=mode, raw=raw)):
            return
        self.logs_view.appendPlainText(log(f"CONSOLE {mode}: {raw}"))
        self.console_command.clear()
        def finished(result, error):
            output = str(error) if error else (result or t("Comando concluído sem saída."))
            self.logs_view.appendPlainText(log(f"SAÍDA {mode}:\n{output}"))
            self.logs_view.appendPlainText("─" * 50)
        self.run_async(lambda: run_command(command, 180), finished)

    def refresh_log(self):
        if not hasattr(self, "logs_view"): return
        try: self.logs_view.setPlainText(LOG_FILE.read_text(encoding="utf-8") if LOG_FILE.exists() else t("Nenhum log ainda."))
        except Exception as e: self.logs_view.setPlainText(str(e))
        sb = self.logs_view.verticalScrollBar(); sb.setValue(sb.maximum())

    def clear_logs(self):
        try:
            LOG_DIR.mkdir(exist_ok=True); LOG_FILE.write_text("", encoding="utf-8"); self.logs_view.clear()
        except Exception as e: QMessageBox.warning(self, t("Logs"), str(e))

    def open_logs(self):
        try: os.startfile(str(LOG_DIR))
        except Exception as e: QMessageBox.warning(self, t("Logs"), str(e))

    def check_update(self):
        url = SETTINGS.get("update_url", "")
        if not url:
            QMessageBox.information(self, t("Atualização"), t("Configure a URL de atualização nas configurações.")); return
        def work():
            import urllib.request
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        def done(data, error):
            if error:
                QMessageBox.warning(self, t("Atualização"), t("Não foi possível verificar a atualização: {e}").format(e=error)); return
            latest = str(data.get("version", ""))
            if latest and version_tuple(latest) > version_tuple(APP_VERSION):
                QMessageBox.information(self, t("Atualização"), t("Nova versão disponível: {v}. {url}").format(v=latest, url=data.get("url", "")))
            else:
                QMessageBox.information(self, t("Atualização"), t("Você já está com a versão mais recente."))
        self.run_async(work, done)

    def open_settings(self):
        if SettingsDialog(self).exec():
            self._monitor_timer.setInterval(int(SETTINGS.get("monitor_s", 5)) * 1000)
            self.note(t("Configurações salvas."))

    def wifi_action(self, kind):
        tool = find_tool("adb")
        if not tool:
            QMessageBox.warning(self, t("Aviso"), t("adb não encontrado. Instale o Platform Tools ou coloque adb.exe na pasta platform-tools/.")); return
        addr = self.wifi_addr.text().strip()
        if kind == "tcpip":
            try: self.ensure_device(); args = self.adb() + ["tcpip", "5555"]
            except Exception as e: QMessageBox.warning(self, t("Aviso"), str(e)); return
            self.run_tool(t("Ativando TCP/IP"), lambda: run_command(args, 30) or t("Operação concluída."))
        elif kind == "connect":
            if not addr: QMessageBox.warning(self, t("Aviso"), t("Informe o IP:porta.")); return
            args = [tool, "connect", addr]
            self.run_tool(t("Conectando"), lambda: run_command(args, 30))
            QTimer.singleShot(2000, lambda: self.refresh_devices(force=True))
        else:
            args = [tool, "disconnect", addr] if addr else [tool, "disconnect"]
            self.run_tool(t("Desconectando"), lambda: run_command(args, 30) or t("Operação concluída."))
            QTimer.singleShot(1500, lambda: self.refresh_devices(force=True))

    def closeEvent(self, event):
        # Para workers antes de encerrar o servidor ADB, evitando subprocessos órfãos.
        worker = self.info_worker
        if worker is not None and worker.isRunning():
            worker.stop(); worker.wait(5000)
        for pending in list(getattr(self, "workers", [])):
            try:
                if pending.isRunning(): pending.wait(1500)
            except RuntimeError:
                pass
        self._flush_labels()
        # adb.exe mantém um servidor residente mesmo após a janela fechar.
        # Encerrar pelo próprio ADB é mais seguro que matar todos os adb.exe do Windows.
        adb_tool = find_tool("adb")
        if adb_tool:
            try:
                subprocess.run([adb_tool, "kill-server"], capture_output=True, text=True,
                               timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except Exception as e:
                log(f"Não foi possível encerrar o servidor ADB ao fechar: {e}")
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Segoe UI", 10))
    window = DroidControl()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
