# dep

from enum   import Enum
from typing import TypeVar

from streamlit.runtime.state import SessionStateProxy

from src.util.wrap  import DFWrapper, Mutable
from src.util.state import SessionState


# const

T = TypeVar('T')

class CsvFile(Enum):
    # inst

    ROSTER     = ( "res/roster.csv",     [ "ID", "Name"                        ], False )
    ATTENDANCE = ( "res/attendance.csv", [ "ID", "Name", "Action", "Timestamp" ], True  )
    HEALTH     = ( "res/health.csv",     [ "ID", "Health"                      ], False )

    # constr

    def __init__(self, path: str, cols: list[str], duplicates_allowed: bool):
        self.__path = path
        self.__cols = cols

    # props

    @property
    def key(self) -> str:
        return self.name.lower()

    @property
    def path(self) -> str:
        return self.__path

    @property
    def cols(self) -> list[str]:
        return self.__cols


# main

class SwipeData(
    SessionState
):
    # constr

    def __init__(
            self,
            session_state: SessionStateProxy
    ):
        super().__init__(session_state)
        self._roster     = self._set_csv(CsvFile.ROSTER    )
        self._attendance = self._set_csv(CsvFile.ATTENDANCE)
        self._health     = self._set_csv(CsvFile.HEALTH    )
        self._admin_auth = self.set(
            "admin_auth",
            False
        )

    # prop

    @property
    def roster(self) -> DFWrapper:
        return self._roster

    @property
    def attendance(self) -> DFWrapper:
        return self._attendance

    @property
    def health(self) -> DFWrapper:
        return self._health

    @property
    def admin_auth(self) -> Mutable:
        return self._admin_auth

    # prot util

    def _set_csv(self, csv: CsvFile) -> DFWrapper:
        return self.set(
            csv.key, DFWrapper.load(
                csv.path, csv.cols
            )
        ).val

    # util

    def get_last_action(self, student_id: str):
        logs = self.attendance.df[
            self.attendance.df["ID"] == student_id
        ]
        if logs.empty: return None
        return logs.iloc[-1]["Action"]