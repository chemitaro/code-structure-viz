from dataclasses import dataclass

from domain.base import Base


@dataclass
class Order(Base):
    identifier: int

    class State:
        pass

    def __init__(self, state: State) -> None:
        self.state: State = state

    @property
    def current_state(self) -> State:
        return self.state
