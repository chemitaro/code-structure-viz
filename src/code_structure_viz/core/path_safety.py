from __future__ import annotations

import os
import stat
from pathlib import Path


def lexical_absolute(path: Path) -> Path:
    """Return an absolute normalized spelling without resolving symlinks."""
    return Path(os.path.abspath(os.fspath(path)))


def has_symlink_component(path: Path) -> bool:
    """Report a symlink or unreadable component in an absolute lexical path."""
    absolute = lexical_absolute(path)
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        try:
            value = current.lstat()
        except FileNotFoundError:
            return False
        except OSError:
            return True
        if stat.S_ISLNK(value.st_mode):
            return True
    return False
