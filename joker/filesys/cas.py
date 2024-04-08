#!/usr/bin/env python3
# coding: utf-8
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from joker.filesys import utils
from joker.filesys.utils import Pathlike, checksum_hexdigest


@dataclass
class ContentAddressedStorage:
    base_dirs: list[Path]
    hash_algo: str = "sha256"
    dir_depth: int = 2
    chunksize: int = 4096

    @classmethod
    def from_config(cls, cfg: dict | list[str]):
        if isinstance(cfg, list):
            return cls([Path(p) for p in cfg])
        return cls(**cfg)

    def locate(self, cid: str) -> Path | None:
        names = utils.spread_by_prefix(cid, self.dir_depth)
        for base_dir in self.base_dirs:
            path = base_dir.joinpath(*names)
            if path.is_file():
                return path

    def walk(self) -> Iterable[tuple]:
        for dir_ in self.base_dirs:
            yield from os.walk(dir_)

    def iter_paths(self) -> Iterable[str]:
        for dirpath, _, filenames in self.walk():
            for filename in filenames:
                yield os.path.join(dirpath, filename)

    def iter_cids(self) -> Iterable[str]:
        for triple in self.walk():
            yield from triple[2]

    def exists(self, cid: str) -> bool:
        return bool(self.locate(cid))

    def delete(self, cid: str):
        path = self.locate(cid)
        if path:
            path.unlink(missing_ok=True)

    def load(self, cid: str) -> Iterable[bytes]:
        path = self.locate(cid)
        if not path:
            return
        with open(path, "rb") as fin:
            chunk = fin.read(self.chunksize)
            while chunk:
                yield chunk
                chunk = fin.read(self.chunksize)

    def check_integrity(self, cid: str) -> bool:
        ho = hashlib.new(self.hash_algo)
        for chunk in self.load(cid):
            ho.update(chunk)
        return ho.hexdigest() == cid

    def _locate_new_file(self, cid: str) -> Path:
        names = utils.spread_by_prefix(cid, self.dir_depth)
        return self.base_dirs[0].joinpath(*names)

    def save(self, chunks: Iterable[bytes]) -> str:
        ho = hashlib.new(self.hash_algo)
        tmp = self.base_dirs[0] / utils.gen_unique_filename()
        try:
            with open(tmp, "wb") as fout:
                for chunk in chunks:
                    ho.update(chunk)
                    fout.write(chunk)
            cid = ho.hexdigest()
            utils.moves(tmp, self._locate_new_file(cid))
            ho = None
        finally:
            if ho is not None:
                tmp.unlink(missing_ok=True)
        return cid

    def seize(self, src_path: Pathlike) -> str:
        cid = checksum_hexdigest(src_path, self.hash_algo)
        utils.moves(src_path, self._locate_new_file(cid))
        return cid


__all__ = ["ContentAddressedStorage"]
