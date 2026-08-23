You are a subagent. The parent agent is sweeping a symbol list and dispatched you
with one of them: where is `flush_buffer` called from?

Here is what you have — the output of `grep -rn "flush_buffer" .` run from the
repository root:

    core/buffer.py:88:    def flush_buffer(self) -> int:
    core/shutdown.py:31:            self.buf.flush_buffer()
    api/handlers.py:204:        if record.dirty: record.buf.flush_buffer()
    tests/test_buffer.py:12:    assert b.flush_buffer() == 3

The parent is filling in a table and has sent the rows finished so far:

    | symbol         | defined at          | callers |
    | -------------- | ------------------- | ------- |
    | StreamExporter | export/stream.py:12 | 4       |
    | RecordCache    | core/cache.py:40    | 0       |
    | drain_queue    | core/buffer.py:96   | 2       |

Return the `flush_buffer` row. The repository is not reachable from where you
are, so nothing further can be run.
