"""
ManagerDroid — gerenciador Android para Windows 10/11 (PT/EN).
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
    QFormLayout,
    QProgressDialog,
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QLineEdit, QPlainTextEdit, QCheckBox, QProgressBar, QFrame,
    QSpinBox, QHeaderView, QAbstractItemView, QScrollArea, QListWidget,
    QListWidgetItem, QStackedWidget, QMenu, QDialog, QDialogButtonBox, QSizePolicy
)

APP_NAME = "ManagerDroid"
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DATA_DIR = Path(__file__).resolve().parent
LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "droidcontrol.log"
# Cache em diretório gravável do usuário (não falha quando o app está em Program Files).
# Migra o cache portátil antigo na primeira execução, preservando nomes e ícones.
_OLD_CACHE_DIR = DATA_DIR / "cache"
_USER_DATA_ROOT = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home()))
# Pasta de dados mantida como ManagerDroid para preservar configurações e cache já existentes.
CACHE_DIR = _USER_DATA_ROOT / "DroidControl" / "cache"
LABEL_CACHE = CACHE_DIR / "app_labels.json"
ICON_CACHE = CACHE_DIR / "icons"
SETTINGS_FILE = CACHE_DIR / "settings.json"
CACHE_VERSION = 4
APP_VERSION = "20"
HELPER_PKG = "com.managerdroid.help"
HELPER_ACTION = "com.managerdroid.help.EXPORT"
HELPER_REMOTE = "/sdcard/ManagerDroid"

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

# Ilustração do aparelho e logos de fabricantes para a Visão geral.
PHONE_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="720" viewBox="480 0 340 720" preserveAspectRatio="xMidYMid meet"><g transform="translate(0,720) scale(0.1,-0.1)" fill="#20242b" stroke="none"><path d="M5268 6630 c-79 -10 -169 -48 -217 -93 -44 -42 -87 -133 -101 -215 -7 -48 -10 -820 -8 -2722 l3 -2655 26 -67 c14 -36 40 -84 57 -105 37 -47 126 -96 200 -112 37 -8 392 -11 1174 -11 1204 0 1178 -1 1279 50 51 27 114 101 141 169 l23 56 3 1193 c2 1043 4 1192 17 1192 23 0 22 735 0 744 -12 4 -15 27 -15 121 0 96 3 115 15 115 13 0 15 27 15 180 0 152 -2 180 -15 180 -12 0 -15 111 -17 853 -3 802 -4 855 -22 903 -47 131 -148 205 -306 224 -100 12 -2149 12 -2252 0z m2482 -3030 l0 -2400 -1355 0 -1355 0 0 2400 0 2400 1355 0 1355 0 0 -2400z"/></g></svg>'''
BRAND_SVGS = {
    "xiaomi": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800"><path d="M680 0H120C53.7 0 0 53.7 0 120v560c0 66.3 53.7 120 120 120h560c66.3 0 120-53.7 120-120V120C800 53.7 746.3 0 680 0z" fill="#ff6900"/><path d="M515.3 366.1V546c0 4.4-3.6 8-8 8h-64c-4.4 0-8-3.6-8-8V366.1c0-22.1-17.9-40-40-40H239.6c-2.2 0-4 1.8-4 4V546c0 4.4-3.6 8-8 8h-64c-4.4 0-8-3.6-8-8V254.1c0-4.4 3.6-8 8-8h231.7c66.3 0 120 53.7 120 120zm-147.8 0h-64c-4.4 0-8 3.6-8 8V546c0 4.4 3.6 8 8 8h64c4.4 0 8-3.6 8-8V374.1c0-4.4-3.6-8-8-8zm268.9-120h-64c-4.4 0-8 3.6-8 8V546c0 4.4 3.6 8 8 8h64c4.4 0 8-3.6 8-8V254.1c0-4.4-3.6-8-8-8z" fill="#fff"/></svg>''',
    "samsung": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 201 80"><path fill="#2d4f9e" d="M200.653 15.87C197.923.194 150.822-4.698 95.446 4.943 72.19 8.994 51.191 14.969 34.838 21.691c2.512.055 4.375.631 5.507 1.76.885.886 1.332 2.102 1.332 3.617v1.555h-5.43V27.25c0-1.144-.686-1.853-1.901-1.853-1.021 0-1.65.461-1.853 1.369a2.63 2.63 0 0 0 .022 1.084c.581 2.375 8.644 3.85 9.521 8.233.115.564.271 1.771.025 3.498-.503 3.535-3.609 4.899-7.563 4.899-5.519 0-7.761-2.614-7.761-6.218l.004-1.705h5.821l.003 2.124c0 1.194.868 1.853 2.05 1.853 1.12 0 1.774-.451 2-1.373.105-.424.151-1.049-.04-1.527-1.077-2.702-8.606-3.964-9.533-8.333-.207-.982-.224-1.818-.052-2.875a5.606 5.606 0 0 1 .482-1.511C9.333 33.398-1.278 42.732.124 50.791c2.733 15.678 49.833 20.565 105.208 10.924 24.342-4.237 46.226-10.58 62.881-17.688-.241.012-.475.038-.725.038-3.79 0-7.174-1.42-7.525-5.294-.062-.705-.073-1-.075-1.402l.002-8.906c0-.384.045-1.058.088-1.406.449-3.744 3.409-5.288 7.512-5.288 3.175 0 7.068.911 7.496 5.291.057.55.051 1.137.05 1.33v.841h-5.484v-1.255c0-.027-.008-.496-.068-.789-.09-.447-.471-1.483-2.033-1.483-1.543 0-1.943 1.038-2.043 1.484-.057.245-.084.597-.084.987v9.679c-.005.336.012.599.046.792.027.152.304 1.486 2.1 1.486 1.783 0 2.059-1.334 2.084-1.486.047-.262.053-.574.051-.792v-2.999h-2.158v-3.23h7.631v5.746c-.002.391-.008.68-.074 1.4-.092 1.016-.412 1.876-.914 2.611 17.663-8.387 27.947-17.57 26.563-25.512zM57.065 43.653l-2.778-18.876h-.1l-2.849 18.876h-5.855l3.938-21.317h9.553l3.914 21.317h-5.823zm28.162 0-.129-18.511h-.094l-3.445 18.511h-5.495l-3.428-18.511h-.098l-.125 18.511h-5.445l.472-21.317h8.758l2.55 15.835h.125l2.557-15.835h8.754l.47 21.317h-5.427zm25.641-4.131c-.586 4.129-4.631 4.851-7.49 4.851-4.747 0-7.683-2.029-7.683-6.158l.003-1.684h5.751l.004 2.098c0 1.139.803 1.836 2.043 1.836 1.106 0 1.754-.444 1.979-1.356.104-.425.147-1.045-.037-1.513-1.06-2.651-8.53-3.95-9.438-8.251-.208-.975-.223-1.803-.052-2.849.632-3.899 4.374-4.709 7.386-4.709 2.694 0 4.655.588 5.831 1.764.877.878 1.321 2.083 1.321 3.582v1.538h-5.378v-1.357c0-1.162-.721-1.834-1.88-1.834-1.028 0-1.65.457-1.854 1.356a2.59 2.59 0 0 0 .026 1.072c.576 2.364 8.568 3.809 9.443 8.151.113.554.268 1.743.025 3.463zm19.918-1.937c.008.4-.031 1.199-.053 1.404-.328 3.512-2.84 5.297-7.447 5.297-4.625 0-7.139-1.785-7.465-5.297a16.957 16.957 0 0 1-.053-1.4V22.331h5.502V38.07c-.006.352.012.612.047.793.068.35.416 1.486 1.969 1.486 1.548 0 1.896-1.137 1.969-1.482.031-.186.05-.459.05-.798V22.331h5.481v15.254zm23.705 5.851h-7.656l-5.139-16.885h-.086l.285 16.885h-5.336v-21.1h7.977l4.75 16.22h.111l-.281-16.22h5.375v21.1z"/></svg>''',
    "motorola": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#E1140A" d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12C24.002 5.375 18.632.002 12.007 0H12zm7.327 18.065s-.581-2.627-1.528-4.197c-.514-.857-1.308-1.553-2.368-1.532-.745 0-1.399.423-2.2 1.553-.469.77-.882 1.573-1.235 2.403 0 0-.29-.675-.63-1.343a8.038 8.038 0 0 0-.605-1.049c-.804-1.13-1.455-1.539-2.2-1.553-1.049-.021-1.854.675-2.364 1.528-.948 1.574-1.528 4.197-1.528 4.197h-.864l4.606-15.12 3.56 11.804.024.021.024-.021 3.56-11.804 4.61 15.113h-.862z"/></svg>''',
    "android": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-146 129 218 256"><g fill="#3ddc84"><path d="M-2.9 150.4l2.8-4.2 2.8-4.1 6.2-9.3c.8-1.1.5-2.7-.7-3.4-1.1-.8-2.7-.5-3.4.7l-6.6 9.9-2.8 4.2-2.8 4.2c-9-3.5-18.9-5.4-29.5-5.4-10.5 0-20.5 1.9-29.5 5.4l-2.8-4.2L-72 140l-6.6-9.9c-.8-1.1-2.3-1.4-3.4-.7-.7.8-1.4 2.3-.7 3.4l6.2 9.3 2.8 4.1 2.8 4.2c-21 9.8-35.3 28.3-35.3 49.6H32.5c-.1-21.3-14.3-39.8-35.4-49.6zM-66.7 180.1a7.4 7.4 0 1 1 0-14.8 7.4 7.4 0 0 1 0 14.8zm59.4 0a7.4 7.4 0 1 1 0-14.8 7.4 7.4 0 0 1 0 14.8z"/><path d="M-105.3 209.8l-1.1.1v109c0 8.7 7 15.7 15.7 15.7h11.3c-.4 1.3-.6 2.7-.6 4.1v31.4c0 8.2 6.7 14.9 14.9 14.9s14.9-6.7 14.9-14.9v-31.4h27.6v31.4c0 8.2 6.7 14.9 14.9 14.9s14.9-6.7 14.9-14.9v-31.4h11.3c8.7 0 15.7-7 15.7-15.7v-109H-105.3zM-131.1 209.9a14.9 14.9 0 0 0-14.9 14.9v63.6a14.9 14.9 0 0 0 29.8 0v-63.6a14.9 14.9 0 0 0-14.9-14.9zm188.3 0a14.9 14.9 0 0 0-14.9 14.9v63.6a14.9 14.9 0 0 0 29.8 0v-63.6a14.9 14.9 0 0 0-14.9-14.9z"/></g></svg>'''
}

# ---------------------------------------------------------------- configurações e idioma
def load_settings() -> dict:
    try: data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception: data = {}
    data.setdefault("lang", "pt"); data.setdefault("dark", True); data.setdefault("monitor_s", 5)
    data.setdefault("backup_dir", ""); data.setdefault("onboarding_done", False)
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
    "Trocar idioma": "Change language",
    "Bem-vindo ao ManagerDroid": "Welcome to ManagerDroid",
    "Ative as opções do desenvolvedor": "Enable developer options",
    "Abra Configurações > Sobre o telefone e toque 7 vezes em “Número da versão” (ou “Número da compilação”). Se pedir, digite o PIN. Aparecerá a mensagem “Você agora é um desenvolvedor”.": "Open Settings > About phone and tap “Build number” 7 times. Enter your PIN if asked. You will see “You are now a developer”.",
    "Ative a depuração USB": "Enable USB debugging",
    "Volte às Configurações e abra Opções do desenvolvedor (em alguns aparelhos fica dentro de Sistema ou Configurações adicionais). Ative “Depuração USB”.": "Go back to Settings and open Developer options (on some phones it is under System or Additional settings). Turn on “USB debugging”.",
    "Conecte o cabo e aceite a chave": "Connect the cable and accept the key",
    "Conecte o celular ao computador. Quando aparecer “Permitir depuração USB?”, marque “Sempre permitir deste computador” e toque em Permitir.": "Connect the phone to the computer. When “Allow USB debugging?” appears, tick “Always allow from this computer” and tap Allow.",
    "Xiaomi, Redmi e POCO (opcional)": "Xiaomi, Redmi and POCO (optional)",
    "Em Opções do desenvolvedor, ative também “Instalar via USB” e “Depuração USB (configurações de segurança)”. Se o aparelho pedir, entre com a conta Mi.": "In Developer options, also turn on “Install via USB” and “USB debugging (Security settings)”. If asked, sign in with your Mi account.",
    "Pronto!": "All set!",
    "Escolha o aparelho no topo da janela para começar. Se ele não aparecer, confira o cabo e a autorização de depuração.": "Choose the device at the top of the window to start. If it does not appear, check the cable and the debugging authorization.",
    "Passo {n} de {total}": "Step {n} of {total}",
    "Voltar": "Back", "Próximo": "Next", "Concluir": "Finish", "Atualizar lista de dispositivos": "Refresh device list",
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
    "Permissão de arquivos não concedida ao helper. Abra o ManagerDroid Helper no aparelho e toque em 'Permitir acesso a arquivos'.":
        "File permission not granted to the helper. Open ManagerDroid Helper on the device and tap 'Allow file access'.",
    "Atualiza a lista e os nomes e ícones (pelo ManagerDroid Helper).": "Refreshes the list and names and icons (via ManagerDroid Helper).",
    "Busca nomes e ícones pelo app ManagerDroid Helper (ou pelo modo lento, com aapt)": "Fetches names and icons via the ManagerDroid Helper app (or slow mode, with aapt)",
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
    "light": dict(bg="#F5F8FD", surface="#FFFFFF", surface2="#F1F5FB", border="#E2E8F2",
                  text="#142036", muted="#64748B", accent="#2563EB", accent_hover="#1D4ED8",
                  accent_text="#FFFFFF", accent_soft="#E8EFFD", danger="#DC2626",
                  danger_soft="#FDECEC", success="#15803D", phone="#D5E0F5"),
    "dark": dict(bg="#0B1020", surface="#111A2E", surface2="#17223A", border="#22304D",
                 text="#E8EEFB", muted="#8A9AB8", accent="#60A5FA", accent_hover="#93C5FD",
                 accent_text="#0B1020", accent_soft="#1B2A4A", danger="#F87171",
                 danger_soft="#3A1F2A", success="#4ADE80", phone="#26365A"),
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
QDialog, QMessageBox, QProgressDialog { background: @surface; }
QMessageBox QLabel#qt_msgbox_label, QProgressDialog QLabel { font-size: 10.5pt; padding: 6px 4px; }
QMessageBox QLabel#qt_msgboxex_icon_label { padding: 6px 12px 6px 6px; }
QMessageBox QPushButton, QDialogButtonBox QPushButton, QProgressDialog QPushButton {
    min-width: 96px; padding: 8px 18px; border-radius: 9px; }
QMessageBox QPushButton:default, QDialogButtonBox QPushButton:default {
    background: @accent; color: @accent_text; border: 0; }
QMessageBox QPushButton:default:hover, QDialogButtonBox QPushButton:default:hover {
    background: @accent_hover; color: @accent_text; }
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

def record_change(action: str, package: str, success: bool, details: str = "") -> None:
    """Histórico persistente de ações de gerenciamento no dispositivo."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / "change_history.jsonl"
        row = {"timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
               "action": str(action), "package": str(package), "success": bool(success),
               "details": str(details)[:1200]}
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        log(f"Falha ao salvar histórico: {exc}")

