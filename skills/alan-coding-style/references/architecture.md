## Architecture Patterns

**Scoped state over globals.** Principle: make state lifetime explicit.
Implementation varies by domain:
- **Web/API:** framework DI (FastAPI `Depends`, Flask `g`, etc.)
- **CLI/scripts:** explicit parameter passing
- **Tree-walkers/compilers:** stack-based scoping via context managers

**Context manager pattern is pervasive.** Resource management, state scoping, and
enter/exit patterns use `with` blocks.

**Registry pattern for ordered pipelines.** Use ordered function lists for
sequential pipelines with 5+ stages. For <5 items, inline is fine.
```python
HANDLERS = [validate, transform, serialize, ...]
STAGES = [parse, analyze, optimize, emit, ...]
```
