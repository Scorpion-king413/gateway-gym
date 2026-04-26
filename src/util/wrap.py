# dep

from __future__ import annotations # fix class/staticmethod return type hints
from typing     import TypeVar

import os
import pandas as pd


# const

T = TypeVar('T')


# base

class Container[T]:
    def __init__(self, val: T):
        self._val: T = val

    @property
    def val(self) -> T:
        return self._val

class Mutable[T](Container[T]):
    def __init__(self, val: T) -> None:
        super().__init__(val)

    def set(self, new: T) -> T:
        self._val = new

class Savable[T](Mutable[T]):
    def save(self):
        pass


# df

class DFWrapper:
    # constr

    def __init__(
            self: DFWrapper,
            df:   pd.DataFrame,
            path: str,
            cols: list[str]
    ):
        self.df: pd.DataFrame = df
        self.__path = path
        self.__cols = cols

    # props

    @property
    def path(self) -> str:
        return self.__path

    @property
    def cols(self) -> list[str]:
        return self.__cols

    # method

    def save(
            self: DFWrapper
    ) -> None:
        self.df.to_csv(
            self.path, index=False
        )

    # static util

    @staticmethod
    def load(
            path:      str,
            cols:      list[str],
            write_new: bool = True
    ) -> DFWrapper:
        df = None # (not technically necessary but it feels safer)
        # pre-check for nonexistent or empty csv
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            df = pd.DataFrame(columns=cols) # new empty
        else:
            # try to load file
            try:
                df = pd.read_csv(path, dtype={"ID": str})
            except pd.errors.EmptyDataError:
                df = pd.DataFrame(columns=cols) # new empty
        # autosave
        dfw = DFWrapper(df, path, cols)
        if write_new:
            dfw.save()
        # return
        return dfw