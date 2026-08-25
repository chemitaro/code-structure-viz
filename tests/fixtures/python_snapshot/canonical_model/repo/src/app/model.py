from typing import Annotated, Literal


class Alpha:
    pass


class Beta:
    pass


class Modèle:
    value: Alpha
    value: Beta
    single: tuple[Alpha]
    pair: tuple[Alpha, Beta]
    union: Alpha | Beta | None
    literal: Literal["redacted", 1]
    annotated: Annotated[Alpha, "redacted"]
    unsupported: factory(Alpha)

    def duplicate(self, value: Alpha) -> None:
        pass

    def duplicate(self, value: Beta) -> None:
        pass

    def signature(
        self, a: Alpha, /, b: Beta = None, *items: Alpha, flag: bool, **meta: object
    ) -> None:
        pass
