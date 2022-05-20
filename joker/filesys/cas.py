#!/usr/bin/env python3
# coding: utf-8
from __future__ import annotations

import hashlib
import os
import shutil
import warnings
from dataclasses import dataclass, field
from functools import cached_property
from os import PathLike
from pathlib import Path
from typing import Iterable
from uuid import uuid1

from joker.filesys import utils
from joker.filesys.utils import PathLike


@dataclass
class ContentAddressedStorage:
    base_dir: PathLike
    hash_algo: str = 'sha256'
    dir_depth: int = 2
    chunksize: int = 4096

    @cached_property
    def _base_path(self) -> Path:
        if isinstance(self.base_dir, Path):
            return self.base_dir
        return Path(self.base_dir)

    @cached_property
    def base_path(self) -> Path:
        msg = (
            "ContentAddressedStorage.base_path is deprecated, "
            "and will be remove in version 0.2.0."
        )
        warnings.warn(msg, DeprecationWarning)
        return self._base_path

    def get_path(self, cid: str) -> Path:
        msg = (
            "ContentAddressedStorage.get_path() is deprecated, "
            "and will be remove in version 0.2.0.; "
            "use ContentAddressedStorage.locate() instead."
        )
        warnings.warn(msg, DeprecationWarning)
        return self.locate(cid)

    def locate(self, cid: str) -> Path:
        names = utils.spread_by_prefix(cid, self.dir_depth)
        return self._base_path.joinpath(*names)

    def check_integrity(self, cid: str) -> bool:
        ho = hashlib.new(self.hash_algo)
        for chunk in self.load(cid):
            ho.update(chunk)
        return ho.hexdigest() == cid

    def guess_content_type(self, cid: str):
        with open(self.locate(cid), 'rb') as fin:
            return utils.guess_content_type(fin.read(64))

    def _walk(self) -> Iterable[tuple]:
        return os.walk(self._base_path)

    def _iter_paths(self) -> Iterable[str]:
        for dirpath, _, filenames in self._walk():
            for filename in filenames:
                yield os.path.join(dirpath, filename)

    def _iter_cids(self) -> Iterable[str]:
        for triple in self._walk():
            yield from triple[2]

    def exists(self, cid: str) -> bool:
        path = self.locate(cid)
        return path.is_file()

    def delete(self, cid: str):
        path = self.locate(cid)
        if path.is_file():
            path.unlink(missing_ok=True)

    def load(self, cid: str) -> Iterable[bytes]:
        path = self.locate(cid)
        if not path.is_file():
            return
        with open(path, 'rb') as fin:
            chunk = fin.read(self.chunksize)
            while chunk:
                yield chunk
                chunk = fin.read(self.chunksize)

    def admit(self, src: Path, cid: str):
        # src and path are possibly on the same volume
        path = self.locate(cid)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, path)

    def save(self, chunks: Iterable[bytes]) -> str:
        ho = hashlib.new(self.hash_algo)
        tmp = self._base_path / f'tmp.{uuid1()}'
        try:
            with open(tmp, 'wb') as fout:
                for chunk in chunks:
                    ho.update(chunk)
                    fout.write(chunk)
            cid = ho.hexdigest()
            self.admit(tmp, cid)
            ho = None
        finally:
            if ho is not None:
                tmp.unlink(missing_ok=True)
        return cid


@dataclass
class JointContentAddressedStorage(ContentAddressedStorage):
    extra_dirs: dict[str, PathLike] = field(default_factory=dict)

    def _walk(self) -> Iterable[tuple]:
        yield from os.walk(self.base_dir)
        for dir_ in self.extra_dirs.values():
            yield from os.walk(dir_)

    @cached_property
    def _prefix_lengths(self) -> list[int]:
        lengths = {len(prefix) for prefix in self.extra_dirs}
        lengths = list(lengths)
        lengths.sort(reverse=True)
        return lengths

    def _get_base_path(self, cid: str) -> Path:
        if not self.extra_dirs:
            return self._base_path
        for length in self._prefix_lengths:
            prefix = cid[:length]
            if prefix in self.extra_dirs:
                return Path(self.extra_dirs[prefix])
        return self._base_path

    def locate(self, cid: str) -> Path:
        base_path = self._get_base_path(cid)
        names = utils.spread_by_prefix(cid, self.dir_depth)
        return base_path.joinpath(*names)

    def admit(self, src: Path, cid: str):
        # src and path are possibly on different volumes
        # tmp and path are surely on the same volume
        path = self.locate(cid)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.parent / f'tmp.{cid}'
        try:
            shutil.move(src, tmp)
            shutil.move(tmp, path)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)


__all__ = ['ContentAddressedStorage', 'JointContentAddressedStorage']
