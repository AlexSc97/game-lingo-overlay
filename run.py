import os
import sys
import time
import webbrowser
import subprocess
import uvicorn
from threading import Thread

PORT = 8000
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}"

def open_window_mode():
    """
    Attempts to launch the overlay in lightweight borderless 'app-mode'
    using Edge or Chrome (native to Windows 10/11), falling back to default browser.
    """
    time.sleep(1.2) # Allow server to start

    # Try Microsoft Edge in standalone app window
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    # Try Google Chrome in standalone app window
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    for exe in edge_paths + chrome_paths:
        if os.path.exists(exe):
            try:
                subprocess.Popen([
                    exe,
                    f"--app={URL}",
                    "--window-size=1020,720",
                    "--window-position=450,150"
                ])
                print(f"[Launcher] Running overlay in standalone App Window ({os.path.basename(exe)})")
                return
            except Exception as e:
                print(f"[Launcher] Could not launch app mode: {e}")

    # Fallback to default browser
    print(f"[Launcher] Opening in default browser: {URL}")
    webbrowser.open(URL)

def main():
    print("=" * 65)
    print(" 🎮  GAME LINGO OVERLAY - Interactive English Screen Translator")
    print("     Tuned for Hollow Knight & Gaming Dialogue OCR")
    print("=" * 65)
    print(f" [*] Local Server: {URL}")
    print(" [*] Press SPACE to capture dialogue region")
    print(" [*] Press 'R' to toggle full sentence translation blur/reveal")
    print(" [*] Hover/Click words in the overlay to hear pronunciation & translation")
    print(" [*] Press Ctrl + C in this terminal to stop.")
    print("=" * 65)

    # Launch browser / app window in background thread
    launcher_thread = Thread(target=open_window_mode, daemon=True)
    launcher_thread.start()

    # Start FastAPI server
    uvicorn.run("backend.server:app", host=HOST, port=PORT, log_level="warning")

if __name__ == "__main__":
    main()
