#!/usr/bin/env python3
"""
Repeatable Windows Build & Packaging Script for SNIPLY.
Steps:
1. Regenerates icons, multi-size Windows .ico, and EN/RU translation dictionaries.
2. Runs the automated test suite (`unittest` / `pytest`) and aborts if any test fails.
3. Invokes PyInstaller using `installer/sniply.spec` to produce `dist/SNIPLY/SNIPLY.exe`.
4. Creates a portable ZIP archive (`dist/SNIPLY_v1.0.0_Windows_x64_Portable.zip`).
5. Optionally compiles the Inno Setup installer if `ISCC.exe` is installed on the host.
"""

from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
SPEC_FILE = PROJECT_ROOT / "installer" / "sniply.spec"
ISS_FILE = PROJECT_ROOT / "installer" / "sniply_setup.iss"


def run_step(description: str, cmd: list[str]) -> int:
    print(f"\n==> {description}")
    print("    $", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)
    return res.returncode


def main() -> int:
    print("============================================================")
    print(" SNIPLY v1.0.0 — Automated Build & Packaging Pipeline")
    print("============================================================")

    # 1. Generate assets & translations
    if run_step("Generating icons and logo assets", [sys.executable, "scripts/generate_assets.py"]) != 0:
        return 1
    if run_step("Generating EN/RU translations", [sys.executable, "scripts/generate_translations.py"]) != 0:
        return 1

    # 2. Run automated tests
    if run_step("Running automated test suite", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]) != 0:
        print("ERROR: Automated tests failed. Aborting build.")
        return 1

    # 3. Check PyInstaller availability and OS
    pyinstaller_bin = shutil.which("pyinstaller")
    if sys.platform != "win32" or not pyinstaller_bin:
        print("\n[INFO] Host environment is", sys.platform, "| PyInstaller:", pyinstaller_bin or "not installed")
        print("       Note: Native Windows .exe binaries must be built on Windows 10/11 (64-bit)")
        print("       with PyInstaller installed (`pip install -r requirements.txt`).")
        print("       All pre-build asset generation and automated tests succeeded!")
        return 0

    # 4. Run PyInstaller
    rc = run_step(
        "Building Windows executable via PyInstaller",
        [pyinstaller_bin, "--noconfirm", "--clean", str(SPEC_FILE)],
    )
    if rc != 0:
        print("ERROR: PyInstaller build failed.")
        return rc

    exe_path = DIST_DIR / "SNIPLY" / "SNIPLY.exe"
    if not exe_path.exists():
        print(f"ERROR: Expected executable not found at {exe_path}")
        return 1

    # 5. Package Portable ZIP
    portable_zip = DIST_DIR / "SNIPLY_v1.0.0_Windows_x64_Portable.zip"
    print(f"\n==> Creating portable ZIP archive: {portable_zip}")
    with zipfile.ZipFile(portable_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in (DIST_DIR / "SNIPLY").rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(DIST_DIR))

    # 6. Optional Inno Setup compilation
    iscc = shutil.which("ISCC") or r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if Path(iscc).exists():
        run_step("Compiling Windows Setup Wizard with Inno Setup", [str(iscc), str(ISS_FILE)])
    else:
        print("\n[INFO] Inno Setup (ISCC.exe) not found in PATH; skipping installer wizard compilation.")

    print("\nBuild completed! Output directory:", DIST_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
