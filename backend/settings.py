"""Persistent settings + recent files, stored as one tiny JSON file."""
import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".cloudpad")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")


class Settings:
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.data = {"recent_files": []}
        self.load()

    def load(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (FileNotFoundError, ValueError):
            self.save()

    def save(self):
        """Atomic write: write .tmp then rename — never corrupts on HDD."""
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=1)
        os.replace(tmp, CONFIG_FILE)

    def add_recent(self, path):
        path = os.path.abspath(path)
        files = [p for p in self.data["recent_files"] if p != path]
        files.insert(0, path)
        self.data["recent_files"] = files[:10]        # cap keeps file tiny
        self.save()

    @property
    def recent_files(self):
        return self.data["recent_files"]

    def remove_recent_file(self, path):
        """Remove a path from the recent files list and persist."""
        if path in self.recent_files:
            self.recent_files.remove(path)
            self.save()   # or whatever your persist method is called