"""AST node definitions for AIL v0.2."""
from dataclasses import dataclass, field
from typing import Any, List as PyList, Optional, Union


@dataclass(frozen=True)
class Number:
    value: float

    def __repr__(self):
        return f"Number({self.value!r})"


@dataclass(frozen=True)
class String:
    value: str

    def __repr__(self):
        return f"String({self.value!r})"


@dataclass(frozen=True)
class Var:
    name: str

    def __repr__(self):
        return f"Var({self.name!r})"


@dataclass(frozen=True)
class List:
    items: PyList[Any]

    def __repr__(self):
        return f"List({self.items!r})"


@dataclass(frozen=True)
class Field:
    key: str
    value: Any
    # True when the field was written bare, e.g. `flag` instead of `flag=true`
    bare: bool = False


@dataclass(frozen=True)
class Atom:
    name: str
    fields: PyList[Field] = field(default_factory=list)


@dataclass(frozen=True)
class Prefix:
    op: str  # one of '~', '?', '!'
    operand: Any


@dataclass(frozen=True)
class BinOp:
    op: str  # '+', '>>', '<<', '<>'
    left: Any
    right: Any


# Convenience alias
Node = Union[Atom, Prefix, BinOp, Number, String, Var, List]
