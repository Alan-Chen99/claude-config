## Function Design

**Size varies.** Prefer 50-200 line functions for transforms. Short helpers
(5-15 lines) for focused utility. Extract helpers only when: (1) >=3 call sites,
(2) distinct testable concern, (3) independent concept. Don't extract just to
reduce line count.

**Early return.** Check-and-bail pattern.

**`ans` as return variable.** Functions that build a result name it `ans`.
Use `ans` when: loop body has >3 lines, conditional logic, or multiple append
paths. Use a comprehension when it's a single-expression transform.
```python
# ans builder — complex logic
def build_something():
    ans = []
    for x in items:
        if x.valid:
            ans.append(process(x))
    return ans

# comprehension — single expression
def collect_names():
    return [x.name for x in items if x.active]
```

**Walrus operator used heavily.** For isinstance chains, dict lookups, regex
matches — any "check and use" pattern:
```python
if i := instr.isinst(RawInstr):
    handle_raw(i)
elif i := instr.isinst(Comment):
    handle_comment(i)

if x := d.get(key):
    process(x)

if m := pat.match(line):
    handle_match(m)
```

**Tuple unpacking for destructuring.**
```python
(opt,) = instr.outputs_
(ipt,) = instr.inputs_
a, b = instr.inputs
(block,) = self.frag.blocks.values()
```

**Comprehensions for transformations.**
```python
args_ = [PtrArith.create(a) for a in args]
new_labels = {x.v: mk_internal_label(x.v.id) for x in index.labels.values()}
```

**Properties for O(1) computed values and validated extractions.** Methods for
anything involving I/O or O(n+) work.
```python
@property
def label(self) -> Label:
    (ans,) = self.label_instr.inputs_
    assert isinstance(ans, Label)
    return ans
```

**Positional-only params (`/`) for API functions.** Keyword-only (`*`) for
optional params.
```python
def if_(cond_: Bool, /) -> Iterator[None]:
def mk_internal_label(prefix: str, id: int | None = None, *, private: bool = True) -> Label:
```

**`_` as throwaway name for decorator side-effects:**
```python
@f.map_instrs
def _(instr: BoundInstr):
    handle_instr(instr, None)
```

**`@override` on EVERY overridden method, no exceptions.** Consistent throughout
class hierarchies.
