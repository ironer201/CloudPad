"""Local file reading / writing with low-resource safeguards."""
import os

MAX_FILE_BYTES = 5 * 1024 * 1024     # 5 MB guard (like classic Notepad)


class FileManager:

    @staticmethod
    def read(path):
        """Return (text, encoding). Tries common encodings in order."""
        if os.path.getsize(path) > MAX_FILE_BYTES:
            raise ValueError("File is larger than 5 MB — not supported.")
        for enc in ("utf-8", "utf-16", "latin-1"):
            try:
                with open(path, "r", encoding=enc) as f:
                    return f.read(), enc
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ValueError("Unsupported text encoding.")

    @staticmethod
    def write(path, content):
        """Atomic save — a crash mid-write never destroys the original."""
        tmp = path + ".cloudpad.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)