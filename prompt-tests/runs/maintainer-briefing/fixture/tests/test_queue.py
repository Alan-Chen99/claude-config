from parqueue import Queue


def test_put_then_drain(tmp_path):
    q = Queue(tmp_path / "q")
    q.put({"a": 1})
    q.put({"b": 2})
    assert q.drain() == [{"a": 1}, {"b": 2}] or q.drain() == [{"b": 2}, {"a": 1}]
    assert q.drain() == []
