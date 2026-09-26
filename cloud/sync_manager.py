"""Runs cloud calls in background threads.

Tkinter is NOT thread-safe: a worker must never touch a widget.
Results go into a queue.Queue; the UI thread drains it every 200 ms
(a timer tick costs ~0 CPU, even on a Celeron).
"""
import queue
import threading

POLL_MS = 200


class SyncManager:
    def __init__(self):
        self.queue = queue.Queue()

    def submit(self, op, func, *args):
        def worker():
            try:
                self.queue.put((op, "ok", func(*args)))
            except Exception as e:
                self.queue.put((op, "error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self, root, handler):
        """Call once at startup — delivers results onto the UI thread."""
        try:
            while True:
                op, status, result = self.queue.get_nowait()
                handler(op, status, result)
        except queue.Empty:
            pass
        root.after(POLL_MS, lambda: self.poll(root, handler))