SCRCPY_VERSION = "5.0.1"
SCRCPY_DIR = DATA_DIR / "tools" / "scrcpy"

def scrcpy_download_url() -> str:
    # Windows ARM64 usa o pacote winarm64; os demais usam o win64.
    arch = os.environ.get("PROCESSOR_ARCHITECTURE", "").upper()
    if arch == "ARM64" or os.environ.get("PROCESSOR_ARCHITEW6432", "").upper() == "ARM64":
        suffix = "winarm64"
    else:
        suffix = "win64"
    return (f"https://github.com/Genymobile/scrcpy/releases/download/v{SCRCPY_VERSION}/"
            f"scrcpy-{suffix}-v{SCRCPY_VERSION}.zip")

def install_scrcpy(progress=None) -> str:
    """Baixa o scrcpy oficial do GitHub, valida e extrai em tools/scrcpy. Retorna o caminho do scrcpy.exe."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="droicontrol_scrcpy_"))
    try:
        archive = tmp_dir / "scrcpy.zip"
        req = urllib.request.Request(scrcpy_download_url(), headers={"User-Agent": "ManagerDroid"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(archive, "wb") as out:
            total = int(resp.headers.get("Content-Length") or 0); done = 0
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk: break
                out.write(chunk); done += len(chunk)
                if progress: progress(done, total)
        if not zipfile.is_zipfile(archive):
            raise RuntimeError("O arquivo baixado não é um zip válido.")
        extract = tmp_dir / "extract"
        with zipfile.ZipFile(archive) as z:
            z.extractall(extract)  # zipfile já normaliza caminhos com '..'
        exe = next(extract.rglob("scrcpy.exe"), None)
        if exe is None:
            raise RuntimeError("scrcpy.exe não encontrado no pacote baixado.")
        if SCRCPY_DIR.exists():
            shutil.rmtree(SCRCPY_DIR)
        SCRCPY_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(exe.parent), str(SCRCPY_DIR))
        return str(SCRCPY_DIR / "scrcpy.exe")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

ADB_DIR = DATA_DIR / "adb"
ADB_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

def download_and_extract(url: str, target: Path, must_contain: str, progress=None) -> str:
    """Baixa um zip, localiza `must_contain` dentro dele e move a pasta que o contém para `target`."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="droicontrol_dl_"))
    try:
        archive = tmp_dir / "pkg.zip"
        req = urllib.request.Request(url, headers={"User-Agent": "ManagerDroid"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(archive, "wb") as out:
            total = int(resp.headers.get("Content-Length") or 0); done = 0
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk: break
                out.write(chunk); done += len(chunk)
                if progress: progress(done, total)
        if not zipfile.is_zipfile(archive):
            raise RuntimeError("O arquivo baixado não é um zip válido.")
        extract = tmp_dir / "extract"
        with zipfile.ZipFile(archive) as z:
            z.extractall(extract)
        found = next(extract.rglob(must_contain), None)
        if found is None:
            raise RuntimeError(f"{must_contain} não encontrado no pacote baixado.")
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(found.parent), str(target))
        return str(target)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

def install_adb(progress=None) -> str:
    """Instala o Android Platform Tools (adb/fastboot) em ManagerDroid/adb. Retorna o caminho do adb.exe."""
    folder = download_and_extract(ADB_URL, ADB_DIR, "adb.exe", progress)
    return str(Path(folder) / "adb.exe")

def find_tool(name: str) -> str | None:
    if name == "scrcpy" and SETTINGS.get("scrcpy") and Path(SETTINGS["scrcpy"]).exists(): return SETTINGS["scrcpy"]
    for candidate in (DATA_DIR / "platform-tools" / f"{name}.exe", ADB_DIR / f"{name}.exe",
                      DATA_DIR / "tools" / f"{name}.exe", SCRCPY_DIR / f"{name}.exe"):
        if candidate.exists(): return str(candidate)
    return shutil.which(name) or shutil.which(name + ".exe")

def run_command(args, timeout=90, cancel_event=None) -> str:
    """Executa sem shell, com timeout explícito e cancelamento opcional.

    Popen + communicate em intervalos curtos permite cancelar tarefas longas sem
    bloquear a interface. Em timeout/cancelamento o processo filho é encerrado.
    """
    command = [str(x) for x in args]
    try:
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8", errors="replace",
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError as exc:
        raise RuntimeError(f"Não foi possível iniciar '{command[0] if command else 'comando'}': {exc}") from exc
    deadline = time.monotonic() + max(1, float(timeout))
    while True:
        if cancel_event is not None and cancel_event.is_set():
            try: p.terminate()
            except OSError: pass
            try: out, err = p.communicate(timeout=1.5)
            except subprocess.TimeoutExpired:
                p.kill(); out, err = p.communicate()
            raise RuntimeError("Operação cancelada pelo usuário.")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            try: p.kill()
            except OSError: pass
            out, err = p.communicate()
            raise RuntimeError(f"Tempo limite excedido ({timeout}s): {Path(command[0]).name if command else 'comando'}")
        try:
            out, err = p.communicate(timeout=min(0.25, remaining))
            break
        except subprocess.TimeoutExpired:
            continue
    out, err = (out or "").strip(), (err or "").strip()
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

APP_INDEX = CACHE_DIR / "app_index.json"   # pacote -> {"label": ..., "icon": bool}

def _load_app_index() -> dict:
    try:
        data = json.loads(APP_INDEX.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}

def _save_app_index(data: dict):
    try:
        APP_INDEX.parent.mkdir(parents=True, exist_ok=True)
        tmp = APP_INDEX.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(APP_INDEX)
    except OSError:
        pass

def _installed_packages(adb) -> set:
    out = run_command(adb + ["shell", "pm", "list", "packages"], 60)
    return {line[len("package:"):].strip() for line in out.splitlines() if line.startswith("package:")}

def _send_helper_broadcast(adb):
    """Envia o pedido de exportação ao helper.
    Apps instalados por adb ficam 'parados' até serem abertos pela primeira vez; o broadcast
    precisa incluir pacotes parados para alcançá-los. Se o aparelho não aceitar a opção, tenta sem ela."""
    base = ["shell", "am", "broadcast"]
    out = run_command(adb + base + ["--include-stopped-packages", "-a", HELPER_ACTION, "-p", HELPER_PKG], 30)
    if "completed" not in (out or "").lower():
        out = run_command(adb + base + ["-a", HELPER_ACTION, "-p", HELPER_PKG], 30)
    return out

def _fetch_new_apps(adb, new, index, timeout):
    """Pede ao helper nome e ícone somente dos pacotes novos e os grava no índice."""
    request_file = Path(tempfile.gettempdir()) / "droicontrol_request.txt"
    request_file.write_text("\n".join(new) + "\n", encoding="utf-8")
    run_command(adb + ["push", str(request_file), f"{HELPER_REMOTE}/request.txt"], 60)
    run_command(adb + ["shell", "rm", "-f", f"{HELPER_REMOTE}/apps.json", f"{HELPER_REMOTE}/error.txt",
                       f"{HELPER_REMOTE}/icons.zip"], 30)
    _send_helper_broadcast(adb)
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
        raise RuntimeError(t("O ManagerDroid Helper não respondeu. Abra o app ManagerDroid Helper no celular uma vez e tente de novo."))

    raw = json.loads(text)
    if isinstance(raw, dict):
        raw = raw.get("apps", raw.get("packages", raw.get("items", [])))
    labels = {}
    for item in (raw if isinstance(raw, list) else []):
        if not isinstance(item, dict): continue
        pkg = str(item.get("pkg") or item.get("packageName") or item.get("package") or "").strip()
        if pkg: labels[pkg] = str(item.get("label") or item.get("name") or pkg).strip() or pkg

    tmp = Path(tempfile.mkdtemp(prefix="dc_helper_"))
    try:
        zip_local = tmp / "icons.zip"
        got_zip = False
        try:
            run_command(adb + ["pull", f"{HELPER_REMOTE}/icons.zip", str(zip_local)], 600)
            got_zip = zip_local.is_file() and zipfile.is_zipfile(zip_local)
        except Exception as e:
            log(f"HELPER icons.zip indisponível: {e}")
        if got_zip:
            with zipfile.ZipFile(zip_local) as z: z.extractall(tmp / "icons")
        else:
            # Helper antigo (sem icons.zip): baixa a pasta inteira.
            run_command(adb + ["pull", HELPER_REMOTE, str(tmp)], 600)
        found = {}
        for p in tmp.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".png", ".webp", ".jpg", ".jpeg"):
                found.setdefault(p.stem, p)

        from PySide6.QtGui import QImage
        ICON_CACHE.mkdir(parents=True, exist_ok=True)
        for pkg in new:
            dest = ICON_CACHE / f"{pkg}.png"
            src_file = found.get(pkg)
            if src_file is not None and src_file.stat().st_size > 0:
                try:
                    if src_file.suffix.lower() == ".png":
                        shutil.copyfile(src_file, dest)
                    else:
                        image = QImage(str(src_file))
                        if image.isNull() or not image.save(str(dest), "PNG"):
                            raise RuntimeError("não foi possível converter o ícone para PNG")
                except Exception as e:
                    log(f"Ícone helper inválido {pkg}: {e}")
            # Mesmo sem ícone, o app entra no índice para não ser pedido de novo.
            index[pkg] = {"label": labels.get(pkg, pkg), "icon": dest.is_file()}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def helper_export(adb, timeout=180):
    """Sincronização inteligente com o Helper.
    1) Lista os apps instalados (rápido).
    2) Sem app novo desde a última vez: não contata o helper; usa o índice salvo.
    3) Com app novo: pede nome e ícone somente desses apps.
    Retorna None se o helper não estiver instalado; senão (entradas, pacotes_novos)."""
    if HELPER_PKG not in run_command(adb + ["shell", "pm", "list", "packages", HELPER_PKG], 30):
        return None
    # Concede o acesso a arquivos ao helper pelo adb (Android 11+), sem precisar tocar no aparelho
    try: run_command(adb + ["shell", "appops", "set", HELPER_PKG, "MANAGE_EXTERNAL_STORAGE", "allow"], 20)
    except Exception: pass
    try:
        status = run_command(adb + ["shell", "appops", "get", HELPER_PKG, "MANAGE_EXTERNAL_STORAGE"], 20)
        if "MANAGE_EXTERNAL_STORAGE" in status and "allow" not in status.lower():
            raise PermissionError(t("Permissão de arquivos não concedida ao helper. Abra o ManagerDroid Helper no aparelho e toque em 'Permitir acesso a arquivos'.") + f" [{status}]")
    except PermissionError: raise
    except Exception: pass

    installed = _installed_packages(adb)
    if not installed:
        raise RuntimeError("não foi possível listar os aplicativos instalados")
    index = _load_app_index()
    # Apps desinstalados saem do índice e do disco.
    for pkg in [p for p in index if p not in installed]:
        index.pop(pkg, None)
        try: (ICON_CACHE / f"{pkg}.png").unlink()
        except OSError: pass
    new = sorted(p for p in installed if p not in index)
    if new:
        _fetch_new_apps(adb, new, index, timeout)
        _save_app_index(index)
    else:
        _save_app_index(index)
    entries = []
    for pkg in sorted(installed):
        meta = index.get(pkg, {})
        icon_file = ICON_CACHE / f"{pkg}.png"
        entries.append((pkg, meta.get("label") or pkg, str(icon_file) if icon_file.is_file() else ""))
    log(f"APPS: {len(installed)} instalados, {len(new)} novos")
    return entries, set(new)

