import os
from pathlib import Path
import tempfile


def _atomic_write(path: Path, contents: str | bytes, *, default_mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else default_mode
    with tempfile.NamedTemporaryFile(
        mode="wb" if isinstance(contents, bytes) else "w",
        encoding=None if isinstance(contents, bytes) else "utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as temporary:
        if isinstance(contents, bytes):
            temporary.write(contents)
        else:
            temporary.write(contents)
        temporary_path = Path(temporary.name)
    try:
        temporary_path.chmod(mode)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, contents: str, *, default_mode: int = 0o644) -> None:
    _atomic_write(path, contents, default_mode=default_mode)


def atomic_write_bytes(path: Path, contents: bytes, *, default_mode: int = 0o644) -> None:
    _atomic_write(path, contents, default_mode=default_mode)
