# PWC Scan (desktop)

Windows app for live data, logging and fault codes on Kawasaki PWC ECUs over the KDS diagnostic port
(K-line, KWP2000). Python 3.9, CustomTkinter GUI, pyserial.

## Rules

- **Read-only diagnostics only.** Never add anything that writes to the ECU: no flashing, map or setting
  changes, actuator tests, or clearing codes (`14 ...` ClearDiagnosticInformation). Code reading always sends
  the fixed `READ_CODES_REQUEST`; don't let the GUI pass request bytes to it.
- **The USB cable path and Demo mode must keep working exactly as they do.** Don't change `KLine`, the
  `Engine` poll/scan/watch steps, `CsvLog` or the demo engine (`EngineSim`, `FakeECUSerial`) unless that is
  the task. New adapter types go alongside the existing serial path. The supported hardware is a USB OBD2
  cable with K-line support that shows up as a COM port; ELM327 adapters are not supported for now.
- **Stay Python 3.9 compatible.** Keep `from __future__ import annotations` in modules with `X | None` hints;
  no `match`, no 3.10+ stdlib APIs. The venv one folder up (`..\venv`) is 3.9: test with it.
- **`build_windows.bat`, `PWCScan.spec` and `installer.iss` must still build.** Files the frozen app reads
  at runtime must be listed in `PWCScan.spec` `datas`.
- **Never change the installer `AppId`** (`{6CE4B958-3306-438D-95FD-9C41288C079B}`): it's what lets a new
  version upgrade the installed one.
- **This repo is public; the phone apps are private.** The Android and iOS apps live in the private PWC Scan
  repo (local clone `C:\Users\rowla\PycharmProjects\kawasakiJetSkiDatalogger\pwc_scan_private`, with `android/`,
  `ios/` and `shared/`). `C:\Users\rowla\AndroidStudioProjects\PWCScan` is an older Android copy. Use them as a
  reference for features and findings: read them, never edit anything there. Reimplement behaviour in Python.
  Don't copy Kotlin or Swift code, comments, internal names, keys, or anything signing or app-store related
  into this repo.
- **Only use the name PWC Scan.** The app had a different name before it was open-sourced. That name must not
  appear anywhere in this repo: code, UI text, messages, docs, comments, file names or commit messages.
- Work on a branch, commit after each step, and run `python selftest.py` after each step.

## Layout

| File | What it is |
|---|---|
| `pwc_scan.py` | GUI: pages, channel editor, dialogs |
| `kline.py` | No GUI code: protocol, settings and channel files, dashboard limits, code parsing, `Engine` worker thread, demo ECU |
| `channels/kawasaki.json` | Built-in channels (same format as the phone apps', keep it interchangeable) |
| `service_codes.json` | Fault code descriptions for the Codes page |
| `selftest.py` | Checks against the demo ECU, no hardware needed |
| `PWCScan.spec`, `installer.iss`, `build_windows.bat` | Build: exe in `dist\PWCScan`, installer in `installer\` |

The GUI talks to `Engine` only through its two queues: `engine.send("cmd", ...)` runs `_cmd_<cmd>` on the
engine thread, and the engine's `emit(...)` events are handled in `App._drain_events`.

## Things to know

- **Channel defaults.** `kline.py` loads the built-in channels from `channels/kawasaki.json`. It's a copy of
  `shared/channels/kawasaki.json` in the private repo, which the phone apps use: fix scalings there and copy the
  file across, keeping `pids`, `defaults_revision` and `defaults_note` identical. When the defaults change in a
  way users should get, raise `defaults_revision` and say what changed in `defaults_note`: users whose own
  `pids.json` has an older revision are offered a reset once, and answering No keeps their edits. Don't raise
  it otherwise.
- **Dashboard limits** are `DASHBOARD_TACH` and `DASHBOARD_CARDS` in `kline.py`, in the channel's own units
  (C for temperatures), matched to channels by PID. They're kept out of the channel files so those stay the
  same as the phone apps'.
- **Fault codes.** A 2007 Ultra LX refuses the standard `18 00 FF 00`; it answers `13 01` with `53 <count>` and
  two bytes per code in the OBD-II layout (`03 40` = P0340). These are faults present now, not a history.
  `service_codes.json` links OBD-II codes to the dash's service codes; `obd_code_seen` marks links confirmed on
  a real ski. Never port the phone app's clear-codes logic (it tries other diagnostic sessions to erase codes).
- **Data folders.** Installed: settings and channels in `%APPDATA%\PWC Scan`, logs in `Documents\PWC Scan`.
  From source: next to the code (gitignored).
- **Releases.** Raise `APP_VERSION` in `pwc_scan.py` and `AppVersion` in `installer.iss`. Attach the
  installer to a GitHub Release renamed to `PWCScan-Setup.exe` (the README links to that name).
- **The developer's PC may have a real install** with real settings and logs in the folders above. Prefer
  testing from source; installing or running the built exe there uses (and can change) that real data.