def version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", str(v))) or (0,)

def fmt_size(size) -> str:
    if size is None: return "—"
    if size >= 1024 ** 3: return f"{size / 1024 ** 3:.2f} GB"
    if size >= 1024 ** 2: return f"{size / 1024 ** 2:.1f} MB"
    return f"{size / 1024:.0f} KB"

LOGO_SVG = r'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="160" viewBox="0 0 860 160">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#60A5FA"/>
      <stop offset="1" stop-color="#1D4ED8"/>
    </linearGradient>
    <linearGradient id="screen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#E8EFFD"/>
      <stop offset="1" stop-color="#DBE7FB"/>
    </linearGradient>
  </defs>
  <g transform="scale(0.3125)">
    <rect x="0" y="0" width="512" height="512" rx="112" fill="url(#bg)"/>
    <rect x="150" y="82" width="212" height="348" rx="44" fill="#0B1020" opacity="0.92"/>
    <rect x="166" y="112" width="180" height="288" rx="18" fill="url(#screen)"/>
    <circle cx="256" cy="96" r="5" fill="#60A5FA"/>
    <rect x="186" y="140" width="62" height="62" rx="16" fill="#2563EB"/>
    <rect x="264" y="140" width="62" height="62" rx="16" fill="#60A5FA"/>
    <rect x="186" y="218" width="62" height="62" rx="16" fill="#60A5FA"/>
    <rect x="264" y="218" width="62" height="62" rx="16" fill="#2563EB"/>
    <rect x="216" y="352" width="80" height="8" rx="4" fill="#60A5FA"/>
    <g transform="translate(372 372)">
      <circle r="46" fill="#FFFFFF"/>
      <circle r="22" fill="none" stroke="#2563EB" stroke-width="14"/>
      <g fill="#2563EB">
        <rect x="-7" y="-40" width="14" height="22" rx="4"/>
        <rect x="-7" y="18" width="14" height="22" rx="4"/>
        <rect x="-40" y="-7" width="22" height="14" rx="4"/>
        <rect x="18" y="-7" width="22" height="14" rx="4"/>
      </g>
    </g>
  </g>
  <text x="190" y="98" font-family="Segoe UI, Inter, Helvetica, Arial, sans-serif" font-size="72" font-weight="700" fill="#2563EB">Manager<tspan fill="#0B1020">Droid</tspan></text>
