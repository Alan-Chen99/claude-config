## Naming Conventions

**Classes:** PascalCase. Short, abbreviated. Domain terms stay abbreviated.
- RIGHT: `Cfg`, `AuthSvc`, `TxnLog`, `ColIdx`, `FmtSpec`
- WRONG: `Configuration`, `AuthenticationService`, `TransactionLog`, `ColumnIndex`
- Internal/helper classes: leading underscore `_Place`, `_AttrProxy`, `_SubsProxy`

**Functions:** snake_case. Leading underscore for internal.
- Public: `can_cast_implicit`, `promote_types`, `format_val`, `read_uservalue`
- Internal: `_get_label`, `_get_type`, `_run_phases_once`, `_status_text`
- Shadowed builtins get trailing underscore: `break_`, `else_`, `if_`, `while_`, `yield_`, `return_`, `print_`, `range_`, `abs_`, `round_`, `min_`, `max_`

**Variables:** Short in tight scopes. `ans` is the universal name for "the thing
being built/returned."
- Single-letter in loops/comprehensions under ~15 lines where the mapping is
  unambiguous: `f` for Fragment/file, `b` for Block/buffer, `v` for Var/value,
  `r` for row, `n` for node, `k`/`v` for key/value
- `ctx` for context, `fn` for function, `typ` (not `type`) to avoid shadowing
- `ipt` for input, `opt` for output
- `i` as walrus-operator result: `if i := instr.isinst(RawInstr):`
- `ans` for the return value being constructed. Use `ans` when the loop body
  has >3 lines or conditional logic. Use a comprehension for single-expression
  transforms.

**Constants:** SCREAMING_SNAKE_CASE for true constants. Module-level mutable state
can use PascalCase or snake_case.
- `FRAG_OPTS`, `GLOBAL_FRAG_OPTS`, `FINAL_OPTS`
- Singleton constants lowercase: `nan`, `empty`, `db_internal`
- Cell-based globals: `SCOPE_STACK`, `_CUR_TRACE`

**Abbreviation policy:** Aggressive and consistent. If the domain uses it, code
uses it. Organized by domain:
- **Universal:** `ctx`, `fn`, `typ`, `val`, `msg`, `cfg`, `fmt`, `desc`, `impl`
- **Web:** `req`, `resp`, `auth`, `svc`, `repo`, `hdlr`
- **Data:** `df`, `col`, `agg`, `xform`, `src`, `dest`
