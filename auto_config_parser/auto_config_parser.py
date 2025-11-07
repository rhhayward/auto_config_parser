"""auto_config_parser.py

Implementation of `AutoConfigParser`, a subclass of ``configparser.ConfigParser``
that automatically reloads the INI file as soon as it changes on disk using the
``watchdog`` package. The watcher runs in a background thread managed by a
``watchdog.observers.Observer``.
"""
from __future__ import annotations

import threading
from pathlib import Path
import configparser
from typing import Any, Iterable, Mapping, Union

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

__all__ = ["AutoConfigParser"]


class _ConfigFileChangeHandler(FileSystemEventHandler):
    """Internal watchdog handler that triggers a reload on file modification."""

    def __init__(self, parser: "AutoConfigParser") -> None:
        self._parser = parser

    def on_modified(self, event):  # type: ignore[override]
        if (
            not event.is_directory
            and Path(event.src_path).resolve() == self._parser._file_path
        ):
            self._parser._reload_from_disk()


class AutoConfigParser(configparser.ConfigParser):
    """A drop-in replacement for ``configparser.ConfigParser`` with auto-reload.

    Parameters
    ----------
    path : Union[str, Path]
        Path to the INI configuration file.
    *args, **kwargs
        Additional positional and keyword arguments are forwarded to the
        ``configparser.ConfigParser`` constructor.
    """

    def __init__(self, path: Union[str, Path], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._file_path = Path(path).expanduser().resolve()
        if not self._file_path.exists():  # create empty file if missing
            try:
                self._file_path.touch()
            except Exception as e:
                pass

        self._lock = threading.RLock()

        # initial load
        self._reload_from_disk()

        # start watchdog observer
        self._observer = Observer()
        handler = _ConfigFileChangeHandler(self)
        self._observer.schedule(handler, self._file_path.parent.as_posix(), recursive=False)
        self._observer.daemon = True
        self._observer.start()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Stop the background watchdog observer thread."""
        with self._lock:
            if getattr(self, "_observer", None) is not None:
                self._observer.stop()
                self._observer.join(timeout=5)
                self._observer = None  # type: ignore[assignment]

    # context manager protocol -------------------------------------------------
    def __enter__(self):  # noqa: D401 (imperative mood not needed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # do not suppress exceptions

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _reload_from_disk(self) -> None:
        """Reload the configuration from disk in a thread-safe manner."""
        with self._lock:
            # Clear current data and re-read file.
            super().clear()
            super().read(self._file_path, encoding="utf-8")

    # ------------------------------------------------------------------
    # Overridden public API to ensure reads are up-to-date
    # ------------------------------------------------------------------
    # We override methods that *read* data to guarantee fresh view. Write
    # operations will internally update the file (if write is called) but chrono
    # isn't critical.
    def get(self, section: str, option: str, *args: Any, **kwargs: Any):  # type: ignore[override]
        self._reload_from_disk()
        return super().get(section, option, *args, **kwargs)

    # NOTE: We intentionally avoid overriding methods such as ``sections`` or
    # ``items`` that are internally used by ``configparser`` during mutation
    # operations (e.g., ``clear``). Overriding them to reload from disk can
    # cause infinite recursion, as seen in the failing test. Instead, the
    # background watchdog observer keeps the internal state in sync, and we
    # only proactively reload for ``get`` where the convenience outweighs the
    # risk.

    # ------------------------------------------------------------------
    # Write helpers remain unchanged but we ensure disk persistence
    # ------------------------------------------------------------------
    def write(self, fp, *args: Any, **kwargs: Any):  # type: ignore[override]
        """Write to a file-like object *and* persist to the configured path."""
        result = super().write(fp, *args, **kwargs)
        # After writing to external stream, save to internal file path as well.
        with open(self._file_path, "w", encoding="utf-8") as f:
            super().write(f)
        return result

    # Ensure cleanup on GC ------------------------------------------------------
    def __del__(self):  # noqa: D401 (imperative mood)
        try:
            self.close()
        except Exception:
            pass
