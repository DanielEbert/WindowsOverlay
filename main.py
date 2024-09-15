import time
import subprocess
import os
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class RestartOnModification(FileSystemEventHandler):
    def __init__(self, script_name):
        self.script_name = script_name
        self.process = None
        self.restart_script()

    def restart_script(self):
        if self.process:
            self.process.terminate()  # Terminate the current process
            self.process.wait()       # Wait for it to fully terminate
        self.process = subprocess.Popen([sys.executable, self.script_name])  # Restart the process

    def on_modified(self, event):
        if event.src_path.endswith(self.script_name):
            print(f'{self.script_name} modified, restarting script...')
            self.restart_script()

if __name__ == "__main__":
    script = 'screen_overlay.py'  # Your script to be monitored and restarted
    event_handler = RestartOnModification(script)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
