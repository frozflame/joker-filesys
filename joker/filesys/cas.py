#!/usr/bin/env python3
# coding: utf-8

import dataclasses
import hashlib
import shutil
from functools import cached_property
from os import PathLike
from pathlib import Path
from typing import Iterable
from uuid import uuid1

from joker.filesys import utils


@dataclasses.dataclass
class ContentAddressedStorage:
    base_dir: PathLike
    hash_algo: str = 'sha256'
    dir_depth: int = 2
    chunksize: int = 4096

    @cached_property
    def base_path(self) -> Path:
        if isinstance(self.base_dir, Path):
            return self.base_dir
        return Path(self.base_dir)

    def get_path(self, cid: str) -> Path:
        names = []
        for i in range(self.dir_depth):
            start = i * 2
            stop = start + 2
            names.append(cid[start: stop])
        names.append(cid)
        return self.base_path.joinpath(*names)

    def check_integrity(self, cid: str) -> bool:
        ho = hashlib.new(self.hash_algo)
        for chunk in self.load(cid):
            ho.update(chunk)
        return ho.hexdigest() == cid

    def guess_content_type(self, cid: str):
        with open(self.get_path(cid), 'rb') as fin:
            return utils.guess_content_type(fin.read(64))

    def exists(self, cid: str) -> bool:
        path = self.get_path(cid)
        return path.is_file()

    def delete(self, cid: str):
        path = self.get_path(cid)
        if path.is_file():
            path.unlink(missing_ok=True)

    def load(self, cid: str):
        path = self.get_path(cid)
        if not path.is_file():
            return
        with open(path, 'rb') as fin:
            chunk = fin.read(self.chunksize)
            while chunk:
                yield chunk
                chunk = fin.read(self.chunksize)

    def save(self, chunks: Iterable[bytes]):
        ho = hashlib.new(self.hash_algo)
        tmppath = self.base_path / str(uuid1())
        try:
            with open(tmppath, 'wb') as fout:
                for chunk in chunks:
                    ho.update(chunk)
                    fout.write(chunk)
            cid = ho.hexdigest()
            path = self.get_path(cid)
            path.parent.mkdir(parents=True, exist_ok=True)
            # ignore duplicating content file
            shutil.move(tmppath, path)
            ho = None
        finally:
            if ho is not None and tmppath.is_file():
                tmppath.unlink(missing_ok=True)
        return cid


__all__ = ['ContentAddressedStorage']
