from __future__ import annotations

import json
import math
import unicodedata
from collections.abc import Mapping, Sequence


def _normalize(value: object) -> object:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON does not support non-finite numbers")
        raise TypeError("canonical JSON contract does not support floats")
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            normalized[unicodedata.normalize("NFC", key)] = _normalize(item)
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [_normalize(item) for item in value]
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def _decimal_from_int(value: int) -> str:
    """Render an integer without routing it through CPython's digit limit."""
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    remaining = -value if value < 0 else value
    base = 10**9
    chunks: list[int] = []
    while remaining:
        remaining, chunk = divmod(remaining, base)
        chunks.append(chunk)
    return sign + str(chunks.pop()) + "".join(f"{chunk:09d}" for chunk in reversed(chunks))


def parse_json_integer(value: str) -> int:
    """Parse a JSON integer without CPython's decimal digit limit."""
    sign = -1 if value.startswith("-") else 1
    digits = value[1:] if sign < 0 else value
    parsed = 0
    for offset in range(0, len(digits), 9):
        chunk = digits[offset : offset + 9]
        parsed = parsed * (10 ** len(chunk)) + int(chunk, 10)
    return sign * parsed


def _encode_json(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return _decimal_from_int(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if isinstance(value, Mapping):
        items = ",".join(f"{_encode_json(key)}:{_encode_json(item)}" for key, item in value.items())
        return "{" + items + "}"
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return "[" + ",".join(_encode_json(item) for item in value) + "]"
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def encode_canonical_json(value: object, field_order: object | None = None) -> bytes:
    """Encode a closed DTO as deterministic UTF-8 JSON with one final LF.

    Object insertion order is the schema field order. ``field_order`` is accepted
    by the stable port but the closed constructors own ordering in v1.
    """
    del field_order
    normalized = _normalize(value)
    return (_encode_json(normalized) + "\n").encode("utf-8")
