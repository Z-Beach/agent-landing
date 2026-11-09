"""QR-GIF packet framing and Reed-Solomon erasure recovery.

Everything on the wire is binary. QR frames base45-encode the packet into
alphanumeric mode (no efficiency loss vs byte mode); grid frames carry the
packet bits directly.
"""
from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass

from reedsolo import RSCodec

DATA_MAGIC = b"QGD1"
MANIFEST_MAGIC = b"QGM1"
PARITY_MAGIC = b"QGP1"

# data: magic(4) session(8) index(u32) n_data(u16) file_size(u32)
#       digest8(8) crc32(u32) + chunk
DATA_HDR = struct.Struct(">4s8sIHI8sI")
# parity: magic(4) session(8) group(u16) k(u8) m(u8) slot(u8) length(u16) crc32(u32)
PARITY_HDR = struct.Struct(">4s8sHBBBHI")
# manifest: magic(4) session(8) n_data(u16) file_size(u32) digest(32) name_len(u16) + name
MANIFEST_HDR = struct.Struct(">4s8sHI32sH")

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
_B45 = {c: i for i, c in enumerate(ALPHABET)}


def b45encode(data: bytes) -> str:
    out = []
    i = 0
    while i + 1 < len(data):
        x = data[i] * 256 + data[i + 1]
        out.extend((ALPHABET[x % 45], ALPHABET[(x // 45) % 45], ALPHABET[x // 2025]))
        i += 2
    if i < len(data):
        x = data[i]
        out.extend((ALPHABET[x % 45], ALPHABET[x // 45]))
    return "".join(out)


def b45decode(text: str) -> bytes:
    out = bytearray()
    i = 0
    n = len(text)
    while i < n:
        rem = n - i
        if rem >= 3:
            x = _B45[text[i]] + _B45[text[i + 1]] * 45 + _B45[text[i + 2]] * 2025
            if x > 0xFFFF:
                raise ValueError("bad base45 triplet")
            out.extend((x >> 8, x & 0xFF))
            i += 3
        elif rem == 2:
            x = _B45[text[i]] + _B45[text[i + 1]] * 45
            if x > 0xFF:
                raise ValueError("bad base45 pair")
            out.append(x)
            i += 2
        else:
            raise ValueError("odd base45 tail")
    return bytes(out)


def chunk_layout(file_size: int, n_data: int) -> list[int]:
    """Deterministic chunk sizes so a receiver can derive them from headers."""
    if n_data <= 0:
        return []
    base, rem = divmod(file_size, n_data)
    return [base + 1 if i < rem else base for i in range(n_data)]


def split(data: bytes, chunk: int) -> list[bytes]:
    n = max(1, (len(data) + chunk - 1) // chunk)
    lens = chunk_layout(len(data), n)
    out, off = [], 0
    for L in lens:
        out.append(data[off:off + L])
        off += L
    return out


@dataclass(frozen=True)
class DataPacket:
    session: bytes
    index: int
    n_data: int
    file_size: int
    digest8: bytes
    chunk: bytes


@dataclass(frozen=True)
class ParityPacket:
    session: bytes
    group: int
    k: int
    m: int
    slot: int
    payload: bytes


def make_data(session: bytes, index: int, n_data: int, file_size: int,
              chunk: bytes, digest: bytes) -> bytes:
    crc = zlib.crc32(chunk) & 0xFFFFFFFF
    return DATA_HDR.pack(DATA_MAGIC, session, index, n_data, file_size,
                         digest[:8], crc) + chunk


def parse_data(raw: bytes) -> DataPacket | None:
    if len(raw) < DATA_HDR.size:
        return None
    (magic, session, index, n_data, file_size, digest8, crc) = \
        DATA_HDR.unpack(raw[:DATA_HDR.size])
    if magic != DATA_MAGIC or n_data < 1 or index >= n_data or file_size < 0:
        return None
    # transports may pad (the grid bit-packs to whole bytes): take the declared length
    expect = chunk_layout(file_size, n_data)[index]
    chunk = raw[DATA_HDR.size:DATA_HDR.size + expect]
    if len(chunk) != expect:
        return None
    if (zlib.crc32(chunk) & 0xFFFFFFFF) != crc:
        return None
    return DataPacket(session, index, n_data, file_size, digest8, chunk)


def make_parity(session: bytes, group: int, k: int, m: int, slot: int,
                payload: bytes) -> bytes:
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return PARITY_HDR.pack(PARITY_MAGIC, session, group, k, m, slot,
                           len(payload), crc) + payload


def parse_parity(raw: bytes) -> ParityPacket | None:
    if len(raw) < PARITY_HDR.size:
        return None
    magic, session, group, k, m, slot, length, crc = \
        PARITY_HDR.unpack(raw[:PARITY_HDR.size])
    if magic != PARITY_MAGIC or m < 1 or k < 1 or slot >= k + m:
        return None
    payload = raw[PARITY_HDR.size:PARITY_HDR.size + length]
    if len(payload) != length or (zlib.crc32(payload) & 0xFFFFFFFF) != crc:
        return None
    return ParityPacket(session, group, k, m, slot, payload)


def make_manifest(session: bytes, n_data: int, file_size: int, digest: bytes,
                  name: str) -> bytes:
    nb = name.encode("utf-8")[:255]
    return MANIFEST_HDR.pack(MANIFEST_MAGIC, session, n_data, file_size,
                             digest, len(nb)) + nb


def parse_manifest(raw: bytes):
    if not raw.startswith(MANIFEST_MAGIC) or len(raw) < MANIFEST_HDR.size:
        return None
    magic, session, n_data, file_size, digest, nlen = MANIFEST_HDR.unpack(raw[:MANIFEST_HDR.size])
    name = raw[MANIFEST_HDR.size:MANIFEST_HDR.size + nlen].decode("utf-8", "replace")
    return session, n_data, file_size, digest, name


def kind_of(raw: bytes) -> str | None:
    if raw.startswith(DATA_MAGIC):
        return "data"
    if raw.startswith(PARITY_MAGIC):
        return "parity"
    if raw.startswith(MANIFEST_MAGIC):
        return "manifest"
    return None


class Fec:
    """Systematic RS(n, k) applied column-wise across a group of packets."""

    def __init__(self, k: int, m: int):
        if k < 1 or m < 0 or k + m > 255:
            raise ValueError("need 1 <= k and k+m <= 255")
        self.k, self.m = k, m
        self._rs = RSCodec(m, nsize=k + m) if m else None

    def pad(self, rows: list[bytes]) -> list[bytes]:
        w = max((len(r) for r in rows), default=0)
        return [r + b"\x00" * (w - len(r)) for r in rows]

    def parity(self, group_rows: list[bytes]) -> list[bytes]:
        if self.m == 0:
            return []
        rows = self.pad(group_rows)
        if len(rows) < self.k:
            rows = rows + [b"\x00" * len(rows[0])] * (self.k - len(rows))
        w = len(rows[0])
        out = [bytearray(w) for _ in range(self.m)]
        for j in range(w):
            cw = self._rs.encode(bytes(r[j] for r in rows))
            for i in range(self.m):
                out[i][j] = cw[self.k + i]
        return [bytes(o) for o in out]

    def recover(self, have: dict[int, bytes], width: int) -> dict[int, bytes] | None:
        """have: {slot: padded_bytes}; slots >= k are parity. Returns missing data rows."""
        if self.m == 0 or not have:
            return None
        k, m = self.k, self.m
        present_data = [i for i in have if i < k]
        if len(present_data) + m < k:
            return None
        got: dict[int, bytearray] = {}
        for j in range(width):
            cw = bytearray(k + m)
            used = 0
            for slot, row in have.items():
                if slot < k + m and j < len(row):
                    cw[slot] = row[j]
                    used += 1
            if used == k + m:
                continue
            erasures = [i for i in range(k + m) if i not in have or j >= len(have[i])]
            if len(erasures) > m:
                return None
            try:
                fixed = self._rs.decode(bytes(cw), erase_pos=erasures, only_erasures=True)[0]
            except Exception:
                return None
            for i in range(k):
                if i not in have:
                    got.setdefault(i, bytearray(width))[j] = fixed[i]
        return {i: bytes(v) for i, v in got.items()}


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()
