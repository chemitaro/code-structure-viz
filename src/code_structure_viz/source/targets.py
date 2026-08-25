from __future__ import annotations

import keyword
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class PathTarget:
    value: PurePosixPath


@dataclass(frozen=True, slots=True)
class ModuleTarget:
    value: str


@dataclass(frozen=True, slots=True)
class ClassTarget:
    raw: str


type TargetSpec = PathTarget | ModuleTarget | ClassTarget


def _valid_identifier_path(value: str) -> bool:
    parts = value.split(".")
    return bool(parts) and all(
        part and part.isidentifier() and not keyword.iskeyword(part) for part in parts
    )


def parse_target(raw: str) -> TargetSpec:
    """Parse one closed v1 path/module/class target."""
    if raw.count(":") != 1:
        raise ValueError("target must contain one kind prefix")
    kind, raw_value = raw.split(":", 1)
    value = unicodedata.normalize("NFC", raw_value)
    if not value:
        raise ValueError("target value cannot be empty")
    if kind == "path":
        path = PurePosixPath(value)
        if (
            "\\" in value
            or path.is_absolute()
            or value != path.as_posix()
            or any(part in {"", ".", ".."} for part in path.parts)
            or path.suffix != ".py"
        ):
            raise ValueError("path target is not a repository-relative Python path")
        return PathTarget(path)
    if kind == "module":
        if not _valid_identifier_path(value):
            raise ValueError("module target is not a dotted Python identifier")
        return ModuleTarget(value)
    if kind == "class":
        if not _valid_identifier_path(value) or "." not in value:
            raise ValueError("class target is not a dotted Python identifier")
        return ClassTarget(value)
    raise ValueError("target kind is not supported")


def target_kind_rank(value: TargetSpec) -> int:
    if isinstance(value, PathTarget):
        return 0
    if isinstance(value, ModuleTarget):
        return 1
    return 2


def target_value(value: TargetSpec) -> str:
    if isinstance(value, PathTarget):
        return value.value.as_posix()
    if isinstance(value, ModuleTarget):
        return value.value
    return value.raw


def target_sort_key(value: TargetSpec) -> tuple[int, bytes]:
    return target_kind_rank(value), target_value(value).encode("utf-8")
