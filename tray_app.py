"""RemitView — System tray application entry point.

Starts the FastAPI server in a background thread, opens the browser,
and shows a system tray icon with menu options.
"""
import sys
import os
import threading
import webbrowser
import time
import uvicorn

# Set up paths for PyInstaller
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

HOST = "127.0.0.1"
PORT = 8000


def start_server():
    """Start the uvicorn server in a thread."""
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        log_level="warning",
    )


def open_browser():
    """Open the browser after a short delay to let the server start."""
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    """Main entry point — starts server, opens browser, shows tray icon."""
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Open browser
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    try:
        # Try to use pystray for system tray icon
        import pystray
        from PIL import Image, ImageDraw

        def create_icon_image():
            """Create a simple tray icon."""
            img = Image.new('RGB', (64, 64), color=(13, 110, 253))
            draw = ImageDraw.Draw(img)
            draw.rectangle([8, 8, 56, 56], fill=(255, 255, 255))
            draw.text((16, 18), "RV", fill=(13, 110, 253))
            return img

        def on_open(icon, item):
            webbrowser.open(f"http://{HOST}:{PORT}")

        def on_quit(icon, item):
            icon.stop()
            os._exit(0)

        icon = pystray.Icon(
            "RemitView",
            create_icon_image(),
            "RemitView — EDI 835 Analyzer",
            menu=pystray.Menu(
                pystray.MenuItem("Open RemitView", on_open, default=True),
                pystray.MenuItem("Quit", on_quit),
            ),
        )
        icon.run()

    except ImportError:
        # pystray not available — just keep the server running
        print(f"RemitView running at http://{HOST}:{PORT}")
        print("Press Ctrl+C to stop")
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
            sys.exit(0)


if __name__ == "__main__":
    main()
