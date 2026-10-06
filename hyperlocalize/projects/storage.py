"""Media storage behind an interface (ADR 0004).

Files live outside the web root under random keys; user-supplied names are
never used in paths. Every stored file's SHA-256 is returned so callers can
record it. An S3-compatible implementation could replace LocalMediaStorage
without changing callers.
"""
import hashlib
import os
import shutil
import uuid
from pathlib import Path

from django.conf import settings


class MediaStorage:
    def save_file(self, src_path, suffix):
        raise NotImplementedError

    def save_bytes(self, data, suffix):
        raise NotImplementedError

    def open(self, key):
        raise NotImplementedError

    def local_path(self, key):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def quarantine(self, key):
        raise NotImplementedError

    def exists(self, key):
        raise NotImplementedError


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class LocalMediaStorage(MediaStorage):
    def __init__(self, root=None):
        self.root = Path(root or settings.HL_MEDIA_ROOT)

    def _ensure(self, path):
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _new_key(self, suffix):
        if not suffix.startswith(".") or "/" in suffix or len(suffix) > 10:
            raise ValueError("invalid suffix")
        token = uuid.uuid4().hex
        return f"{token[:2]}/{token}{suffix}"

    def _path(self, key):
        path = (self.root / "files" / key).resolve()
        if not str(path).startswith(str((self.root / "files").resolve()) + os.sep):
            raise ValueError("invalid media key")
        return path

    def save_file(self, src_path, suffix):
        key = self._new_key(suffix)
        dest = self._path(key)
        self._ensure(dest)
        shutil.copyfile(src_path, dest)
        os.chmod(dest, 0o600)
        return key, _sha256_file(dest)

    def save_bytes(self, data, suffix):
        key = self._new_key(suffix)
        dest = self._path(key)
        self._ensure(dest)
        with open(dest, "wb") as f:
            f.write(data)
        os.chmod(dest, 0o600)
        return key, hashlib.sha256(data).hexdigest()

    def new_path(self, suffix):
        """Reserve a key and return (key, path) for a tool such as ffmpeg to write into."""
        key = self._new_key(suffix)
        path = self._path(key)
        self._ensure(path)
        return key, path

    def finalise(self, key):
        """Return the SHA-256 of a file written via new_path()."""
        path = self._path(key)
        os.chmod(path, 0o600)
        return _sha256_file(path)

    def open(self, key):
        return open(self._path(key), "rb")

    def local_path(self, key):
        return self._path(key)

    def exists(self, key):
        return bool(key) and self._path(key).exists()

    def delete(self, key):
        if not key:
            return False
        path = self._path(key)
        if path.exists():
            path.unlink()
            return True
        quarantined = self.root / "quarantine" / key
        if quarantined.exists():
            quarantined.unlink()
            return True
        return False

    def quarantine(self, key):
        """Move a file out of the servable area until it is purged (ADR 0006)."""
        src = self._path(key)
        if not src.exists():
            return False
        dest = self.root / "quarantine" / key
        self._ensure(dest)
        src.replace(dest)
        return True


def get_storage():
    return LocalMediaStorage()
