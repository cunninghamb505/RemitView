"""Build script for creating the RemitView Windows executable."""
import subprocess
import sys
import os

def main():
    print("=" * 50)
    print("RemitView Windows Build")
    print("=" * 50)

    # Install build dependencies
    print("\n[1/3] Installing build dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "pyinstaller>=6.0.0", "pystray>=0.19.0", "Pillow>=10.0.0",
        "--quiet",
    ])

    # Install runtime dependencies
    print("[2/3] Installing runtime dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet",
    ])

    # Run PyInstaller
    print("[3/3] Building executable with PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "RemitView",
        "--onedir",
        "--noconsole",
        "--add-data", "frontend;frontend",
        "--add-data", "app;app",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "uvicorn.lifespan.off",
        "--hidden-import", "app.routers.files",
        "--hidden-import", "app.routers.claims",
        "--hidden-import", "app.routers.dashboard",
        "--hidden-import", "app.routers.codes",
        "--hidden-import", "app.routers.export",
        "--hidden-import", "app.routers.analytics",
        "--hidden-import", "app.routers.flags",
        "--hidden-import", "app.routers.settings",
        "--hidden-import", "app.routers.compare",
        "--hidden-import", "app.routers.api_keys",
        "--hidden-import", "app.routers.search",
        "--hidden-import", "pystray",
        "--hidden-import", "PIL",
        "--clean",
        "--noconfirm",
        "tray_app.py",
    ]

    # Add icon if it exists
    if os.path.exists("icon.ico"):
        cmd.extend(["--icon", "icon.ico"])

    subprocess.check_call(cmd)

    print("\n" + "=" * 50)
    print("Build complete!")
    print("Executable: dist/RemitView/RemitView.exe")
    print("=" * 50)


if __name__ == "__main__":
    main()
