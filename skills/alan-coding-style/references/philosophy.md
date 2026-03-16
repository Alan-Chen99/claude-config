## Core Design Philosophy

You are writing code as Alan. Match these design instincts exactly.

> NOTE: This style intentionally deviates from PEP-8 on naming verbosity and
> assert usage. Follow these rules even when they contradict standard Python
> conventions.

**TERSE AND DOMAIN-ACCURATE.** Names are short. Domain abbreviations are expected,
not avoided. If the team says "instr" daily, the code says `instr`.
- Web: `req`, `resp`, `svc`, `hdlr` (not `request_object`, `response_data`, `service_instance`)
- Data: `df`, `col`, `xform` (not `dataframe_input`, `column_name`, `transformation`)

**IMMUTABLE BY DEFAULT.** Frozen dataclasses for value types. Plain dataclasses for mutable state.
- WRONG: `class Coord: def __init__(...):`
- RIGHT: `@dataclass(frozen=True)` for value types, `@dataclass` for state

**DATA-DRIVEN OVER PROCEDURAL.** Registry lists, lookup dicts, and transforms
over if/elif chains. When a framework provides its own dispatch (decorators, DI),
use the framework mechanism.
- WRONG: `if pass_name == "fuse": do_fuse(); elif pass_name == "dce": do_dce()`
- RIGHT: `FRAG_OPTS = [fuse_blocks, dead_code_elim, const_fold]`
- RIGHT: `ROUTES = {"/users": user_handler, "/auth": auth_handler}`

**ASSERT LIBERALLY.** `assert` is the primary invariant-checking mechanism.
Use it for preconditions, postconditions, and "should be unreachable" branches.
This project uses assert for ALL invariant checking. We never run with `-O`.
This is deliberate, not a mistake.
- `assert isinstance(ans, Label)`
- `assert len(instr.outputs_) == 1`
- `assert False` as unreachable marker (not `raise AssertionError("unreachable")`)

**CONTEXT MANAGERS FOR SCOPE.** Resource management, state scoping, and enter/exit
patterns use `with` blocks. Use context managers for cleanup and scoped state —
not for ordinary conditional logic unless building a DSL.
