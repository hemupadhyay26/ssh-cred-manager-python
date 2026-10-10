# Build on the target architecture; no credentials or .env are bundled.
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata
from pathlib import Path

root = Path(SPECPATH)
textual_data, textual_binaries, textual_imports = collect_all("textual")
a = Analysis(
    [str(root / "scripts/binary_entry.py")],
    pathex=[str(root)],
    binaries=textual_binaries,
    datas=textual_data + copy_metadata("ssh-cred-manager-python"),
    hiddenimports=textual_imports + collect_submodules("keyring.backends"),
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "ruff", "tests"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="ssc", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=True)
