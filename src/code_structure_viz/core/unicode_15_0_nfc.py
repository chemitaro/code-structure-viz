"""Runtime implementation of the Issue #8 Unicode 15.0.0 NFC profile.

The checked-in compressed payload contains the complete frozen normalization
tables. This implementation never consults the host Unicode database and is
kept separate from the independent contract oracle at
tests/contracts/unicode_15_0_nfc.py.

UNICODE LICENSE V3

COPYRIGHT AND PERMISSION NOTICE

Copyright © 1991-2026 Unicode, Inc.

NOTICE TO USER: Carefully read the following legal agreement. BY
DOWNLOADING, INSTALLING, COPYING OR OTHERWISE USING DATA FILES, AND/OR
SOFTWARE, YOU UNEQUIVOCALLY ACCEPT, AND AGREE TO BE BOUND BY, ALL OF THE
TERMS AND CONDITIONS OF THIS AGREEMENT. IF YOU DO NOT AGREE, DO NOT
DOWNLOAD, INSTALL, COPY, DISTRIBUTE OR USE THE DATA FILES OR SOFTWARE.

Permission is hereby granted, free of charge, to any person obtaining a
copy of data files and any associated documentation (the "Data Files") or
software and any associated documentation (the "Software") to deal in the
Data Files or Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, and/or sell
copies of the Data Files or Software, and to permit persons to whom the
Data Files or Software are furnished to do so, provided that either (a)
this copyright and permission notice appear with all copies of the Data
Files or Software, or (b) this copyright and permission notice appear in
associated Documentation.

THE DATA FILES AND SOFTWARE ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF
THIRD PARTY RIGHTS.

IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS INCLUDED IN THIS NOTICE
BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL DAMAGES,
OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE DATA
FILES OR SOFTWARE.

Except as contained in this notice, the name of a copyright holder shall
not be used in advertising or otherwise to promote the sale, use or other
dealings in these Data Files or Software without prior written
authorization of the copyright holder.
"""

from __future__ import annotations

import base64
import hashlib
import json
import zlib

UNICODE_VERSION = "15.0.0"
PROFILE_ID = "unicode-15.0.0-nfc-v1"
ALGORITHM_VERSION = "unicode-nfc-15.0.0"
NFC_TABLE_DIGEST = "877b34f03bc09c193fb9014c381b3d3d980dea0676b942b4d54f56c1e11a6eb2"
FULL_SCALAR_KAT_DIGEST = "61f9ea3772b20f223112b3709361f387cde38bf0c5b7c329aeae49fd0d7de3d5"

# Base64(zlib(JSON)) stores the complete table without a runtime dependency.
# The source digests and documented generation rules make it reproducible.
_DATA_B64 = (
    "eNplfUuSJq2O5V7uOAc8BdRW0u4gHpmztmqzHpbdvTfSOZKIvyYRHIEjAQIJkPv3P//6+vr613/9z7+W7H/9V+vl"
    "100dT60SqRqpFqkeqRGpGSmJ1IpU8FjBYwePHTx28NjBYwePHTx28NjBYwePbTzaTR3l0ZR2aqRapHqkRjyhPKpo"
    "SiJ3RWpH6jC1S4mU8ihNUy1SPXJHpGakJFIrntiRCh41eNQaqRap4FGDRw0eNXjUFakdqeDRLo+q/yv/N/7v/D/4"
    "P2puUXOLmlvU3Hykdy+RqpFqkeqRGpGakZJIKY9hqR20kH5ED43ooRE8RvAYwWNEO0a0Y0TNI6SfIf2Mmmf0/Yy+"
    "n9H3M6SfQr3aM3poRg/N4CHGo2vKemhoqkWqR+4I2oyURO6K+qIdMad3zOkdc3rHnN4xp3fM6R1zesec3jGnd8zp"
    "HXO61mj6TUomVyZ3JuOxETp1k5LUlcmdyXysl3gsNOsmWyZ7Jm14miWTW09uPbn15NaT2yiZTG6jRWWjZ3JkMrmF"
    "ot3kymRyG8ltZttmcpvZNmieNQiqty05s8DlVpG6zGq11OVV8cxlVbumVPnqsJRO/WkpnfxiKZ3+y1K6ABgTVb56"
    "LCWRsgXMUtoe42bKZ9ygcpZSsY2bKZpxWzkKK/tF1cr4zWz1nD2TI5Mzk5LJlcmdyejjqS1n6srXq6UuL52xVWyp"
    "XZZS/ttSyv5YavBZ0aXWnhVdavnsZa1z8qYuZ52nNxWMpZVM+qJyky2TPQuMTM5MSiZXJnfWkNx6cuvJTdWua/ev"
    "WOFusmayZbJncmRyZlIyGXyXZL2S9UrWKzFhlmS9sYzV9E0qXBKUXVnZyspWVGaGs6v27pyzaRdqGoaalqHunLOw"
    "DaRKJlcW2Jk8kcyOTFtR01jUnR2Z5qKmvag7O3Kn9qbJqGkzKowGqNm9MBukJjdJbpLcxLldf2NlcmfyRDKU6CZr"
    "Jlsmeyad203OoMZC2MrKylZWtrKylZWtrGGlvCvlXSnvSnl3stjJYieLnSx2stjJYieLnfWerPdkvSfrPVFv7a4w"
    "N7kz6Qpz/0RlrdSktkz2TI4sOzMpmQx528x6Y0bfZMtkz2TWO2OE2pRMrkzuTGYrJLlJcpPkJslNkptkK1IRm2Qr"
    "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"
    "ancCZL0ezv73f/7z/wFVQ6MK"
)
_DATA_JSON = zlib.decompress(base64.b64decode("".join(_DATA_B64)))
if hashlib.sha256(_DATA_JSON).hexdigest() != NFC_TABLE_DIGEST:
    raise RuntimeError("Unicode 15.0.0 NFC table digest mismatch")
