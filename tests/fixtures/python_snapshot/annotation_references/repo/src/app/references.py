from typing import Generic, TypeVar

from external.models import External as Alias

T = TypeVar("T")


class Foo:
    pass


class Outer:
    class Inner:
        pass

    same: list[Foo]
    nested: Inner
    external: Alias
    missing: Missing


class Box(Generic[T]):
    pass
