# dep

from typing import TypeVar

from streamlit.runtime.state.session_state_proxy import SessionStateProxy

from src.util.wrap import Mutable


# const

T = TypeVar('T')


# main

class SessionState:
    # constr

    def __init__(
            self,
            session_state: SessionStateProxy
    ) -> None:
        self.__state = session_state

    # prop

    @property
    def _state(self) -> SessionStateProxy:
        return self.__state

    # method

    def set[T](
            self,
            key: str,
            val: T
    ) -> Mutable[T]:
        self._state[key] = Mutable(val)
        return self._state[key]

    def get[T](
            self,
            key: str
    ) -> Mutable[T]:
        if key not in self._state:
            raise KeyError()
        return self._state[key]