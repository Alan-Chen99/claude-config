## Contrastive Examples

### Assert vs Try/Except for Invariants
WRONG:
```python
try:
    result = lookup[key]
except KeyError:
    raise RuntimeError(f"Key {key} not found")
```
RIGHT:
```python
assert key in lookup, f"{key} not found"
result = lookup[key]
```

### Walrus Check-and-Use Pattern
WRONG:
```python
val = d.get(key)
if val is not None:
    process(val)
```
RIGHT:
```python
if val := d.get(key):
    process(val)

if m := pat.match(line):
    handle_match(m)
```

### `ans` Builder vs Comprehension (both RIGHT in context)
RIGHT (complex logic — use `ans`):
```python
def collect():
    ans = []
    for x in items:
        if x.valid and x.score > threshold:
            ans.append(process(x))
    return ans
```
RIGHT (single expression — use comprehension):
```python
def collect_names():
    return [x.name for x in items if x.active]
```

### Property vs Method (cheap vs expensive)
RIGHT (O(1) — property):
```python
@property
def label(self) -> Label:
    return self._label
```
RIGHT (I/O or O(n) — method):
```python
def fetch_labels(self) -> list[Label]:
    return db.query(Label).filter_by(scope=self.id).all()
```

### Single-Letter Variable Scope
RIGHT (tight scope, unambiguous):
```python
names = [n.strip() for n in raw_names]
```
WRONG (wide scope, ambiguous):
```python
n = get_node()
# ... 40 lines later ...
process(n)  # what is n?
```

### Over-Abstraction vs Inline
WRONG:
```python
class HandlerFactory:
    def create(self, typ: str) -> Handler:
        return self._registry[typ]()
# ... used exactly once
```
RIGHT:
```python
handler = HANDLERS[typ]()
```

### Context Manager vs Manual Setup/Teardown
WRONG:
```python
scope = enter_scope()
try:
    do_work()
finally:
    exit_scope(scope)
```
RIGHT:
```python
with new_scope():
    do_work()
```

### Terse Error Messages vs Verbose
WRONG: `raise TypeError("Error: It is not possible to cast type1 to type2.")`
RIGHT: `raise TypeError(f"not possible to use {t1} as {t2}")`

### Dataclass vs NamedTuple
WRONG: `class Point(NamedTuple): x: int; y: int`
RIGHT: `@dataclass(frozen=True)` `class Point: x: int; y: int`

### PEP 695 Type Alias vs Old Style
WRONG: `Result = Union[Success, Failure]`
RIGHT: `type Result[T] = Success[T] | Failure`
