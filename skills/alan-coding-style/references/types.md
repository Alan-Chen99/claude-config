## Type System Usage

**Union types:** `|` syntax exclusively. Never `Optional`, never `Union`.
- RIGHT: `Register | None`, `str | None`, `MVar | int`
- WRONG: `Optional[Register]`, `Union[str, None]`

**PEP 695 `type` aliases for complex unions.**
```python
type Const[T: VarT = VarT] = VirtualConst[T] | T
type Value[T: VarT = VarT] = Var[T] | VirtualConst[T] | T
type Float = VarRead[float] | float
type _CallableOr[T] = Callable[[], T] | T
```

**PEP 695 generics on classes and functions.**
```python
def mk_var[T: VarT](typ: type[T], ...) -> Var[T]:
class Cell[T]:
class VirtualConst[T: VarT = VarT](abc.ABC):
```

Older `Generic[T_co]` / `TypeVar` style also appears in existing code.

**Dataclass patterns:** `frozen=True` for value types. `eq=False` for
identity-based objects (paired with `ByIdMixin`). `kw_only=True` selectively.
```python
@dataclass(frozen=True)
class RegInfo: ...

@dataclass(frozen=True, eq=False)
class Var(Generic[T_co], ByIdMixin): ...

@dataclass(eq=False)
class Scope: ...

@dataclass
class Block: ...
```

**Protocols for structural typing.** `@runtime_checkable` when needed for
`isinstance` checks.
```python
@runtime_checkable
class EffectBase(Protocol):
    def known_distinct(self, other: Self) -> bool: ...

class UnpackPolicy(Protocol):
    def should_unpack(self, instr: BoundInstr, /) -> bool: ...
```

**`@overload` for type-safe API boundaries.** Multiple overloads for different
call signatures in public-facing code.

**`TYPE_CHECKING` for circular imports.**
```python
if TYPE_CHECKING:
    from ._api import UserValue
    from ._api import VarRead
```

Also used for conditional runtime behavior:
```python
if not TYPE_CHECKING:
    __getattr__ = _getattr
    __setattr__ = _setattr
```

**Lowercase builtins for generics:** `dict`, `list`, `tuple` -- never
`Dict`, `List`, `Tuple` from typing.