_DATA = json.loads(_DATA_JSON)
_DECOMPOSITION = {int(key): tuple(value) for key, value in _DATA["decomp"].items()}
_COMBINING_CLASS = {int(key): int(value) for key, value in _DATA["ccc"].items()}
_COMPOSITION = {
    tuple(int(part, 16) for part in key.split(",")): value
    for key, value in _DATA["compose"].items()
}

_SBASE = 0xAC00
_LBASE = 0x1100
_VBASE = 0x1161
_TBASE = 0x11A7
_LCOUNT = 19
_VCOUNT = 21
_TCOUNT = 28
_NCOUNT = _VCOUNT * _TCOUNT
_SCOUNT = _LCOUNT * _NCOUNT


def _hangul_decompose(codepoint: int) -> tuple[int, ...] | None:
    if not (_SBASE <= codepoint < _SBASE + _SCOUNT):
        return None
    offset = codepoint - _SBASE
    lead = _LBASE + offset // _NCOUNT
    vowel = _VBASE + (offset % _NCOUNT) // _TCOUNT
    trail = offset % _TCOUNT
    return (lead, vowel) if trail == 0 else (lead, vowel, _TBASE + trail)


def _decompose(codepoint: int, output: list[int]) -> None:
    hangul = _hangul_decompose(codepoint)
    if hangul is not None:
        for item in hangul:
            _decompose(item, output)
        return
    decomposition = _DECOMPOSITION.get(codepoint)
    if decomposition is None:
        output.append(codepoint)
        return
    for item in decomposition:
        _decompose(item, output)


def _ccc(codepoint: int) -> int:
    return _COMBINING_CLASS.get(codepoint, 0)


def _compose_pair(first: int, second: int) -> int | None:
    if _LBASE <= first < _LBASE + _LCOUNT and _VBASE <= second < _VBASE + _VCOUNT:
        return _SBASE + ((first - _LBASE) * _VCOUNT + (second - _VBASE)) * _TCOUNT
    if (
        _SBASE <= first < _SBASE + _SCOUNT
        and (first - _SBASE) % _TCOUNT == 0
        and _TBASE < second <= _TBASE + _TCOUNT - 1
    ):
        return first + second - _TBASE
    return _COMPOSITION.get((first, second))


def normalize_nfc(value: str) -> str:
    """Normalize *value* with the frozen Unicode 15.0.0 NFC profile."""

    if not isinstance(value, str):
        raise TypeError("NFC input must be str")
    if value.isascii():
        return value
    decomposed: list[int] = []
    for character in value:
        _decompose(ord(character), decomposed)

    # Canonical ordering (stable insertion sort) is intentionally explicit so
    # no host implementation can change the profile.
    ordered: list[int] = []
    for codepoint in decomposed:
        combining_class = _ccc(codepoint)
        if combining_class == 0:
            ordered.append(codepoint)
            continue
        position = len(ordered)
        while position > 0:
            previous_class = _ccc(ordered[position - 1])
            if previous_class == 0 or previous_class <= combining_class:
                break
            position -= 1
        ordered.insert(position, codepoint)

    composed: list[int] = []
    starter_index: int | None = None
    starter: int | None = None
    last_combining_class = 0
    for codepoint in ordered:
        combining_class = _ccc(codepoint)
        if starter is not None and (
            last_combining_class < combining_class or last_combining_class == 0
        ):
            replacement = _compose_pair(starter, codepoint)
            if replacement is not None:
                assert starter_index is not None
                composed[starter_index] = replacement
                starter = replacement
                continue
        if combining_class == 0:
            starter_index = len(composed)
            starter = codepoint
        composed.append(codepoint)
        last_combining_class = combining_class
    return "".join(chr(codepoint) for codepoint in composed)


def full_scalar_kat_digest() -> str:
    """Return the exhaustive frozen-profile scalar known-answer digest."""

    hasher = hashlib.sha256()
    for codepoint in range(0x110000):
        if 0xD800 <= codepoint <= 0xDFFF:
            continue
        encoded = normalize_nfc(chr(codepoint)).encode("utf-8")
        hasher.update(codepoint.to_bytes(4, "big"))
        hasher.update(len(encoded).to_bytes(4, "big"))
        hasher.update(encoded)
    return hasher.hexdigest()


def verify_full_scalar_kat() -> None:
    if full_scalar_kat_digest() != FULL_SCALAR_KAT_DIGEST:
        raise RuntimeError("Unicode 15.0.0 NFC scalar KAT mismatch")


UNICODE_NFC_PROFILE = {
    "profile_id": PROFILE_ID,
    "unicode_version": UNICODE_VERSION,
    "normalization": "NFC",
    "algorithm_version": ALGORITHM_VERSION,
    "table_digest": NFC_TABLE_DIGEST,
    "full_scalar_kat_digest": FULL_SCALAR_KAT_DIGEST,
}
