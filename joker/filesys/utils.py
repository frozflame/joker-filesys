#!/usr/bin/env python3
# coding: utf-8
from __future__ import annotations

import base64
import hashlib
import math
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Generator, Union, Iterable
from uuid import uuid4

Pathlike = Union[str, os.PathLike]
Filelike = Union[str, os.PathLike, Iterable[bytes]]

# for compatibility; will be removed in version 0.3.0
PathLike = Pathlike
FileLike = Filelike


def read_as_chunks(
    path: Pathlike, length=-1, offset=0, chunksize=65536
) -> Generator[bytes, None, None]:
    if length == 0:
        return
    if length < 0:
        length = float("inf")
    chunksize = min(chunksize, length)
    with open(path, "rb") as fin:
        fin.seek(offset)
        while chunksize:
            chunk = fin.read(chunksize)
            if not chunk:
                break
            yield chunk
            length -= chunksize
            chunksize = min(chunksize, length)


def compute_checksum(path_or_chunks: Filelike, algo="sha1"):
    hashobj = hashlib.new(algo) if isinstance(algo, str) else algo
    # path_or_chunks:str - a path
    if isinstance(path_or_chunks, str):
        chunks = read_as_chunks(path_or_chunks)
    else:
        chunks = path_or_chunks
    for chunk in chunks:
        hashobj.update(chunk)
    return hashobj


def checksum(path: Pathlike, algo="sha1", length=-1, offset=0):
    chunks = read_as_chunks(path, length=length, offset=offset)
    return compute_checksum(chunks, algo=algo)


def checksum_hexdigest(path: Pathlike, algo="sha1", length=-1, offset=0):
    hashobj = checksum(path, algo=algo, length=length, offset=offset)
    return hashobj.hexdigest()


def b32_sha1sum(path: Pathlike, length=-1, offset=0):
    hashobj = checksum(path, algo="sha1", length=length, offset=offset)
    return base64.b32encode(hashobj.digest()).upper().decode()


def b64_sha384sum(path: Pathlike, length=-1, offset=0):
    hashobj = checksum(path, algo="sha384", length=length, offset=offset)
    return base64.urlsafe_b64encode(hashobj.digest()).decode()


def b64_encode_data_url(mediatype: str, content: bytes) -> str:
    b64 = base64.b64encode(content).decode("ascii")
    return "data:{};base64,{}".format(mediatype, b64)


def b64_encode_local_file(path: Pathlike) -> str:
    mediatype = mimetypes.guess_type(path)[0]
    with open(path, "rb") as fin:
        return b64_encode_data_url(mediatype, fin.read())


def spread_by_prefix(filename: str, depth: int = 2, width: int = 2) -> list:
    names = []
    for i in range(depth):
        start = i * width
        stop = start + width
        part = filename[start:stop]
        if not part:
            break
        names.append(part)
    names.append(filename)
    return names


def compute_collision_probability(buckets: int, balls: int) -> float:
    x = -balls * (balls - 1) / 2.0 / buckets
    return 1.0 - math.exp(x)


def random_hex(length=24) -> str:
    size = sum(divmod(length, 2))
    bs = os.urandom(size)
    return bs.hex()[:length]


_prefix_and_content_type_pairs = [
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xFF\xD8\xFF", "image/jpeg"),
    (b"\x52\x61\x72\x21\x1A\x07", "application/x-rar-compressed"),
    (b"\x7F\x45\x4C\x46", "application/x-elf"),
    (b"\x51\x4C\x69\x74\x65\x20\x66\x6F\x72\x6D\x61\x74\x20\x33\x00", "sqlite3"),
    (b"\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A", "image/jpm"),
    (b"\x1F\x8B", "application/gzip"),
    (b"\x37\x7A\xBC\xAF\x27\x1C", "application/x-7z-compressed"),
    (b"\xFD\x37\x7A\x58\x5A\x00", "xz"),
    (b"\x4D\x53\x43\x46", "application/vnd.ms-cab-compressed"),
    (b"\x38\x42\x50\x53", "image/vnd.adobe.photoshop"),
    (b"\xFF\xFB", "audio/mpeg"),
    (b"\xFF\xF3", "audio/mpeg"),
    (b"\xFF\xF2", "audio/mpeg"),
    (b"\x49\x44\x33", "audio/mpeg"),
    (b"\x43\x44\x30\x30\x31", "iso"),
    (b"\x66\x4C\x61\x43", "flac"),
    (b"\x4D\x54\x68\x64", "audio/midi"),
]


def guess_content_type(content: bytes):
    # see also: python-magic (https://pypi.org/project/python-magic/)
    # see also: file (https://www.man7.org/linux/man-pages/man1/file.1.html)
    for prfix, content_type in _prefix_and_content_type_pairs:
        if content.startswith(prfix):
            return content_type


def gen_unique_filename(title: str = "tmp"):
    u = uuid4().bytes.hex().upper()
    return f"{title}.{u}.part"


def moves(old: Pathlike, new: Path):
    # old and new are possibly on different volumes
    # tmp and new are surely on the same volume
    new.parent.mkdir(parents=True, exist_ok=True)
    tmp = new.parent / gen_unique_filename(new.name)
    try:
        shutil.move(old, tmp)
        os.rename(tmp, new)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def saves(path: Pathlike, chunks: Iterable[bytes]):
    """
    Save content safely.
    Args:
        path: the file to be created or replaced
        chunks: iterable of chunks of content to be saved
    """
    if not isinstance(path, Path):
        path = Path(path)
    tmp = path.with_name(gen_unique_filename())
    with open(tmp, "wb") as fout:
        for chunk in chunks:
            fout.write(chunk)
    tmp.rename(path)


def find_regular_files(dirpath, **kwargs):
    for root, dirs, files in os.walk(dirpath, **kwargs):
        for name in files:
            path = os.path.join(root, name)
            if os.path.isfile(path):
                yield path


def infer_st_dev(path: Pathlike) -> int:
    while True:
        if os.path.exists(path):
            return os.stat(path).st_dev
        path = os.path.split(path)[0]