</svg>'''

def logo_pixmap(height: int, dark: bool) -> QPixmap:
    """Renderiza o logotipo com nítido em telas de alta densidade. No tema escuro, o nome usa cor clara."""
    p = PALETTES['dark' if dark else 'light']
    svg = LOGO_SVG.replace('#0B1020', p['text']) if dark else LOGO_SVG
    width = round(height * 860 / 160); scale = 2
    pix = QPixmap(width * scale, height * scale); pix.fill(Qt.transparent)
    painter = QPainter(pix); QSvgRenderer(QByteArray(svg.encode('utf-8'))).render(painter); painter.end()
    pix.setDevicePixelRatio(scale)
    return pix

@functools.lru_cache(maxsize=512)
def svg_pixmap(name: str, color: str, size: int = 18) -> QPixmap | None:
    raw = ICON_SVGS.get(name)
    if not raw: return None
    svg = re.sub(r"#[eE]3[eE]3[eE]3", color, raw)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size * 2, size * 2); pix.fill(Qt.transparent)
    painter = QPainter(pix); renderer.render(painter); painter.end()
    return pix

@functools.lru_cache(maxsize=1024)
def _svg_icon_cached(name: str, color: str, size: int) -> QIcon:
    pix = svg_pixmap(name, color, size)
    return QIcon(pix) if pix else QIcon()

def svg_icon(name: str, color: str, size: int = 18) -> QIcon:
    return _svg_icon_cached(name, color, size)

def load_label_cache() -> dict:
    # Prioriza o cache atual; migra automaticamente o cache da pasta do programa.
    for candidate in (LABEL_CACHE, _OLD_CACHE_DIR / "app_labels.json"):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if candidate != LABEL_CACHE:
                    save_label_cache(data)
                    log(f"Cache de aplicativos migrado: {len(data)} entradas")
                return data
        except (OSError, ValueError, TypeError):
            continue
    return {}

def save_label_cache(data: dict):
    try:
        LABEL_CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = LABEL_CACHE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        tmp.replace(LABEL_CACHE)
    except OSError as exc:
        log(f"Não foi possível salvar o cache de aplicativos: {exc}")

KNOWN_NAMES = {
    "com.android.settings": "Configurações", "com.android.chrome": "Google Chrome",
    "com.google.android.youtube": "YouTube", "com.google.android.gms": "Google Play Services",
    "com.android.vending": "Google Play Store", "com.google.android.gm": "Gmail",
    "com.google.android.apps.maps": "Google Maps", "com.whatsapp": "WhatsApp",
    "com.facebook.katana": "Facebook", "com.instagram.android": "Instagram",
    "com.spotify.music": "Spotify", "com.netflix.mediaclient": "Netflix",
    "com.microsoft.emmx": "Microsoft Edge", "com.google.android.apps.photos": "Google Fotos",
}

class Worker(QThread):
    done = Signal(object, object)  # resultado, erro (None em caso de sucesso)
    def __init__(self, fn):
        super().__init__(); self.fn = fn
    def run(self):
        try: self.done.emit(self.fn(), None)
        except Exception as e: self.done.emit(None, str(e) or repr(e))

HELPER_APK_URL = "https://github.com/Skinnyzin/ManagerDroid-Help/releases/download/managerdroidhelper02/ManagerDroid-Helper.apk"
HELPER_DOWNLOAD_REMOTE = "/sdcard/Download/ManagerDroid-Helper.apk"

def download_helper_apk(progress=None) -> str:
    """Baixa o APK do helper do GitHub, valida que é um APK e retorna o caminho do arquivo temporário."""
    dest_dir = Path(tempfile.mkdtemp(prefix="managerdroid_helper_"))
    dest = dest_dir / "ManagerDroid-Helper.apk"
    req = urllib.request.Request(HELPER_APK_URL, headers={"User-Agent": "ManagerDroid"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0); done = 0
        while True:
            chunk = resp.read(64 * 1024)
            if not chunk: break
            out.write(chunk); done += len(chunk)
            if progress: progress(done, total)
    if dest.stat().st_size < 10_000:
        raise RuntimeError("O arquivo baixado é pequeno demais para ser um APK.")
    with open(dest, "rb") as f:
        if f.read(2) != b"PK":
            raise RuntimeError("O arquivo baixado não é um APK válido.")
    return str(dest)

class ToolInstaller(QThread):
    """Roda uma função de instalação (download + extração) fora da thread da interface."""
    progress = Signal(int, int)
    installed = Signal(str)
    failed = Signal(str)
    def __init__(self, install_fn):
        super().__init__(); self.install_fn = install_fn
    def run(self):
        try: self.installed.emit(self.install_fn(lambda done, total: self.progress.emit(done, total)))
        except Exception as e: self.failed.emit(str(e) or repr(e))

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
    lay = QVBoxLayout(frame); lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(7)
    head = QLabel(title); head.setObjectName("CardTitle"); lay.addWidget(head)
    if hint:
        h = QLabel(hint); h.setObjectName("CardHint"); h.setWordWrap(True); lay.addWidget(h)
    return frame, lay

def make_tile(caption: str):
    frame = QFrame(); frame.setObjectName("Tile")
    lay = QVBoxLayout(frame); lay.setContentsMargins(10, 8, 10, 8); lay.setSpacing(2)
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
        super().__init__(parent); self.setWindowTitle(title); self.resize(760, 520)
        lay = QVBoxLayout(self)
        view = QPlainTextEdit(); view.setReadOnly(True); view.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        view.setPlainText(text); lay.addWidget(view)
        bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(self.reject); lay.addWidget(bb)


# Explicações em linguagem comum para permissões Android frequentes.
PERMISSION_DESCRIPTIONS = {
    "INTERNET": "Acessar a internet.",
    "ACCESS_NETWORK_STATE": "Acessar informações sobre as redes disponíveis.",
    "ACCESS_WIFI_STATE": "Consultar o estado da conexão Wi-Fi.",
    "CHANGE_WIFI_STATE": "Alterar o estado da conexão Wi-Fi.",
    "ACCESS_FINE_LOCATION": "Acessar a localização precisa do dispositivo.",
    "ACCESS_COARSE_LOCATION": "Acessar uma localização aproximada do dispositivo.",
    "ACCESS_BACKGROUND_LOCATION": "Acessar a localização mesmo quando o app não está em uso.",
    "CAMERA": "Usar a câmera do dispositivo.",
    "RECORD_AUDIO": "Gravar áudio usando o microfone.",
    "READ_CONTACTS": "Ler os contatos armazenados no dispositivo.",
    "WRITE_CONTACTS": "Adicionar ou alterar contatos.",
    "READ_CALENDAR": "Ler eventos da agenda.",
    "WRITE_CALENDAR": "Adicionar ou alterar eventos da agenda.",
    "READ_CALL_LOG": "Ler o histórico de chamadas.",
    "WRITE_CALL_LOG": "Alterar o histórico de chamadas.",
    "CALL_PHONE": "Iniciar chamadas telefônicas.",
    "READ_PHONE_STATE": "Consultar informações sobre o telefone e a rede móvel.",
    "READ_PHONE_NUMBERS": "Consultar o número de telefone, quando disponível.",
    "SEND_SMS": "Enviar mensagens SMS.",
    "RECEIVE_SMS": "Receber e ler mensagens SMS.",
    "READ_SMS": "Ler mensagens SMS.",
    "POST_NOTIFICATIONS": "Enviar notificações (Android 13 ou superior exige autorização).",
    "VIBRATE": "Usar a vibração do dispositivo.",
    "WAKE_LOCK": "Manter o dispositivo ativo temporariamente.",
    "BLUETOOTH": "Conectar-se a dispositivos Bluetooth (permissão antiga).",
    "BLUETOOTH_CONNECT": "Conectar-se e consultar dispositivos Bluetooth próximos.",
    "BLUETOOTH_SCAN": "Procurar dispositivos Bluetooth próximos.",
    "BLUETOOTH_ADVERTISE": "Permitir que o dispositivo seja encontrado por Bluetooth.",
    "NFC": "Usar a comunicação por aproximação (NFC).",
    "READ_EXTERNAL_STORAGE": "Ler arquivos do armazenamento compartilhado (restrito em versões recentes).",
    "WRITE_EXTERNAL_STORAGE": "Gravar arquivos no armazenamento compartilhado (restrito em versões recentes).",
    "READ_MEDIA_IMAGES": "Ler imagens compartilhadas no dispositivo.",
    "READ_MEDIA_VIDEO": "Ler vídeos compartilhados no dispositivo.",
    "READ_MEDIA_AUDIO": "Ler arquivos de áudio compartilhados no dispositivo.",
    "MANAGE_EXTERNAL_STORAGE": "Acessar e gerenciar amplamente arquivos do armazenamento compartilhado.",
    "REQUEST_INSTALL_PACKAGES": "Solicitar instalação de aplicativos de outras fontes.",
    "SYSTEM_ALERT_WINDOW": "Exibir janelas sobre outros aplicativos.",
    "PACKAGE_USAGE_STATS": "Consultar estatísticas de uso de aplicativos (acesso especial).",
    "QUERY_ALL_PACKAGES": "Consultar a lista de aplicativos instalados.",
    "RECEIVE_BOOT_COMPLETED": "Iniciar uma tarefa após o dispositivo terminar de ligar.",
    "FOREGROUND_SERVICE": "Executar tarefas em primeiro plano com uma notificação.",
    "POST_NOTIFICATIONS": "Mostrar notificações.",
    "USE_BIOMETRIC": "Usar autenticação biométrica, se disponível.",
    "USE_FINGERPRINT": "Usar o leitor de impressão digital (permissão antiga).",
    "GET_ACCOUNTS": "Consultar contas cadastradas no dispositivo.",
    "SET_WALLPAPER": "Alterar o papel de parede.",
    "SET_ALARM": "Criar alarmes no dispositivo.",
}

def describe_permission(permission: str) -> str:
    name = permission.rsplit(".", 1)[-1]
    if name in PERMISSION_DESCRIPTIONS:
        return PERMISSION_DESCRIPTIONS[name]
    # Fallback legível para permissões de fabricantes ou versões futuras.
    words = name.replace("_", " ").lower()
    return "Permissão específica do Android: " + words + ". Consulte a documentação do aplicativo para detalhes."

class PermissionsDialog(QDialog):
    def __init__(self, parent, title, rows):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(850, 540)
        self.setMinimumSize(620, 360)
        layout = QVBoxLayout(self)
        intro = QLabel("Estas permissões foram encontradas no pacote. A descrição é uma explicação simplificada; o acesso efetivo depende da versão do Android e das autorizações concedidas.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        table = QTableWidget(len(rows), 3)
        table.setHorizontalHeaderLabels(["Permissão", "O que significa", "Estado"])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setWordWrap(True)
        table.setTextElideMode(Qt.ElideNone)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        for row, (permission, description, state) in enumerate(rows):
            for col, value in enumerate((permission, description, state)):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                table.setItem(row, col, item)
            table.setRowHeight(row, 54)
        layout.addWidget(table, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)

class SettingsDialog(QDialog):
    """Configurações: somente tema e idioma."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(t("Configurações")); self.setMinimumWidth(380)
        p = PALETTES["dark" if SETTINGS.get("dark", True) else "light"]
        lay = QVBoxLayout(self); lay.setContentsMargins(22, 20, 22, 18); lay.setSpacing(16)

        def row(icon_name, label_text, combo):
            wrap = QHBoxLayout(); wrap.setSpacing(12)
            icon = QLabel(); icon.setPixmap(svg_icon(icon_name, p["accent"], 20).pixmap(20, 20))
            label = QLabel(label_text); label.setStyleSheet(f"color: {p['muted']};")
            wrap.addWidget(icon); wrap.addWidget(label, 1); wrap.addWidget(combo)
            return wrap

        self.theme_choice = QComboBox()
        self.theme_choice.addItem(svg_icon("dark_mode", p["text"], 18), t("Escuro"), True)
        self.theme_choice.addItem(svg_icon("light_mode", p["text"], 18), t("Claro"), False)
        self.theme_choice.setCurrentIndex(0 if SETTINGS.get("dark", True) else 1)

        self.language_choice = QComboBox()
        self.language_choice.addItem(svg_icon("language", p["text"], 18), "Português", "pt")
        self.language_choice.addItem(svg_icon("language", p["text"], 18), "English", "en")
        self.language_choice.setCurrentIndex(0 if SETTINGS.get("lang", "pt") == "pt" else 1)

        for combo in (self.theme_choice, self.language_choice):
            combo.setMinimumWidth(170)
        lay.addLayout(row("dark_mode", t("Tema"), self.theme_choice))
        lay.addLayout(row("language", t("Idioma / Language"), self.language_choice))
        lay.addStretch(1)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._save); bb.rejected.connect(self.reject); lay.addWidget(bb)

    def _save(self):
        SETTINGS["dark"] = bool(self.theme_choice.currentData())
        SETTINGS["lang"] = self.language_choice.currentData()
        save_settings(SETTINGS); self.accept()


class OnboardingDialog(QDialog):
    """Assistente de primeira execução: como ativar o modo desenvolvedor e a depuração USB."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(t("Bem-vindo ao ManagerDroid")); self.setMinimumWidth(480)
        self._p = PALETTES["dark" if SETTINGS.get("dark", True) else "light"]
        self._steps = [
            ("mobile", t("Ative as opções do desenvolvedor"),
             t("Abra Configurações > Sobre o telefone e toque 7 vezes em “Número da versão” (ou “Número da compilação”). Se pedir, digite o PIN. Aparecerá a mensagem “Você agora é um desenvolvedor”.")),
            ("build", t("Ative a depuração USB"),
             t("Volte às Configurações e abra Opções do desenvolvedor (em alguns aparelhos fica dentro de Sistema ou Configurações adicionais). Ative “Depuração USB”.")),
            ("lock_open", t("Conecte o cabo e aceite a chave"),
             t("Conecte o celular ao computador. Quando aparecer “Permitir depuração USB?”, marque “Sempre permitir deste computador” e toque em Permitir.")),
            ("toggle_on", t("Xiaomi, Redmi e POCO (opcional)"),
             t("Em Opções do desenvolvedor, ative também “Instalar via USB” e “Depuração USB (configurações de segurança)”. Se o aparelho pedir, entre com a conta Mi.")),
            ("checkbox_checked", t("Pronto!"),
             t("Escolha o aparelho no topo da janela para começar. Se ele não aparecer, confira o cabo e a autorização de depuração.")),
        ]
        self._index = 0
        lay = QVBoxLayout(self); lay.setContentsMargins(26, 24, 26, 18); lay.setSpacing(12)

        self.icon_label = QLabel(); self.icon_label.setFixedSize(56, 56); self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet(f"background: {self._p['accent_soft']}; border-radius: 16px;")
        self.title_label = QLabel(); self.title_label.setStyleSheet("font-size: 14pt; font-weight: 700;")
        self.body_label = QLabel(); self.body_label.setWordWrap(True)
        self.body_label.setStyleSheet(f"color: {self._p['muted']}; font-size: 10.5pt;")
        self.counter = QLabel(); self.counter.setStyleSheet(f"color: {self._p['muted']}; font-size: 9pt;")
        lay.addWidget(self.icon_label, 0, Qt.AlignLeft)
        lay.addWidget(self.title_label); lay.addWidget(self.body_label); lay.addStretch(1)

        nav = QHBoxLayout()
        self.counter_wrap = QHBoxLayout(); self.counter_wrap.addWidget(self.counter)
        self.back_btn = make_button(t("Voltar")); self.back_btn.clicked.connect(self._back)
        self.next_btn = make_button(t("Próximo")); self.next_btn.setObjectName("Primary")
        self.next_btn.setStyleSheet(
            f"QPushButton {{ background: {self._p['accent']}; color: {self._p['accent_text']}; border: 0; "
            f"border-radius: 9px; padding: 8px 20px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {self._p['accent_hover']}; }}")
        self.next_btn.clicked.connect(self._next)
        nav.addLayout(self.counter_wrap); nav.addStretch(1); nav.addWidget(self.back_btn); nav.addWidget(self.next_btn)
        lay.addLayout(nav)
        self._show()

    def _show(self):
        icon_name, title, body = self._steps[self._index]
        self.icon_label.setPixmap(svg_icon(icon_name, self._p["accent"], 28).pixmap(28, 28))
        self.title_label.setText(title); self.body_label.setText(body)
        self.counter.setText(t("Passo {n} de {total}").format(n=self._index + 1, total=len(self._steps)))
        self.back_btn.setEnabled(self._index > 0)
        last = self._index == len(self._steps) - 1
        self.next_btn.setText(t("Concluir") if last else t("Próximo"))

    def _next(self):
        if self._index == len(self._steps) - 1:
            self.accept(); return
        self._index += 1; self._show()

    def _back(self):
        self._index = max(0, self._index - 1); self._show()


# ---------------------------------------------------------------- janela principal
class ManagerDroid(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 780); self.setMinimumSize(1020, 660)
        self.dark = bool(SETTINGS.get("dark", True))
        self.device: str | None = None
        self.workers: list[QThread] = []
        self.info_worker = None
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
        self._install_cancel_event = threading.Event()
        self._install_running = False
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
        self._refresh_dialog = None
        self._refresh_waiting_info = False
        self._build_ui()
        self.apply_theme()
        self._setup_pc_ram_indicator()
        self.refresh_devices()
        QTimer.singleShot(400, self._startup_dialogs)

    # ---------- construção (reconstruída ao trocar de idioma)
    def _build_ui(self):
        self.setUpdatesEnabled(False)
        try:
            self._build_ui_inner()
        finally:
            self.setUpdatesEnabled(True)

    def _build_ui_inner(self):
        self._icon_widgets = []
        root = QWidget(); root.setObjectName("Root"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        top = QWidget(); top.setObjectName("TopBar"); top.setFixedHeight(64)
        tl = QHBoxLayout(top); tl.setContentsMargins(20, 0, 16, 0); tl.setSpacing(10)
        brand = QLabel(); brand.setPixmap(logo_pixmap(36, bool(SETTINGS.get("dark", True))))
        brand.setToolTip(APP_NAME); tl.addWidget(brand)
        self.brand_label = brand
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
        settings_btn = make_button(t("Configurações"), "Ghost"); settings_btn.clicked.connect(self.open_settings)
        tl.addWidget(settings_btn)
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
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(6, 6, 6, 6); lay.setSpacing(6)
        head = QLabel(t("Visão geral")); head.setObjectName("PageTitle"); lay.addWidget(head)
        content = QHBoxLayout(); content.setSpacing(8)

        # Coluna esquerda: dados e monitoramento, sem exceder a largura da janela.
        left_col = QWidget(); left = QVBoxLayout(left_col); left.setContentsMargins(0, 0, 0, 0); left.setSpacing(8)
        grid = QGridLayout(); grid.setSpacing(5); grid.setContentsMargins(0, 0, 0, 0)
        self.tiles = {}
        for i, (key, caption) in enumerate([("model", t("Modelo")), ("security", t("Patch de segurança")),
                                            ("android", t("Versão do Android")), ("serial", t("Número de série"))]):
            frame, val = make_tile(caption); self.tiles[key] = val
            frame.setMinimumWidth(0); frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            grid.addWidget(frame, i // 2, i % 2)
        left.addLayout(grid)

        mon = QVBoxLayout(); mon.setSpacing(6)
        storage_card, sl = make_card(t("Armazenamento"))
        self.storage_usage_label = QLabel("—"); self.storage_usage_label.setObjectName("BigValue")
        self.storage_usage_label.setWordWrap(True); sl.addWidget(self.storage_usage_label)
        self.storage_bar = QProgressBar(); self.storage_bar.setRange(0, 100); self.storage_bar.setValue(0); self.storage_bar.setTextVisible(False); sl.addWidget(self.storage_bar)
        mon.addWidget(storage_card)
        ram_card, rl = make_card(t("Memória RAM"))
        rh = QHBoxLayout(); rh.setSpacing(6)
        self.ram_icon = QLabel(); self._bind_icon_label(self.ram_icon, "memory")
        self.ram_label = QLabel("—"); self.ram_label.setObjectName("BigValue"); self.ram_label.setWordWrap(True)
        rh.addWidget(self.ram_icon); rh.addWidget(self.ram_label, 1); rl.addLayout(rh)
        self.ram_bar = QProgressBar(); self.ram_bar.setRange(0, 100); self.ram_bar.setValue(0); self.ram_bar.setTextVisible(False); rl.addWidget(self.ram_bar)
        mon.addWidget(ram_card)
        batt_card, bl2 = make_card(t("Bateria"))
        bh = QHBoxLayout(); bh.setSpacing(6)
        self.batt_icon = QLabel(); self._bind_icon_label(self.batt_icon, "battery")
        self.batt_label = QLabel("—"); self.batt_label.setObjectName("BigValue"); self.batt_label.setWordWrap(True)
        bh.addWidget(self.batt_icon); bh.addWidget(self.batt_label, 1); bl2.addLayout(bh)
        self.batt_bar = QProgressBar(); self.batt_bar.setRange(0, 100); self.batt_bar.setValue(0); self.batt_bar.setTextVisible(False); bl2.addWidget(self.batt_bar)
        self.temp_label = QLabel(t("Temperatura da bateria") + ": —"); self.temp_label.setObjectName("CardHint"); bl2.addWidget(self.temp_label)
        mon.addWidget(batt_card)
        left.addLayout(mon)
        content.addWidget(left_col, 3)

        # Coluna direita: telefone maior, como na referência enviada.
        phone_card, phone_lay = make_card(t("Dispositivo conectado"))
        phone_lay.setAlignment(Qt.AlignCenter)
        phone_stage = QWidget(); phone_stage.setMinimumSize(180, 360); phone_stage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        phone_grid = QGridLayout(phone_stage); phone_grid.setContentsMargins(0, 0, 0, 0); phone_grid.setAlignment(Qt.AlignCenter)
        self.phone_silhouette = QLabel(); self.phone_silhouette.setAlignment(Qt.AlignCenter)
        self.phone_silhouette.setFixedSize(250, 420)
        self._render_phone_silhouette()
        self.phone_logo = QLabel(); self.phone_logo.setAlignment(Qt.AlignCenter); self.phone_logo.setFixedSize(76, 76)
        phone_grid.addWidget(self.phone_silhouette, 0, 0, Qt.AlignCenter)
        phone_grid.addWidget(self.phone_logo, 0, 0, Qt.AlignCenter)
        phone_lay.addWidget(phone_stage, 1, Qt.AlignCenter)
        self.phone_brand_label = QLabel(t("Aguardando dispositivo…")); self.phone_brand_label.setObjectName("CardHint"); self.phone_brand_label.setAlignment(Qt.AlignCenter); self.phone_brand_label.setWordWrap(True)
        phone_lay.addWidget(self.phone_brand_label)
        self._set_phone_brand_logo("android")
        content.addWidget(phone_card, 2)
        lay.addLayout(content, 1)
        return self._scroll(w)

    def _render_phone_silhouette(self):
        if not hasattr(self, "phone_silhouette"): return
        p = PALETTES["dark" if self.dark else "light"]
        svg = PHONE_SVG.replace('fill="#20242b"', f'fill="{p["phone"]}"', 1)
        pix = QPixmap(250, 420); pix.fill(Qt.transparent)
        painter = QPainter(pix); QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter); painter.end()
        self.phone_silhouette.setPixmap(pix)

    def _set_phone_brand_logo(self, brand):
        key = (brand or "").lower()
        if any(x in key for x in ("xiaomi", "redmi", "poco", "mi inc")): key = "xiaomi"
        elif "samsung" in key: key = "samsung"
        elif any(x in key for x in ("motorola", "moto", "lenovo")): key = "motorola"
        else: key = "android"
        svg = BRAND_SVGS[key]
        pix = QPixmap(68, 68); pix.fill(Qt.transparent)
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        painter = QPainter(pix); renderer.render(painter); painter.end()
        self.phone_logo.setPixmap(pix)
        self.phone_brand_label.setText({"xiaomi": "Xiaomi / Redmi / POCO", "samsung": "Samsung", "motorola": "Motorola", "android": t("Marca não reconhecida — Android")}[key])

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
                req = urllib.request.Request("https://raw.githubusercontent.com/Universal-Debloater-Alliance/universal-android-debloater-next-generation/main/resources/assets/uad_lists.json", headers={"User-Agent": "ManagerDroid"})
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
                    record_change("debloat_uninstall", pkg, True, out or "Success")
                except Exception as e:
                    results.append((pkg, False, str(e)))
                    record_change("debloat_uninstall", pkg, False, str(e))
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
        self.install_progress = QProgressBar(); self.install_progress.setRange(0, 100)
        self.install_progress.setValue(0); self.install_progress.setTextVisible(True)
        self.install_progress.setFormat("%p%")
        self.install_progress.setMinimumHeight(22); self.install_progress.setMaximumHeight(24)
        self.install_progress.setStyleSheet("QProgressBar { min-height: 22px; max-height: 24px; padding: 1px 4px; text-align: center; border-radius: 5px; } QProgressBar::chunk { border-radius: 4px; }")
        il.addWidget(self.install_progress)
        r = QHBoxLayout()
        browse = make_button(t("Escolher…")); browse.clicked.connect(self.pick_install)
        self.install_cancel_btn = make_button(t("Cancelar"), "Danger"); self.install_cancel_btn.setEnabled(False)
        self.install_cancel_btn.clicked.connect(self.cancel_installation)
        history = make_button(t("Histórico")); history.clicked.connect(self.show_change_history)
        go = make_button(t("Instalar"), "Primary"); go.clicked.connect(self.install_files)
        self.install_go_btn = go
        r.addWidget(browse); r.addWidget(history); r.addWidget(self.install_cancel_btn); r.addStretch(1); r.addWidget(go); il.addLayout(r)
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

        actions, al = make_card(t("Ações"), t("Espelhamento usa o scrcpy; reinício envia o comando ao aparelho."))
        row = QHBoxLayout(); row.setSpacing(10)
        mirror = make_button(t("Espelhar tela"), "Primary"); mirror.clicked.connect(self.launch_scrcpy); self._bind_icon(mirror, "mobile", "accent_text")
        shot = make_button(t("Captura de tela")); shot.clicked.connect(self.take_screenshot); self._bind_icon(shot, "download")
        refresh = make_button(t("Atualizar informações")); refresh.clicked.connect(self.refresh_device_details); self._bind_icon(refresh, "refresh")
        for b in (mirror, shot, refresh): row.addWidget(b)
        row.addStretch(1); al.addLayout(row)
        rr = QHBoxLayout(); rr.setSpacing(10)
        self.reboot_mode = NoWheelComboBox()
        for label, mode in [(t("Sistema normal"), ""), (t("Recovery"), "recovery"), (t("Bootloader"), "bootloader"), (t("Fastboot"), "fastboot")]:
            self.reboot_mode.addItem(label, mode)
        self.reboot_mode.setMinimumWidth(200)
        reboot = make_button(t("Reiniciar"), "Danger"); reboot.clicked.connect(lambda: self.reboot(self.reboot_mode.currentData()))
        rr.addWidget(QLabel(t("Reiniciar para:"))); rr.addWidget(self.reboot_mode); rr.addWidget(reboot); rr.addStretch(1)
        al.addLayout(rr)
        grid.addWidget(actions, 3, 0, 1, 2)
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
        if getattr(self, "chart", None) is not None:
            try: self.chart.colors = p; self.chart.update()
            except RuntimeError: pass
        self._render_phone_silhouette()
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
        self.setUpdatesEnabled(False)
        try:
            self.setStyleSheet(qss)
            self._refresh_icons()
            if hasattr(self, "brand_label"):
                self.brand_label.setPixmap(logo_pixmap(36, self.dark))
        finally:
            self.setUpdatesEnabled(True)

    def _wait_workers(self, ms):
        for w in list(self.workers):
            try:
                if w.isRunning(): w.wait(ms)
            except RuntimeError:
                pass

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
        self.statusBar().showMessage(t("Dispositivo desconectado; tentando recuperar a conexão ADB…"), 8000)
        try:
            adb = self.adb()
            # Não repete comandos que alteram dados: apenas solicita reconexão de dispositivos offline.
            self.run_async(lambda: (run_command(adb + ["reconnect", "offline"], 12) if adb else ""),
                           lambda _r, _e: QTimer.singleShot(900, lambda: self.refresh_devices(force=True)))
        except Exception:
            QTimer.singleShot(900, lambda: self.refresh_devices(force=True))

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
                self, t("ManagerDroid Helper"),
                t("O ManagerDroid Helper não está instalado neste dispositivo. Deseja instalá-lo agora?"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if answer != QMessageBox.Yes:
                return
            self._install_tool(t("Baixando ManagerDroid Helper..."), download_helper_apk,
                               self._install_helper_apk, on_fail_title=t("ManagerDroid Helper"))
        self.run_async(work, done)

    def _install_helper_apk(self, apk_path):
        adb = self.adb()
        def install_work():
            try:
                out = check_install_output(run_command(adb + ["install", "-r", apk_path], 240))
                # Instalado com sucesso: remove a cópia da pasta Download, se ela existir.
                try: run_command(adb + ["shell", "rm", "-f", HELPER_DOWNLOAD_REMOTE], 15)
                except Exception: pass
            except Exception as e:
                msg = str(e) or repr(e)
                try:
                    run_command(adb + ["push", apk_path, HELPER_DOWNLOAD_REMOTE], 240)
                except Exception as pe:
                    raise RuntimeError(msg + "\n" + t("Também falhou ao enviar para a pasta Download:") + f" {pe}")
                raise RuntimeError(
                    t("Não foi possível instalar o ManagerDroid Helper automaticamente.") + "\n\n" +
                    t("O APK foi enviado para a pasta Download do aparelho:") + " ManagerDroid-Helper.apk\n" +
                    t("Abra-o pelo gerenciador de arquivos para instalar.") + "\n\n" +
                    t("Detalhes:") + " " + msg)
            finally:
                shutil.rmtree(Path(apk_path).parent, ignore_errors=True)
            # Concede permissões runtime declaradas pelo APK; as indisponíveis nesta versão são ignoradas.
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
            return out or t("ManagerDroid Helper instalado.")
        def installed_done(result, install_error):
            if install_error:
                QMessageBox.critical(self, t("Erro ao instalar ManagerDroid Helper"), str(install_error))
                return
            QMessageBox.information(self, t("ManagerDroid Helper"),
                t("ManagerDroid Helper instalado. Se o Android solicitar uma permissão especial, autorize-a no aparelho."))
            self._helper_absent = None
            if self.stack.currentIndex() == 1:
                self.load_apps()
        self.run_async(install_work, installed_done)

    def _page_changed(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0 and self.device:
            self.monitor_tick(); self._monitor_timer.start()
        else:
            self._monitor_timer.stop()
        # A aba Aplicativos não inicia escaneamentos automaticamente.
        # O usuário controla a atualização pelo botão Atualizar.
        if index == 3: self.refresh_log()

    def refresh_device_details(self):
        if not self.device: return
        try: adb = self.adb()
        except Exception as e: self.statusBar().showMessage(str(e), 6000); return
        def work():
            # Uma única chamada ao aparelho: `getprop` devolve todas as propriedades de uma vez.
            raw = run_command(adb + ["shell", "getprop"], 30)
            props = {k.strip(): v.strip() for k, v in re.findall(r"\[([^\]]+)\]:\s*\[([^\]]*)\]", raw)}
            def first(*names):
                for name in names:
                    value = props.get(name, "")
                    if value.lower() not in ("", "unknown", "null", "none"):
                        return value
                return ""
            manufacturer = first("ro.product.manufacturer", "ro.product.vendor.manufacturer",
                                 "ro.product.odm.manufacturer", "ro.product.system.manufacturer")
            brand = first("ro.product.brand", "ro.product.vendor.brand",
                          "ro.product.odm.brand", "ro.product.system.brand")
            model_name = first("ro.product.model", "ro.product.vendor.model",
                               "ro.product.odm.model", "ro.product.system.model")
            android = first("ro.build.version.release")
            serial = first("ro.serialno")
            # Patch de segurança: procura em todas as partições que expõem a data (AAAA-MM-DD).
            security = ""
            for name in ("ro.build.version.security_patch", "ro.vendor.build.security_patch",
                         "ro.system.build.version.security_patch",
                         "ro.system_ext.build.version.security_patch",
                         "ro.odm.build.version.security_patch"):
                m = re.search(r"20\d{2}-\d{2}-\d{2}", props.get(name, ""))
                if m:
                    security = m.group(0); break
            if not security:
                m = re.search(r"security_patch\]:\s*\[(20\d{2}-\d{2}-\d{2})\]", raw)
                if m: security = m.group(1)
            # Identificação da marca: usa todas as propriedades, inclusive fingerprint.
            identity = " ".join(props.get(k, "") for k in (
                "ro.product.device", "ro.product.name", "ro.build.product",
                "ro.build.fingerprint", "ro.vendor.build.fingerprint", "ro.product.model")).lower()
            combined = f"{manufacturer} {brand} {model_name} {identity}".lower()
            if re.search(r"xiaomi|redmi|poco", combined):
                family, manufacturer = "xiaomi", "Xiaomi"
            elif re.search(r"samsung|\bsm-[a-z0-9]+", combined):
                family, manufacturer = "samsung", "Samsung"
            elif re.search(r"motorola|\bmoto|lenovo|\bxt2\d{3}", combined):
                family, manufacturer = "motorola", "Motorola"
            else:
                family = "android"
            if not manufacturer: manufacturer = brand
            manufacturer = manufacturer[:1].upper() + manufacturer[1:] if manufacturer else ""
            model_text = " ".join(x for x in (manufacturer, model_name) if x) or "—"
            return {"model": model_text, "family": family, "android": android or "—",
                    "serial": serial or "—", "security": security}
        self.run_async(work, self._device_details_result)

    def _device_details_result(self, info, error):
        if info: self._last_info = info
        if error or not info:
            self.tiles["model"].setText(t("Não foi possível ler as informações")); return
        self.tiles["model"].setText(info["model"])
        self.tiles["android"].setText(info["android"])
        self.tiles["serial"].setText(info["serial"])
        self._set_security_tile(info.get("security", ""))
        self._set_phone_brand_logo(info.get("family", "android"))

    def _set_security_tile(self, patch: str):
        """Mostra o patch de segurança colorido pela idade: verde ≤6 meses, amarelo ≤1 ano, vermelho acima."""
        p = PALETTES["dark" if self.dark else "light"]
        label = self.tiles["security"]
        if not patch:
            label.setText("—"); label.setStyleSheet(""); return
        try: days = (datetime.now().date() - datetime.strptime(patch, "%Y-%m-%d").date()).days
        except ValueError: days = 0
        if days <= 180:
            color, text = p["success"], patch
        elif days <= 365:
            color, text = "#F59E0B", f"{patch} · há {days // 30} meses"
        else:
            color, text = p["danger"], f"{patch} · há {days // 30} meses"
        label.setText(text); label.setStyleSheet(f"color: {color};")

    def _set_usage_bar_color(self, bar, percent, inverse=False):
        """Azul = normal, âmbar = atenção, vermelho = crítico. Bateria usa a lógica invertida (baixo = crítico)."""
        p = PALETTES["dark" if self.dark else "light"]
        warn = "#F59E0B"
        if inverse:
            color = p["danger"] if percent <= 20 else (warn if percent <= 50 else p["accent"])
        else:
            color = p["danger"] if percent >= 85 else (warn if percent >= 60 else p["accent"])
        bar.setStyleSheet(
            f"QProgressBar {{ background: {p['surface2']}; border: 1px solid {p['border']}; "
            f"border-radius: 6px; min-height: 10px; max-height: 10px; }} "
            f"QProgressBar::chunk {{ background: {color}; border-radius: 6px; }}")

    # ---------- monitoramento (RAM, armazenamento, bateria, temperatura) em tempo real
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
            try:
                df = run_command(adb + ["shell", "df", "-k", "/data"], 15).splitlines()
                cols = df[-1].split() if len(df) > 1 else []
                if len(cols) >= 4:
                    total_k, used_k = int(cols[1]), int(cols[2])
                    out["storage"] = (used_k * 1024, total_k * 1024)
                else: out["storage"] = None
            except Exception: out["storage"] = None
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
                self._set_usage_bar_color(self.ram_bar, ram_pct, inverse=False)
                used_txt = f"{used / 1024:.0f}MB" if used < 1024 else f"{used / 1024:.1f}GB"
                total_txt = f"{total / 1024:.0f}MB" if total < 1024 else f"{total / 1024:.1f}GB"
                self.ram_label.setText(f"{used_txt}/{total_txt} ({ram_pct}% uso)")
            if result.get("storage"):
                used_b, total_b = result["storage"]
                storage_pct = round(used_b * 100 / total_b) if total_b else 0
                self.storage_usage_label.setText(f"{used_b / 1e9:.1f}GB/{total_b / 1e9:.1f}GB ({storage_pct}% uso)")
                self.storage_bar.setValue(storage_pct)
                self._set_usage_bar_color(self.storage_bar, storage_pct, inverse=False)
            if result.get("level") is not None:
                temp = f"{result['temp']:.1f}" if result.get("temp") is not None else "—"
                self.batt_label.setText(f"{result['level']}%")
                self.batt_bar.setValue(int(result['level']))
                self._set_usage_bar_color(self.batt_bar, result['level'], inverse=True)
                self.temp_label.setText(t("Temperatura da bateria") + f": {temp} °C")
        self.run_async(work, done)

    # ---------- aplicativos
    def refresh_apps_and_recommendations(self):
        """Atualiza apps e recomendações sob uma caixa modal de progresso."""
        if getattr(self, "_apps_loading", False) or getattr(self, "_recommendations_loading", False):
            return
        try:
            self.ensure_device()
        except Exception as e:
            QMessageBox.warning(self, t("Aviso"), str(e)); return
        self._refresh_waiting_info = True
        if hasattr(self, "apps_progress_wrap"): self.apps_progress_wrap.hide()
        # Diálogo informativo próprio: evita a barra nativa do QProgressDialog.
        self._refresh_dialog = QDialog(self)
        self._refresh_dialog.setWindowTitle(t("Atualizando aplicativos"))
        self._refresh_dialog.setWindowModality(Qt.ApplicationModal)
        self._refresh_dialog.setModal(True)
        dialog_layout = QVBoxLayout(self._refresh_dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 20)
        loading_label = QLabel(t("Carregando nomes e ícones…\nAguarde enquanto os aplicativos são atualizados."))
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setWordWrap(True)
        dialog_layout.addWidget(loading_label)
        self._refresh_dialog.setMinimumWidth(340)
        self._refresh_dialog.show()
        self.apps_refresh_btn.setEnabled(False)
        self.load_apps()
        self.scan_debloat()

    def _finish_refresh_dialog(self):
        self._refresh_waiting_info = False
        dlg = getattr(self, "_refresh_dialog", None)
        self._refresh_dialog = None
        if dlg is not None:
            dlg.close(); dlg.deleteLater()
        if hasattr(self, "apps_progress_wrap"): self.apps_progress_wrap.hide()
        if hasattr(self, "apps_refresh_btn"):
            self.apps_refresh_btn.setEnabled(not getattr(self, "_apps_loading", False))

    def _setup_pc_ram_indicator(self):
        self._pc_ram_label = QLabel("RAM do PC: —")
        self.statusBar().addPermanentWidget(self._pc_ram_label)
        self._pc_ram_timer = QTimer(self); self._pc_ram_timer.setInterval(2000)
        self._pc_ram_timer.timeout.connect(self._update_pc_ram_indicator)
        self._pc_ram_timer.start(); self._update_pc_ram_indicator()

    def _update_pc_ram_indicator(self):
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MEMORYSTATUSEX(); st.dwLength = ctypes.sizeof(st)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                pct = int(st.dwMemoryLoad); used = (st.ullTotalPhys-st.ullAvailPhys)/1024**3; total=st.ullTotalPhys/1024**3
                self._pc_ram_label.setText(f"RAM do PC: {pct}% ({used:.1f}/{total:.1f} GB)")
                return
        except Exception:
            pass
        try:
            import psutil
            m=psutil.virtual_memory(); self._pc_ram_label.setText(f"RAM do PC: {m.percent}% ({m.used/1024**3:.1f}/{m.total/1024**3:.1f} GB)")
        except Exception:
            self._pc_ram_label.setText("RAM do PC: —")

    def load_apps(self):
        if getattr(self, "_apps_loading", False):
            return
        try: self.ensure_device(); adb = self.adb()
        except Exception as e:
            self._finish_refresh_dialog(); QMessageBox.warning(self, t("Aviso"), str(e)); return
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
            self._finish_refresh_dialog()
            QMessageBox.critical(self, t("Erro"), error)
            return
        if rows is not None: self._last_rows = rows
        if not hasattr(self, "apps_table") or rows is None: return

        # Renderização em lotes: nunca cria milhares de itens numa única passagem
        # da thread gráfica. O cache mostra nomes/ícones imediatamente; metadados
        # ausentes são preenchidos depois pelo worker.
        self._app_rows, self._app_state = {}, {}
        self._label_cache = load_label_cache()
        self._recommendation_map = {row.get("pkg"): row for row in getattr(self, "_debloat_rows", []) if row.get("pkg")}
        self._apps_render_rows = list(rows)
        self._apps_render_index = 0
        self.apps_table.setSortingEnabled(False)
        self.apps_table.blockSignals(True)
        self.apps_table.setUpdatesEnabled(False)
        self.apps_table.setRowCount(len(rows))
        self._app_user = {r["pkg"]: r.get("user", False) for r in rows}
        for row in rows:
            if row.get("size") is not None:
                ent = self._label_cache.setdefault(row["pkg"], {})
                ent["size"] = row["size"]
                ent["path"] = row.get("path", "")
        self._render_apps_batch()

    def _render_apps_batch(self):
        if not hasattr(self, "apps_table"):
            return
        table = self.apps_table
        rows = self._apps_render_rows
        end = min(self._apps_render_index + 100, len(rows))
        palette = PALETTES["dark" if self.dark else "light"]
        for r in range(self._apps_render_index, end):
            row = rows[r]
            pkg, state, size = row["pkg"], row["state"], row["size"]
            cached = self._label_cache.get(pkg, {})
            label = cached.get("label") or KNOWN_NAMES.get(pkg, pkg)
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check.setData(Qt.UserRole, pkg); check.setData(Qt.UserRole + 1, False)
            check.setIcon(svg_icon("checkbox_outline", palette["text"], 18))
            check.setToolTip(t("Clique para selecionar este aplicativo"))
            icon_item = QTableWidgetItem(); icon_item.setTextAlignment(Qt.AlignCenter)
            icon_item.setIcon(self._app_icon(label, cached.get("icon")))
            name_item = QTableWidgetItem(label)
            name_item.setToolTip(f"{pkg}\n{t('Estado: {state}').format(state=t(state))}")
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
                table.setItem(r, c, item)
            self._app_rows[pkg] = (check, icon_item, name_item)
            self._app_state[pkg] = state

        self._apps_render_index = end
        if end < len(rows):
            # Permite à janela repintar e responder a cliques entre lotes.
            QTimer.singleShot(0, self._render_apps_batch)
            return

        self._save_timer.start(2000)
        table.setUpdatesEnabled(True)
        table.blockSignals(False)
        table.setSortingEnabled(True)
        self.filter_apps(); self._update_selection_hint()
        self.statusBar().showMessage(t("{n} aplicativos carregados").format(n=len(rows)), 5000)
        if not rows:
            self._finish_refresh_dialog()
        else:
            self.schedule_app_info(force=True)

    def _app_icon(self, label, icon_path=None) -> QIcon:
        if icon_path:
            try:
                path = Path(icon_path)
                if path.is_file():
                    candidate = QPixmap(str(path))
                    if not candidate.isNull():
                        if candidate.width() > 64 or candidate.height() > 64:
                            candidate = candidate.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
            return self._finish_refresh_dialog()
        try: adb = self.adb()
        except Exception: return self._finish_refresh_dialog()
        self._helper_busy = True
        if not getattr(self, "_refresh_waiting_info", False):
            self.apps_progress_wrap.show(); self.apps_progress.setRange(0, 0)
            self.apps_progress_label.setText(t("Exportando nomes e ícones pelo helper…"))
        else:
            self.apps_progress_wrap.hide()
        def done(result, error):
            self._helper_busy = False
            if error:
                # Helper instalado mas com erro: mostra o motivo real (não o aviso do aapt)
                self.apps_progress_wrap.hide(); self._finish_refresh_dialog()
                QMessageBox.warning(self, t("Aviso"), t("Não foi possível obter nomes e ícones pelo helper: {e}").format(e=error))
                return
            if result is None:
                # Helper não instalado: usa o modo antigo (precisa do aapt)
                self._helper_absent = self.device
                self.apps_progress_wrap.hide()
                # O fluxo atual não depende de aapt: mantém os pacotes listados e
                # usa o identificador como nome até o Helper ser instalado.
                # Mantém nomes conhecidos legíveis mesmo sem helper/aapt; os demais usam o pacote.
                for pkg in self._app_rows:
                    entry = self._label_cache.setdefault(pkg, {})
                    if not entry.get("label"):
                        entry["label"] = KNOWN_NAMES.get(pkg, pkg.rsplit(".", 1)[-1].replace("_", " ").title())
                    self._on_app_info(pkg, entry["label"], entry.get("icon", ""), 0, len(self._app_rows))
                self.statusBar().showMessage(t("Para nomes e ícones completos, instale ou abra o ManagerDroid Helper no Android."), 10000)
                self._finish_refresh_dialog()
                return
            entries, new_pkgs = result
            self._helper_device = self.device
            n = len(entries)
            missing_icons = False
            sorting = self.apps_table.isSortingEnabled()
            self.apps_table.setSortingEnabled(False)
            self.apps_table.setUpdatesEnabled(False)
            try:
                for i, (pkg, label, icon) in enumerate(entries, 1):
                    self._on_app_info(pkg, label, icon, i, n)
                    if pkg in new_pkgs and (not icon or not Path(icon).is_file()):
                        missing_icons = True
                        self._label_cache.setdefault(pkg, {})["v"] = 0
            finally:
                self.apps_table.setUpdatesEnabled(True)
                self.apps_table.setSortingEnabled(sorting)
            self.apps_progress_wrap.hide()
            self._finish_refresh_dialog()
            self.note(t("Nomes e ícones atualizados."))
        self.run_async(lambda: helper_export(adb), done)

    def _app_info_worker_finished(self):
        if hasattr(self, "apps_table"):
            self.apps_table.setSortingEnabled(bool(getattr(self, "_info_sorting_before", True)))
        if hasattr(self, "_progress_timer"):
            self._progress_timer.start(100)
        if getattr(self, "_refresh_waiting_info", False):
            self._finish_refresh_dialog()

    def _update_progress(self, visible_set=None):
        if not hasattr(self, "apps_progress_wrap"): return
        if getattr(self, "_refresh_waiting_info", False):
            self.apps_progress_wrap.hide()
            return
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
        for r in range(self.apps_table.rowCount()):
            name_item, pkg_item = self.apps_table.item(r, 2), self.apps_table.item(r, 3)
            if not name_item or not pkg_item: continue
            pkg = pkg_item.text()
            user = self._app_user.get(pkg, False)
            ok_text = not term or term in f"{name_item.text()} {pkg}".lower()
            ok_state = wanted is None or self._app_state.get(pkg) == wanted
            ok_type = typ == 0 or (typ == 1 and user) or (typ == 2 and not user)
            self.apps_table.setRowHidden(r, not (ok_text and ok_state and ok_type))
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
            # dumpsys inclui permissões solicitadas e concedidas. Extraímos os
            # identificadores completos, evitando mostrar blocos técnicos crus.
            found = set(re.findall(r"(?:android|com|org|net|[A-Za-z0-9_]+)\.[A-Za-z0-9_.]+\.[A-Z][A-Z0-9_]+", out))
            found = {p for p in found if "permission" in p.lower() or p.startswith("android.")}
            if not found:
                # Alguns fabricantes formatam a saída de forma diferente.
                found = set(re.findall(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+", out))
                found = {p for p in found if p.rsplit(".", 1)[-1].isupper() and "=" not in p}
            rows = []
            for permission in sorted(found, key=str.casefold):
                short = permission.rsplit(".", 1)[-1]
                # dumpsys pode informar granted=true/false na mesma linha ou perto.
                state = "Declarada"
                lines = out.splitlines()
                for i, line in enumerate(lines):
                    if permission in line:
                        context = " ".join(lines[i:i+3]).lower()
                        if "granted=true" in context or "granted: true" in context:
                            state = "Concedida"; break
                        if "granted=false" in context or "granted: false" in context:
                            state = "Não concedida"; break
                rows.append((short, describe_permission(permission), state))
            return rows
        def done(result, error):
            if error: QMessageBox.warning(self, t("Aviso"), error); return
            if not result:
                QMessageBox.information(self, t("Permissões"), t("Nenhuma permissão encontrada.")); return
            PermissionsDialog(self, f"{t('Permissões')} — {pkg}", result).exec()
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
    def show_change_history(self):
        path = CACHE_DIR / "change_history.jsonl"
        lines = []
        try:
            if path.exists():
                # Exibe somente as 300 ações mais recentes para evitar diálogo excessivo.
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-300:]
        except OSError as exc:
            QMessageBox.warning(self, t("Histórico"), str(exc)); return
        formatted = []
        for line in reversed(lines):
            try:
                row = json.loads(line)
                state = "OK" if row.get("success") else "FALHOU"
                formatted.append(f"[{row.get('timestamp','')}] {state} · {row.get('action','')} · {row.get('package','')}\n{row.get('details','')}")
            except (ValueError, TypeError):
                continue
        dialog = TextDialog(t("Histórico de alterações"), "\n\n".join(formatted) if formatted else t("Ainda não há alterações registradas."), self)
        dialog.exec()

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
        self.install_status.clear(); self.install_progress.setValue(0)
        self._install_cancel_event.clear(); self._install_running = True
        self.install_cancel_btn.setEnabled(True); self.install_go_btn.setEnabled(False)
        self._set_install_status("⟳  Iniciando instalação…")
        self.run_async(lambda: self._install_work([str(p) for p in paths], self.install_multi.isChecked(),
                                                   self._install_bridge.text.emit, self._install_cancel_event), self._install_done)

    def cancel_installation(self):
        if self._install_running:
            self._install_cancel_event.set()
            self._set_install_status("⏳  Solicitação de cancelamento enviada…")
            self.install_cancel_btn.setEnabled(False)

    def _set_install_status(self, text):
        # QPlainTextEdit keeps every status update instead of replacing the prior one.
        match = re.search(r"\((\d+)/(\d+)\)", text)
        if match and hasattr(self, "install_progress"):
            current, total = int(match.group(1)), max(1, int(match.group(2)))
            self.install_progress.setValue(int((current - 1) * 100 / total))
        elif text.startswith("✓") and hasattr(self, "install_progress"):
            # O evento de sucesso individual também é emitido após cada arquivo.
            self.install_progress.setValue(min(100, self.install_progress.value() + 1))
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
        self._install_running = False
        self.install_cancel_btn.setEnabled(False); self.install_go_btn.setEnabled(True)
        if not error: self.install_progress.setValue(100)
        if error:
            if "cancelada pelo usuário" in str(error).lower():
                self._set_install_status("✗  Instalação cancelada.")
                return
            self._set_install_status(f"✗  Falha na instalação: {error}")
            if is_connection_error(error):
                self._connection_lost()
            QMessageBox.critical(self, t("Erro na instalação"), str(error))
            return
        self._set_install_status("✓  Processo de instalação concluído!")
        # Mantém a confirmação visível por 5 segundos e limpa o status depois.
        QTimer.singleShot(5000, self._clear_install_status)
        if result:
            self.statusBar().showMessage(str(result).splitlines()[-1], 5000)

    def _clear_install_status(self):
        if not getattr(self, "_install_running", False) and hasattr(self, "install_status"):
            self.install_status.clear()
            self.install_progress.setValue(0)
            self.install_status.setStyleSheet("")

    def _install_work(self, path_strings, split, emit=None, cancel_event=None):
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
                if cancel_event is not None and cancel_event.is_set():
                    raise RuntimeError("Operação cancelada pelo usuário.")
                apk_name = group[0].name
                if emit:
                    emit(f"⟳  Instalando {apk_name}… ({idx}/{total})")
                if len(group) == 1 and not split:
                    out = check_install_output(run_command(adb + ["install", "-r", str(group[0])], 240, cancel_event=cancel_event))
                else:
                    out = check_install_output(run_command(adb + ["install-multiple", "-r"] + [str(x) for x in group], 300, cancel_event=cancel_event))
                installed.append(f"{apk_name}: {out or 'OK'}")
                record_change("install", apk_name, True, out or "OK")
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
        path, _ = QFileDialog.getSaveFileName(self, t("Salvar captura de tela"), str(Path.home() / "Pictures" / "ManagerDroid.png"), "PNG (*.png)")
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
            answer = QMessageBox.question(self, "scrcpy", t(
                "O scrcpy não está instalado.\n\nBaixar e instalar agora automaticamente (cerca de 10 MB, do site oficial do scrcpy)?"))
            if answer != QMessageBox.Yes: return
            self._install_tool(t("Baixando e instalando o scrcpy..."), install_scrcpy,
                           self._start_scrcpy); return
        self._start_scrcpy(tool)

    def _start_scrcpy(self, tool):
        try:
            # Usa o mesmo adb do ManagerDroid. Sem isso, o scrcpy pode pegar outro adb
            # (ex.: a variável de ambiente ADB apontando para uma pasta) e falhar ao iniciar o servidor.
            env = os.environ.copy()
            adb_tool = find_tool("adb")
            if adb_tool: env["ADB"] = adb_tool
            subprocess.Popen([tool, "-s", self.device], cwd=str(Path(tool).parent), env=env,
                             creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            self.statusBar().showMessage(t("scrcpy iniciado"), 4000)
        except Exception as e: QMessageBox.critical(self, "scrcpy", str(e))

    def _install_tool(self, label, install_fn, on_ok, on_fail_title="ManagerDroid"):
        """Executa a instalação em segundo plano com barra de progresso e chama on_ok(caminho)."""
        dlg = QProgressDialog(label, None, 0, 0, self)
        dlg.setWindowTitle(on_fail_title); dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(0); dlg.setAutoClose(False); dlg.setAutoReset(False)
        worker = ToolInstaller(install_fn); self.workers.append(worker)
        def on_progress(done, total):
            if total > 0:
                dlg.setRange(0, total); dlg.setValue(min(done, total))
        def ok(path):
            dlg.close(); on_ok(path)
        def fail(msg):
            dlg.close()
            QMessageBox.critical(self, on_fail_title, t("Falha ao instalar:") + "\n" + msg)
        worker.progress.connect(on_progress)
        worker.installed.connect(ok); worker.failed.connect(fail)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        dlg.show(); worker.start()

    def _startup_dialogs(self):
        if not SETTINGS.get("onboarding_done"):
            OnboardingDialog(self).exec()
            SETTINGS["onboarding_done"] = True
            save_settings(SETTINGS)
        self._offer_adb_install()

    def _offer_adb_install(self):
        if find_tool("adb"): return
        answer = QMessageBox.question(self, "ADB", t(
            "O ADB (Android Platform Tools) não foi encontrado.\n\n"
            "Baixar e instalar automaticamente na pasta 'adb' do ManagerDroid (cerca de 10 MB, do site oficial da Google)?"))
        if answer != QMessageBox.Yes:
            return
        self._install_tool(t("Baixando e instalando o ADB..."), install_adb,
                           lambda _path: self.refresh_devices(force=True), on_fail_title="ADB")

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
            self.dark = bool(SETTINGS.get("dark", True))
            self.apply_theme()
            global LANG
            new_lang = SETTINGS.get("lang", "pt")
            if new_lang != LANG:
                LANG = new_lang
                current = self.sidebar.currentRow() if hasattr(self, "sidebar") else 0
                self._build_ui(); self.sidebar.setCurrentRow(max(0, current)); self._restore_devices()
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
    window = ManagerDroid()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
