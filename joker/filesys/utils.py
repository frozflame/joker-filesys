#!/usr/bin/env python3
# coding: utf-8

import base64
import hashlib
import mimetypes
from typing import Generator, Union, Iterable


def read_as_chunks(path: str, length=-1, offset=0, chunksize=65536) \
        -> Generator[bytes, None, None]:
    if length == 0:
        return
    if length < 0:
        length = float('inf')
    chunksize = min(chunksize, length)
    with open(path, 'rb') as fin:
        fin.seek(offset)
        while chunksize:
            chunk = fin.read(chunksize)
            if not chunk:
                break
            yield chunk
            length -= chunksize
            chunksize = min(chunksize, length)


def compute_checksum(path_or_chunks: Union[str, Iterable[bytes]], algo='sha1'):
    hashobj = hashlib.new(algo) if isinstance(algo, str) else algo
    # path_or_chunks:str - a path
    if isinstance(path_or_chunks, str):
        chunks = read_as_chunks(path_or_chunks)
    else:
        chunks = path_or_chunks
    for chunk in chunks:
        hashobj.update(chunk)
    return hashobj


def checksum(path: str, algo='sha1', length=-1, offset=0):
    chunks = read_as_chunks(path, length=length, offset=offset)
    return compute_checksum(chunks, algo=algo)


def checksum_hexdigest(path: str, algo='sha1', length=-1, offset=0):
    hashobj = checksum(path, algo=algo, length=-1, offset=0)
    return hashobj.hexdigest()


def b64_encode_data_url(mediatype: str, content: bytes):
    b64 = base64.b64encode(content).decode('ascii')
    return 'data:{};base64,{}'.format(mediatype, b64)


def b64_encode_local_file(path: str):
    mediatype = mimetypes.guess_type(path)[0]
    with open(path, 'rb') as fin:
        return b64_encode_data_url(mediatype, fin.read())
