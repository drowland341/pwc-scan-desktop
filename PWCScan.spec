# PyInstaller recipe for the Windows app. Build with:  build_windows.bat
# (or:  python -m PyInstaller --noconfirm --clean PWCScan.spec)
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("customtkinter")      # CustomTkinter's themes and fonts
datas += [("assets", "assets")]                   # icon and header logo
datas += [("channels", "channels")]               # built-in channel lists
datas += [("service_codes.json", ".")]            # descriptions for the Codes page

a = Analysis(
    ["pwc_scan.py"],
    datas=datas,
    hiddenimports=["serial.tools.list_ports", "serial.tools.list_ports_windows"],
    excludes=["matplotlib", "numpy", "pandas", "PIL"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PWCScan",
    icon="assets/icon.ico",
    console=False,          # no black console window behind the app
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, upx=False, name="PWCScan")
