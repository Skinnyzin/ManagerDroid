<p align="center">
  <img src="branding/managerdroid-logo.svg" alt="ManagerDroid" width="420">
</p>

# ManagerDroid

🇧🇷 [Português](README.md) · 🇺🇸 English

A Windows desktop manager for Android devices, written in Python (PySide6) on top of **ADB**. It lets you monitor the device, manage apps, remove system apps, mirror the screen and run everyday tools, with an interface in Portuguese or English.

> No root required. Works with USB debugging (or wireless ADB) enabled on the phone.

---

## Contents

- [Features](#features)
- [Screens](#screens)
- [Requirements](#requirements)
- [How to use](#how-to-use)
- [Android helper](#android-helper)
- [External tools](#external-tools)
- [Settings](#settings)
- [Building the executable](#building-the-executable)
- [Project structure](#project-structure)
- [Privacy and security](#privacy-and-security)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Features

### Device overview
- Model, brand (with a recognized logo), Android version, serial number and **security patch** (colored by age: green up to 6 months, amber up to 1 year, red beyond that).
- Real-time monitoring of **storage**, **RAM** and **battery** (level and temperature).
- RAM usage of the computer itself in the status bar.
- Configurable refresh interval.

### Applications
- List of all installed apps with **real names and icons**, package name, size and recommendation.
- Filters by text, state (enabled, disabled, uninstalled) and type (user or system).
- Actions on one or several apps at once:
  - uninstall, disable and re-enable;
  - force stop and open the app;
  - clear cache (of one app or all);
  - back up the APK and back up app data;
  - view granted permissions, with a plain-language description of each.
- History of the changes made by the program.
- Smart updates: names and icons are only downloaded when a new app appears. Later updates load the list almost instantly.

### Bloatware removal
- List of system apps with a **removal recommendation** and a description for each.
- Shortcuts to select the recommended ones or clear the selection.
- Confirmation before any removal.

### Tools
- **Screen mirroring** with scrcpy (installed automatically the first time).
- **Install APK** and split packages, with a progress bar and cancel option.
- **Send files** to the device.
- **Screenshot** saved to the computer.
- **Resolution and density** of the screen, with a restore-default option.
- **Reboot** the device, including recovery and bootloader modes.
- **Wireless connection** (ADB over Wi-Fi).
- **Interactive ADB shell**.

### Console
- Run **ADB** or **Fastboot** commands, with or without the prefix (`pm list packages` or `adb shell pm list packages`).
- Every command run is recorded in the log.

### Interface
- **Light** or **dark** theme, in blue tones.
- **Portuguese** or **English** language.
- Settings grouped in a single dialog.
- First-run guide explaining how to enable developer options and USB debugging.

---

## Screens

| Screen | What it does |
|---|---|
| **Overview** | Device data, storage, RAM and battery usage, and the phone silhouette with the brand |
| **Applications** | App list, filters and batch actions |
| **Tools** | Mirroring, installation, files, screen, reboot, Wi-Fi and shell |
| **Console** | ADB and Fastboot commands with a log |

---

## Requirements

- Windows 10 or 11 (64-bit or ARM64)
- Python 3.10 or later (only to run from source)
- Android device with **USB debugging** enabled (Settings → Developer options)
- USB cable (or wireless ADB, on Android 11 or later)

Python dependencies (`requirements.txt`):

```text
PySide6>=6.7,<7
psutil>=5.9
```

---

## How to use

1. Enable **USB debugging** on the phone and accept the debugging key prompt.
2. Open ManagerDroid. If ADB is not installed, the program offers to install it automatically.
3. Choose the device in the selector at the top of the window.
4. Use the side menu to switch between Overview, Applications, Tools and Console.

The first time the program opens, a guide explains how to enable developer options and USB debugging.

To run from source:

```powershell
py -m pip install -r requirements.txt
py main.py
```

---

## Android helper

To get real app names and icons quickly, ManagerDroid uses a small companion app on the device, **ManagerDroid Helper** (`com.managerdroid.help`).

- It only exports the data the computer needs, into `/sdcard/ManagerDroid`.
- It asks for **"All files access"** once, either on the helper screen or through ADB.
- If the helper is not installed, the program asks whether you want to install it. When you confirm, it downloads the APK from the project's GitHub and installs it. If installation fails, the APK is copied to the phone's **Download** folder (`ManagerDroid-Helper.apk`) so you can install it from the file manager.
- Without the helper, the program still works, but shows apps by package name (with known names for the main system apps) and without icons.

The helper's source code is in a separate folder of the project and can be compiled with Android Studio or Gradle.

---

## External tools

ManagerDroid does not ship third-party binaries. It looks for these tools and offers to install them automatically when they are missing:

| Tool | Source | Location |
|---|---|---|
| **ADB / Fastboot** (Android Platform Tools) | Google, `dl.google.com` | `adb\` folder |
| **scrcpy** | Genymobile project, GitHub | `tools\scrcpy\` folder |

The search order is: `platform-tools` folder, `adb` folder, `tools` folder, then the system `PATH`. The program always uses the same `adb` for itself and for scrcpy, avoiding version conflicts.

---

## Settings

Open **Settings** from the button at the top of the window. There are only two options:

- **Theme**: light or dark
- **Language**: Portuguese or English

---

## Building the executable

The `build.ps1` script generates a single executable with PyInstaller:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The result is `dist\ManagerDroid.exe`. The adb and scrcpy tools are downloaded on first use and kept in `%LOCALAPPDATA%\ManagerDroid\`.

---

## Project structure

```text
managerdroid/
├── main.py              # Entire application (interface and logic)
├── requirements.txt     # Python dependencies
├── build.ps1            # Build script (PyInstaller)
├── icone.ico            # Application icon
└── android_fallback.png # Default icon for apps without one
```

Files generated at runtime (do not commit):

- `adb\`, `tools\` and `dist\`: downloaded tools and the generated executable
- Cache, app index and settings: stored in the user data folder (`%LOCALAPPDATA%`)

---

## Privacy and security

- The program only talks to the connected device through ADB, and to the official tool sites when it installs them automatically.
- It does not send personal data to any server of its own.
- Destructive actions (uninstalling, removing system apps, rebooting into recovery) ask for confirmation first.
- Console commands are recorded in the log for auditing.

---

## Acknowledgements

- **ADB (Android Debug Bridge)**: command-line tool created by the Android team at Google and distributed in the [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools). ManagerDroid would not be able to talk to the device without it.
- **scrcpy**: created by Romain Vimont and maintained by [Genymobile](https://github.com/Genymobile/scrcpy), it displays and controls an Android device's screen from the computer. Its license and credits are in the [official repository](https://github.com/Genymobile/scrcpy).
- **Canta Debloater**: Created by samolego, this is a tool for removing unwanted apps from Android (https://github.com/samolego/Canta).
If it weren't for them, the program wouldn't have all these features (Thank you <3)

---

## License

This project is distributed under the [MIT License](LICENSE).

Third-party tools (Platform Tools, scrcpy, icons) keep their own licenses.
