"""Tests for the count-tokens local tokenizer backend.

The API backend is not exercised here: it needs a credential and a network
round-trip, so its failure modes are covered by the Rust integration tests in
`agent-tools/tests/count_tokens_test.rs` instead.
"""

import hashlib
import json
import subprocess
import sys
from importlib import resources
from pathlib import Path

import pytest

DATA = resources.files("claude_config") / "tokenizer_data"


def _run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "claude_config.count_tokens", *args],
        input=stdin if stdin is not None else "",
        capture_output=True,
        text=True,
    )


def test_vendored_tokenizer_matches_its_recorded_digest() -> None:
    provenance = json.loads((DATA / "PROVENANCE.json").read_text(encoding="utf-8"))
    blob = (DATA / provenance["file"]).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == provenance["sha256"]
    assert len(blob) == provenance["bytes"]


def test_provenance_records_a_pinned_upstream_revision() -> None:
    provenance = json.loads((DATA / "PROVENANCE.json").read_text(encoding="utf-8"))
    # A floating ref would let the vendored bytes and the recorded origin drift
    # apart silently, so the revision must be a full commit hash.
    assert len(provenance["revision"]) == 40
    assert set(provenance["revision"]) <= set("0123456789abcdef")
    assert provenance["source"].startswith("https://huggingface.co/")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("hello world", 2),
        ("The quick brown fox jumps over the lazy dog.", 10),
        ("机器学习", 1),
        ("def f(x):\n    return x + 1\n", 12),
    ],
)
def test_known_texts_have_pinned_counts(text: str, expected: int) -> None:
    """Pin counts so replacing the tokenizer file cannot pass unnoticed."""
    result = _run(text)
    assert result.returncode == 0, result.stderr
    assert int(result.stdout.strip()) == expected


def test_empty_input_counts_zero() -> None:
    """No BOS/EOS is added: the count is of the text and nothing else."""
    result = _run(stdin="")
    assert result.returncode == 0, result.stderr
    assert int(result.stdout.strip()) == 0


def test_local_backend_needs_no_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_TOKEN_COUNT_API_KEY", raising=False)
    result = _run("hello world")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "2"


def test_stdin_and_file_agree(tmp_path: Path) -> None:
    text = "The quick brown fox jumps over the lazy dog.\n" * 5
    target = tmp_path / "sample.txt"
    target.write_text(text, encoding="utf-8")

    from_file = _run("--file", str(target))
    from_stdin = _run(stdin=text)
    assert from_file.returncode == 0, from_file.stderr
    assert from_stdin.returncode == 0, from_stdin.stderr
    assert from_file.stdout == from_stdin.stdout


def test_model_without_api_is_rejected() -> None:
    result = _run("--model", "claude-opus-5", "hello")
    assert result.returncode != 0
    assert "--model applies to --api only" in result.stderr


def test_file_and_positional_are_mutually_exclusive(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("x", encoding="utf-8")
    result = _run("--file", str(target), "inline")
    assert result.returncode != 0
    assert "mutually exclusive" in result.stderr


def test_corrupted_tokenizer_fails_loudly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A swapped tokenizer must raise, not quietly report different numbers."""
    import claude_config

    package_root = Path(str(resources.files(claude_config)))
    staged = tmp_path / "claude_config"
    subprocess.run(["cp", "-r", str(package_root), str(staged)], check=True)

    provenance = json.loads(
        (staged / "tokenizer_data" / "PROVENANCE.json").read_text(encoding="utf-8")
    )
    victim = staged / "tokenizer_data" / provenance["file"]
    blob = bytearray(victim.read_bytes())
    blob[100] ^= 0x01
    victim.write_bytes(bytes(blob))

    result = subprocess.run(
        [sys.executable, "-m", "claude_config.count_tokens", "hello"],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(tmp_path)},
    )
    assert result.returncode != 0
    assert "does not match its recorded digest" in result.stderr
