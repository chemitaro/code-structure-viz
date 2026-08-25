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


def encode_canonical_json(value: object, field_order: object | None = None) -> bytes:
    """Encode a closed DTO as deterministic UTF-8 JSON with one final LF.

    Object insertion order is the schema field order. ``field_order`` is accepted
    by the stable port but the closed constructors own ordering in v1.
    """
    del field_order
    normalized = _normalize(value)
    return (
        json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")
