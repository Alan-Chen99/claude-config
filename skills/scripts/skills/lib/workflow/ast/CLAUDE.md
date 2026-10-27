# ast/

AST for workflow XML output: build nodes, render them with `XMLRenderer`.

## Files

| File                   | What                                                                 | When to read                    |
| ---------------------- | -------------------------------------------------------------------- | ------------------------------- |
| `nodes.py`             | Node types: `TextNode`, `CodeNode`, `ElementNode` (built with `W.el()`), `FileContentNode`, and the step nodes `StepHeaderNode`, `CurrentActionNode`, `InvokeAfterNode`; the `Node` union | Understanding node structure; adding a node type |
| `builder.py`           | Immutable builder `W`: `W.el(tag, *children, **attrs)`, `.build()`, `.node()` | Constructing AST nodes |
| `renderer.py`          | `Renderer` protocol, `XMLRenderer`, `render()`, the standalone step-node renderers | Rendering AST to XML; adding a node type |
| `dispatch.py`          | Dispatch nodes with usage examples: `SubagentDispatchNode` (one agent), `TemplateDispatchNode` (one `$var` template over N targets), `RosterDispatchNode` (shared context, one task per agent) | Subagent orchestration patterns |
| `dispatch_renderer.py` | Render functions for the dispatch nodes                              | Rendering dispatch XML          |
| `__init__.py`          | Public API exports                                                   | Importing AST types             |

## Agent policy

- A new node type goes in the `Node` union, the `Renderer` protocol, `XMLRenderer` and the `match` in `_render_node`. That `match` has no default case: a node missing from it comes back as `None`, and `render()` then fails with a `TypeError` that does not name the node.
