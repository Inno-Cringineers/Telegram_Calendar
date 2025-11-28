"""Development script with hot reload using watchdog."""

import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver


class ReloadHandler(FileSystemEventHandler):
    """Handler for file system events that triggers reload."""

    def __init__(self, script_path: Path, restart_callback):
        """Initialize handler.

        Args:
            script_path: Path to the main script to run.
            restart_callback: Callback function to restart the process.
        """
        self.script_path = script_path
        self.restart_callback = restart_callback
        self.last_modified = time.time()
        self.debounce_seconds = 1.0

    def on_modified(self, event):
        """Handle file modification event."""
        if event.is_directory:
            return

        # Only watch Python files
        file_path = str(event.src_path)
        if not file_path.endswith(".py"):
            return

        # Debounce: ignore rapid successive changes
        current_time = time.time()
        if current_time - self.last_modified < self.debounce_seconds:
            return
        self.last_modified = current_time

        # Ignore changes to this file itself
        if event.src_path == str(self.script_path):
            return

        print(f"\nFile changed: {event.src_path}", flush=True)
        print("Restarting application...", flush=True)
        sys.stdout.flush()
        self.restart_callback()

    def on_created(self, event) -> None:
        """Handle file creation event."""
        # Treat file creation the same as modification for Python files
        if event.is_directory:
            return

        file_path = str(event.src_path)
        if not file_path.endswith(".py"):
            return

        # Debounce: ignore rapid successive changes
        current_time = time.time()
        if current_time - self.last_modified < self.debounce_seconds:
            return
        self.last_modified = current_time

        # Ignore changes to this file itself
        if file_path == str(self.script_path):
            return

        print(f"\nFile created: {file_path}", flush=True)
        print("Restarting application...", flush=True)
        sys.stdout.flush()
        self.restart_callback()


class HotReloadRunner:
    """Runner that monitors file changes and restarts the application."""

    def __init__(self, script_path: str = "main.py"):
        """Initialize runner.

        Args:
            script_path: Path to the main script to run.
        """
        self.script_path = Path(script_path)
        self.process: subprocess.Popen[bytes] | None = None
        self.observer: PollingObserver | None = None

    def start_process(self) -> None:
        """Start the application process."""
        if self.process is not None:
            self.stop_process()

        print(f"Starting: {self.script_path}", flush=True)
        sys.stdout.flush()
        # Type ignore needed because Popen type inference is complex
        self.process = subprocess.Popen(  # type: ignore[assignment]
            [sys.executable, str(self.script_path)],
            cwd=self.script_path.parent,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    def stop_process(self) -> None:
        """Stop the application process."""
        if self.process is not None:
            print("Stopping application...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Force killing process...")
                self.process.kill()
            self.process = None

    def restart_process(self) -> None:
        """Restart the application process."""
        self.stop_process()
        time.sleep(0.5)  # Small delay before restart
        self.start_process()

    def start_watcher(self) -> None:
        """Start file system watcher.

        Uses PollingObserver for better compatibility with Docker volumes,
        especially in WSL2 environments where inotify may not work properly.
        """
        watch_path = self.script_path.parent.resolve()
        event_handler = ReloadHandler(self.script_path, self.restart_process)

        # Use PollingObserver for better Docker/WSL2 compatibility
        self.observer = PollingObserver(timeout=1)
        self.observer.schedule(event_handler, str(watch_path), recursive=True)
        self.observer.start()
        print(f"Watching for changes in: {watch_path}", flush=True)
        print(f"Observer is alive: {self.observer.is_alive()}", flush=True)
        sys.stdout.flush()

    def stop_watcher(self) -> None:
        """Stop file system watcher."""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def run(self) -> None:
        """Run the application with hot reload."""
        try:
            self.start_process()
            self.start_watcher()

            print("\nHot reload enabled. Press Ctrl+C to stop.\n", flush=True)
            sys.stdout.flush()

            # Keep running until interrupted
            while True:
                if self.process is not None and self.process.poll() is not None:
                    # Process died, restart it
                    print("Process exited, restarting...")
                    self.restart_process()
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            self.stop_process()
            self.stop_watcher()
            print("Stopped")


if __name__ == "__main__":
    runner = HotReloadRunner("main.py")
    runner.run()
