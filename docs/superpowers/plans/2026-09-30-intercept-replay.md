# Intercept Capture Completeness and `cc-replay` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the whole HTTP call in every intercept capture, and add `agent-tools cc-replay` so a captured request can be re-sent — faithfully, or with edits.

**Architecture:** `scripts/intercept/proxy.py` gains one `http` region per log entry (method, URL, request headers as ordered pairs, response status and headers) with credential-bearing headers reduced to a slot description. A new `src/claude_config/cc_replay/` package extracts a capture into an editable directory and sends it back, reusing the addon's own `parse_sse_stream` so a replay is comparable to what it replays. `cc-pretty-intercept` surfaces the new region.

**Tech Stack:** Python 3.14, mitmproxy 12 addon, httpx 0.28.1 (streaming client), pydantic v2 (capture schema), pytest, Rust/clap for the `agent-tools` subcommand.

**Spec:** `docs/superpowers/specs/2026-09-30-intercept-replay-design.md`

**Run tests with:** `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/$(basename $PWD) uv run pytest <path>`
Abbreviated below as `uv run pytest`; the environment variable is required every time.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `scripts/intercept/proxy.py` | **Modify.** Add `CREDENTIAL_HEADERS`, `split_credentials()`, `http_region()`; attach the region to both `write_log` calls. Stays standard-library only. |
| `src/claude_config/cc_pretty_intercept/parse.py` | **Modify.** Type the region: `Credential`, `HttpResponse`, `Http`, and `InterceptLog.http`. |
| `src/claude_config/cc_pretty_intercept/convert.py` | **Modify.** `header_lines()` gains `show_http`. |
| `src/claude_config/cc_pretty_intercept/main.py` | **Modify.** `--show-http` flag. |
| `src/claude_config/cc_replay/proxy_module.py` | **Create.** Loads the addon by path so the package can borrow `parse_sse_stream` without the addon importing anything. |
| `src/claude_config/cc_replay/extract.py` | **Create.** Capture → `request.json` + `http.json` + `meta.json`. Owns the synthesized-header fallback. |
| `src/claude_config/cc_replay/credentials.py` | **Create.** Host → credential source, each resolution naming itself. |
| `src/claude_config/cc_replay/send.py` | **Create.** Directory → HTTP call → `result-NNNN.json` + `.sse`. |
| `src/claude_config/cc_replay/main.py` | **Create.** argparse surface for `extract` and `send`. |
| `tests/test_intercept_proxy.py` | **Modify.** Header-capture tests; import the shared addon loader. |
| `tests/test_cc_pretty_intercept.py` | **Modify.** Render tests for the `http` region. |
| `tests/test_pretty_parity.py` | **Modify.** `INTERCEPT_ONLY` gains `--show-http`. |
| `tests/test_cc_replay.py` | **Create.** Extract/send round trip against a local origin. |
| `pyproject.toml` | **Modify.** `httpx` dependency, `cc-replay` script entry. |
| `agent-tools/src/main.rs` | **Modify.** `Cmd::CcReplay` and its dispatch arm. |
| `agent-tools/CLAUDE.md`, `scripts/intercept/README.md`, `scripts/CLAUDE.md`, `src/claude_config/CLAUDE.md`, `docs/CLAUDE.md` | **Modify.** Document the region, the subcommand, and correct the stale spec/plan counts. |

---

## Task 1: The proxy records the whole HTTP call

**Files:**
- Modify: `scripts/intercept/proxy.py` (add after `error_detail`, ~`:252`; wire into `response()` at `:407` and `:438`)
- Test: `tests/test_intercept_proxy.py`

- [ ] **Step 1: Let the test helper send arbitrary headers**

`_post_through_proxy` builds its request line by line and has no way to add a header. Give it one. Replace its signature and header block:

```python
def _post_through_proxy(
    proxy_port: int,
    origin_port: int,
    session_id: str,
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> list[tuple[float, bytes]]:
    """POST a conversation-shaped body and timestamp every arrival.

    The Host header is what the addon filters on (mitmproxy's
    Request.pretty_host prefers it over the destination address), so a local
    origin can stand in for api.anthropic.com without touching DNS.
    """
    body = json.dumps(
        {"model": "claude-stream-test", "messages": [{"role": "user", "content": "hi"}], "stream": True}
    ).encode()
    extra = "".join(f"{name}: {value}\r\n" for name, value in extra_headers)
    request = (
        f"POST http://127.0.0.1:{origin_port}/v1/messages?beta=true HTTP/1.1\r\n"
        f"Host: {proxy.TARGET_HOSTS[0]}\r\n"
        f"{proxy.SESSION_HEADER}: {session_id}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"{extra}"
        "Connection: close\r\n\r\n"
    ).encode() + body
```

The rest of the function is unchanged. Note the added `?beta=true` — the test now
exercises a query string, which is one of the things the region must keep.

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_intercept_proxy.py`:

```python
# --- The HTTP envelope ---
#
# anthropic-beta varies per request inside one session -- 8 entries measured on
# an auxiliary call against 14 on the main one, cc 2.1.269 -- so nothing else on
# disk implies it and a capture without it cannot be re-sent.


def _capture_with_headers(proxy_port, origin_port, home, headers):
    session_id = str(uuid.uuid4())
    _post_through_proxy(proxy_port, origin_port, session_id, headers)
    log_file = home / ".claude" / "requests-log" / session_id / "0001.json"
    deadline = time.monotonic() + 10
    while not log_file.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert log_file.exists(), f"no capture written to {log_file}"
    return json.loads(log_file.read_text())


BETAS = "claude-code-20250219,oauth-2025-04-20,effort-2025-11-24"


def test_the_beta_list_and_the_query_string_reach_the_capture(sse_origin, proxy_process) -> None:
    proxy_port, home = proxy_process
    entry = _capture_with_headers(
        proxy_port, sse_origin, home,
        (("anthropic-beta", BETAS), ("x-app", "cli"), ("anthropic-version", "2023-06-01")),
    )

    http = entry["http"]
    assert http["method"] == "POST"
    assert http["url"].endswith("/v1/messages?beta=true")
    sent = {name.lower(): value for name, value in http["request_headers"]}
    assert sent["anthropic-beta"] == BETAS
    assert sent["x-app"] == "cli"
    assert sent["anthropic-version"] == "2023-06-01"


def test_the_credential_becomes_a_slot_description_and_not_a_value(sse_origin, proxy_process) -> None:
    """94,820 captures sit unencrypted under $HOME; none needs the secret."""
    proxy_port, home = proxy_process
    entry = _capture_with_headers(
        proxy_port, sse_origin, home,
        (("Authorization", "Bearer sk-secret-token-value"), ("x-api-key", "also-secret")),
    )

    http = entry["http"]
    names = {name.lower() for name, _ in http["request_headers"]}
    assert "authorization" not in names
    assert "x-api-key" not in names
    assert http["credential"] == {
        "header": "Authorization", "scheme": "Bearer", "length": len("Bearer sk-secret-token-value"),
    }
    assert "sk-secret-token-value" not in json.dumps(entry)


def test_a_repeated_header_keeps_both_values_and_the_send_order(sse_origin, proxy_process) -> None:
    """dict() would join these with ", "; pairs keep them separable."""
    proxy_port, home = proxy_process
    entry = _capture_with_headers(
        proxy_port, sse_origin, home,
        (("X-Repeat", "first"), ("X-Repeat", "second")),
    )

    repeats = [v for name, v in entry["http"]["request_headers"] if name.lower() == "x-repeat"]
    assert repeats == ["first", "second"]


def test_a_successful_call_records_its_status_and_response_headers(sse_origin, proxy_process) -> None:
    """Only a non-200 recorded a status before; error.status was the sole record."""
    proxy_port, home = proxy_process
    entry = _capture_with_headers(proxy_port, sse_origin, home, ())

    assert entry["http"]["response"]["status"] == 200
    resp = {name.lower() for name, _ in entry["http"]["response"]["headers"]}
    assert "content-type" in resp


def test_a_refused_call_records_the_http_region_too(error_origin, proxy_process) -> None:
    proxy_port, home = proxy_process
    entry = _capture_with_headers(
        proxy_port, error_origin, home, (("anthropic-beta", BETAS),),
    )

    assert entry["http"]["response"]["status"] == 429
    assert entry["error"]["status"] == 429
    sent = {name.lower(): value for name, value in entry["http"]["request_headers"]}
    assert sent["anthropic-beta"] == BETAS
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_intercept_proxy.py -k "http_region or beta_list or credential_becomes or repeated_header or successful_call or refused_call_records" -v`
Expected: FAIL, `KeyError: 'http'` on each.

- [ ] **Step 4: Add the region builder to the addon**

Insert into `scripts/intercept/proxy.py` after `error_detail` (i.e. after the line `    return {"body": text[:ERROR_BODY_MAX]}`) and before `# --- Logging ---`:

```python
# --- The HTTP envelope ---

# Header names whose value is a credential. Dropped before an entry is built:
# the log tree sits unencrypted under $HOME, and nothing needs the secret to
# replay a call -- cc-replay resolves a fresh one at send time.
CREDENTIAL_HEADERS = frozenset(
    {"authorization", "x-api-key", "cookie", "proxy-authorization"}
)


def split_credentials(headers) -> tuple[list[list[str]], dict]:
    """Headers as sent, minus the secrets, plus the shape of the slot.

    Pairs rather than a mapping: `Headers.items(multi=True)` keeps a repeated
    header and the order it was sent in, where `dict()` joins duplicates with
    ", " and loses both.

    The slot -- which header, which scheme, how many characters -- is what
    tells a reader an OAuth bearer from an API key, and a replay where to put
    the credential it resolves. The value itself is never written.
    """
    kept: list[list[str]] = []
    credential: dict = {}
    for name, value in headers.items(multi=True):
        if name.lower() in CREDENTIAL_HEADERS:
            if not credential:
                scheme = value.split(" ", 1)[0] if " " in value else ""
                credential = {"header": name, "scheme": scheme, "length": len(value)}
            continue
        kept.append([name, value])
    return kept, credential


def http_region(flow) -> dict:
    """The call itself: everything about it the body cannot say.

    `anthropic-beta` varies per request inside one session -- 8 entries measured
    on an auxiliary call against 14 on the main one -- so no sibling capture,
    model id or client version implies it. Without this region a capture is a
    conversation, and a conversation cannot be put back on the wire.
    """
    request_headers, credential = split_credentials(flow.request.headers)
    region: dict = {
        "method": flow.request.method,
        "url": flow.request.pretty_url,
        "http_version": flow.request.http_version,
        "request_headers": request_headers,
    }
    if credential:
        region["credential"] = credential
    if flow.response is not None:
        region["response"] = {
            "status": flow.response.status_code,
            "reason": flow.response.reason,
            "headers": [[k, v] for k, v in flow.response.headers.items(multi=True)],
        }
    return region
```

- [ ] **Step 5: Attach it to both log entries**

In `response()`, the non-200 branch currently reads:

```python
            write_log(
                {
                    "timestamp": timestamp,
                    "duration_ms": duration_ms,
                    **({"session": session_meta} if session_meta else {}),
                    "streaming": streaming,
                    "error": {
```

Insert `"http": http_region(flow),` directly after the `"streaming": streaming,` line.

The success branch reads:

```python
        write_log(
            {
                "timestamp": timestamp,
                "duration_ms": duration_ms,
                **({"session": session_meta} if session_meta else {}),
                "streaming": streaming,
                "request": body,
                "response": parsed,
            },
            session_id,
        )
```

Insert `"http": http_region(flow),` directly after its `"streaming": streaming,` line too.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_intercept_proxy.py -v`
Expected: PASS, every test in the file including the pre-existing streaming and refusal tests.

- [ ] **Step 7: Commit**

```bash
git add scripts/intercept/proxy.py tests/test_intercept_proxy.py
git commit -m "$(cat <<'MSG'
intercept: the capture records the call, not only the body

proxy.py read flow.request.get_content() and the session id header and nothing
else, so method, URL, every other header and the response's status were absent
from every capture. anthropic-beta varies per request inside one session --
8 entries on an auxiliary call against 14 on the main one, cc 2.1.269 -- so the
one input that most changes what the API does was the one nothing recorded.

Headers are stored as ordered [name, value] pairs because Headers.items(multi=True)
keeps a repeated header where dict() joins duplicates with ", ".

Credential-bearing headers are dropped and reduced to {header, scheme, length}:
enough to tell an OAuth bearer from an API key and to know where a replay puts
its own, with no secret on disk.

Claude-Session: d01082f1-9b11-4484-9620-f1923a66d187
MSG
)"
```

---

## Task 2: The capture schema types the region

**Files:**
- Modify: `src/claude_config/cc_pretty_intercept/parse.py`
- Test: `tests/test_cc_pretty_intercept.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cc_pretty_intercept.py`:

```python
# ── The http region ─────────────────────────────────────────────────────────

HTTP = {
    "method": "POST",
    "url": "https://api.anthropic.com/v1/messages?beta=true",
    "http_version": "HTTP/1.1",
    "request_headers": [
        ["anthropic-beta", "claude-code-20250219,effort-2025-11-24"],
        ["x-app", "cli"],
    ],
    "credential": {"header": "Authorization", "scheme": "Bearer", "length": 115},
    "response": {
        "status": 200,
        "reason": "OK",
        "headers": [["request-id", "req_011CfYdgBnuh"], ["anthropic-ratelimit-unified-5h-utilization", "0.11"]],
    },
}


def test_a_capture_without_an_http_region_still_loads(tmp_path) -> None:
    """94,820 captures predate the region; absence is normal, not an error."""
    from claude_config.cc_pretty_intercept.parse import load_intercept

    path = tmp_path / "0001.json"
    path.write_text(json.dumps(capture()))
    assert load_intercept(str(path)).http is None


def test_the_http_region_is_typed_and_reachable_by_header_name(tmp_path) -> None:
    from claude_config.cc_pretty_intercept.parse import load_intercept

    path = tmp_path / "0001.json"
    path.write_text(json.dumps(capture(http=HTTP)))
    log = load_intercept(str(path))

    assert log.http is not None
    assert log.http.method == "POST"
    assert log.http.header("Anthropic-Beta") == "claude-code-20250219,effort-2025-11-24"
    assert log.http.header("absent") == ""
    assert log.http.response_header("Request-Id") == "req_011CfYdgBnuh"
    assert log.http.credential is not None
    assert log.http.credential.length == 115
    assert log.http.response is not None
    assert log.http.response.status == 200
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cc_pretty_intercept.py -k "http_region_is_typed or without_an_http_region" -v`
Expected: FAIL, `AttributeError: 'InterceptLog' object has no attribute 'http'`.

- [ ] **Step 3: Add the models**

In `src/claude_config/cc_pretty_intercept/parse.py`, insert after the `TransportError` class and before `InterceptLog`:

```python
class Credential(_Base):
    """The credential slot, never its value — proxy.py drops the secret.

    `length` and `scheme` are what separate an OAuth bearer from an API key
    without recording either.
    """
    header: str = ""
    scheme: str = ""
    length: int = 0


class HttpResponse(_Base):
    status: int = 0
    reason: str = ""
    # Ordered pairs: a repeated header stays separable and send order survives.
    headers: list[list[str]] = []


class Http(_Base):
    """The HTTP call around the body.

    Absent from any capture written before the proxy recorded it, so every
    reader treats it as optional rather than as an empty header set.
    """
    method: str = ""
    url: str = ""
    http_version: str = ""
    request_headers: list[list[str]] = []
    credential: Credential | None = None
    response: HttpResponse | None = None

    def header(self, name: str) -> str:
        """First value for a request header, case-insensitively; "" if absent."""
        wanted = name.lower()
        for key, value in self.request_headers:
            if key.lower() == wanted:
                return value
        return ""

    def response_header(self, name: str) -> str:
        """First value for a response header, case-insensitively; "" if absent."""
        wanted = name.lower()
        for key, value in self.response.headers if self.response else []:
            if key.lower() == wanted:
                return value
        return ""
```

Then add the field to `InterceptLog`, after `error`:

```python
    http: Http | None = None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_cc_pretty_intercept.py -v`
Expected: PASS, whole file.

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/cc_pretty_intercept/parse.py tests/test_cc_pretty_intercept.py
git commit -m "$(cat <<'MSG'
cc-pretty-intercept: type the capture's http region

_Base allows extra keys, so the region loaded but nothing could read it without
reaching into __pydantic_extra__. Http carries method, url, the ordered header
pairs, the credential slot and the response's status and headers, with
header()/response_header() doing the case-insensitive lookup every caller
otherwise repeats.

Optional, because 94,820 captures predate the region and their absence of it is
normal rather than a parse failure.

Claude-Session: d01082f1-9b11-4484-9620-f1923a66d187
MSG
)"
```

---

## Task 3: The renderer shows the region

**Files:**
- Modify: `src/claude_config/cc_pretty_intercept/convert.py:169-215`
- Modify: `src/claude_config/cc_pretty_intercept/main.py:42-54, 70-82`
- Modify: `tests/test_pretty_parity.py:37`
- Test: `tests/test_cc_pretty_intercept.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cc_pretty_intercept.py`. These reuse the `HTTP` constant
Task 2 Step 1 added to the same file — run Task 2 first.

```python
def test_the_header_names_the_call_the_status_and_the_betas(tmp_path) -> None:
    """A region no render shows is a region nobody reads."""
    out = render(tmp_path, capture(http=HTTP))

    assert "POST https://api.anthropic.com/v1/messages?beta=true" in out
    assert "200" in out
    assert "req_011CfYdgBnuh" in out
    assert "claude-code-20250219,effort-2025-11-24" in out


def test_show_http_dumps_every_header_and_the_default_does_not(tmp_path) -> None:
    plain = render(tmp_path, capture(http=HTTP))
    full = render(tmp_path, capture(http=HTTP), "--show-http")

    assert "anthropic-ratelimit-unified-5h-utilization" not in plain
    assert "anthropic-ratelimit-unified-5h-utilization" in full
    assert "x-app" in full
    assert "115 chars, not captured" in full


def test_a_capture_with_no_http_region_renders_as_before(tmp_path) -> None:
    out = render(tmp_path, capture())
    assert "claude-test" in out
    assert "POST" not in out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cc_pretty_intercept.py -k "names_the_call or show_http_dumps" -v`
Expected: FAIL — the first on the missing `POST …` line, the second with `unrecognized arguments: --show-http`.

- [ ] **Step 3: Extend `header_lines`**

In `src/claude_config/cc_pretty_intercept/convert.py`, change the signature:

```python
def header_lines(log: InterceptLog, path: str, *, show_http: bool = False) -> list[str]:
    """The capture's front-matter: what the call was, not what it said.

    Plain strings — ``run_pipeline`` prints them above the legend, and the
    caller colors them.

    The ``http`` region's call line and beta list are always shown. The beta
    list decides what the API did with the body and varies per request inside
    one session, so nobody would think to go looking for it until it had already
    misled them. ``show_http`` adds every header.
    """
```

Then, immediately before the closing `return ["  ".join(group) for group in lines]`, insert:

```python
    if log.http:
        call: list[str] = []
        if log.http.method and log.http.url:
            call.append(f"{log.http.method} {log.http.url}")
        if log.http.response and log.http.response.status:
            call.append(f"-> {log.http.response.status}")
        rid = log.http.response_header("request-id")
        if rid:
            call.append(rid)
        if call:
            lines.append(call)

        betas = log.http.header("anthropic-beta")
        if betas:
            lines.append([f"betas: {betas}"])

        if show_http:
            for label, pairs in (
                ("req ", log.http.request_headers),
                ("resp", log.http.response.headers if log.http.response else []),
            ):
                for name, value in pairs:
                    lines.append([f"{label} {name}: {value}"])
            cred = log.http.credential
            if cred:
                lines.append([
                    f"req  {cred.header}: {cred.scheme} "
                    f"<{cred.length} chars, not captured>"
                ])
```

- [ ] **Step 4: Add the flag**

In `src/claude_config/cc_pretty_intercept/main.py`, after the `--no-tools` argument:

```python
    region.add_argument(
        "--show-http",
        action="store_true",
        help="Dump every request and response header from the http region",
    )
```

and change the `run_pipeline` call's header argument:

```python
        header=header_lines(log, args.file, show_http=args.show_http),
```

- [ ] **Step 5: Widen the parity allowance**

`tests/test_pretty_parity.py` asserts each front-end invents no flag outside a
named set. Change line 37:

```python
# Regions only an API payload has; the other two formats hold no system prompt,
# tool schema or HTTP envelope to show.
INTERCEPT_ONLY = {"--no-system", "--no-tools", "--show-http"}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_cc_pretty_intercept.py tests/test_pretty_parity.py -v`
Expected: PASS, both files.

- [ ] **Step 7: Commit**

```bash
git add src/claude_config/cc_pretty_intercept/convert.py src/claude_config/cc_pretty_intercept/main.py tests/test_cc_pretty_intercept.py tests/test_pretty_parity.py
git commit -m "$(cat <<'MSG'
cc-pretty-intercept: put the call, the status and the betas in the header

A capture region no render shows is a region nobody reads. The call line and the
beta list are always on -- the beta list decides what the API did with the body
and varies per request inside one session, so it is not something a reader would
go looking for before it had misled them. --show-http dumps every header,
rate-limit utilization included, and names the credential slot without a value.

A capture with no http region renders exactly as before.

Claude-Session: d01082f1-9b11-4484-9620-f1923a66d187
MSG
)"
```

---

## Task 4: `cc-replay extract`

**Files:**
- Create: `src/claude_config/cc_replay/__init__.py`, `proxy_module.py`, `extract.py`
- Modify: `tests/test_intercept_proxy.py:30-38` (use the shared loader)
- Test: `tests/test_cc_replay.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cc_replay.py`:

```python
"""cc-replay turns a capture into an editable request and sends it back.

The extract/send pair exists so a what-if is a file you edit rather than a flag
you remember, and so a replay's result renders under the same front-end as the
capture it came from.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_config.cc_replay.extract import extract
from claude_config.cc_replay.proxy_module import load_proxy

HTTP = {
    "method": "POST",
    "url": "https://api.anthropic.com/v1/messages?beta=true",
    "http_version": "HTTP/1.1",
    "request_headers": [
        ["Accept", "application/json"],
        ["anthropic-beta", "claude-code-20250219,effort-2025-11-24"],
        ["Content-Length", "4145"],
        ["Host", "api.anthropic.com"],
        ["x-client-request-id", "7fa860c6-4611-456e-b4ed-415f87619442"],
        ["X-Stainless-Retry-Count", "2"],
        ["X-Claude-Code-Session-Id", "ea529de9-61c3-422b-8868-b008a66ded9d"],
    ],
    "credential": {"header": "Authorization", "scheme": "Bearer", "length": 115},
    "response": {
        "status": 200, "reason": "OK",
        "headers": [["request-id", "req_011CfYdgBnuh"]],
    },
}


def capture(**over) -> dict:
    base = {
        "timestamp": "2026-09-29T23:54:47+00:00",
        "duration_ms": 2100,
        "session": {"session_id": "ea529de9-61c3-422b-8868-b008a66ded9d"},
        "streaming": True,
        "request": {
            "model": "claude-opus-5",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        },
        "response": {"model": "claude-opus-5", "usage": {"input_tokens": 9, "output_tokens": 3}},
        "http": HTTP,
    }
    base.update(over)
    return base


def write_capture(tmp_path: Path, cap: dict) -> Path:
    path = tmp_path / "0007.json"
    path.write_text(json.dumps(cap))
    return path


def test_the_addon_loader_finds_parse_sse_stream() -> None:
    """The dependency runs package -> addon; proxy.py imports nothing."""
    assert callable(load_proxy().parse_sse_stream)


def test_extract_writes_the_body_the_call_and_what_it_answered(tmp_path) -> None:
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    body = json.loads((out / "request.json").read_text())
    http = json.loads((out / "http.json").read_text())
    meta = json.loads((out / "meta.json").read_text())

    assert body["model"] == "claude-opus-5"
    assert http["headers_source"] == "captured"
    assert http["url"].endswith("?beta=true")
    assert ["anthropic-beta", "claude-code-20250219,effort-2025-11-24"] in http["request_headers"]
    # The original response's own headers belong to the original, not to what
    # is about to be sent.
    assert "response" not in http
    assert meta["request_id"] == "req_011CfYdgBnuh"
    assert meta["status"] == 200
    assert meta["usage"] == {"input_tokens": 9, "output_tokens": 3}
    assert meta["source"].endswith("0007.json")


def test_extract_refuses_to_overwrite_a_directory_with_work_in_it(tmp_path) -> None:
    out = tmp_path / "w1"
    out.mkdir()
    (out / "request.json").write_text("{}")

    with pytest.raises(FileExistsError):
        extract(write_capture(tmp_path, capture()), out)

    extract(write_capture(tmp_path, capture()), out, force=True)
    assert json.loads((out / "request.json").read_text())["model"] == "claude-opus-5"


def test_a_capture_with_no_http_region_is_marked_synthesized(tmp_path) -> None:
    """The betas are unrecoverable; saying so is the whole point of the mark."""
    cap = capture()
    del cap["http"]
    out = tmp_path / "old"
    extract(write_capture(tmp_path, cap), out)

    http = json.loads((out / "http.json").read_text())
    assert http["headers_source"] == "synthesized"
    assert http["url"] == "https://api.anthropic.com/v1/messages?beta=true"
    assert not any(name.lower() == "anthropic-beta" for name, _ in http["request_headers"])


@pytest.mark.parametrize(
    ("model", "host"),
    [("k3", "api.kimi.ai"), ("glm-5.3", "api.z.ai"), ("claude-opus-5", "api.anthropic.com")],
)
def test_a_synthesized_url_picks_its_host_off_the_model_id(tmp_path, model, host) -> None:
    cap = capture()
    del cap["http"]
    cap["request"]["model"] = model
    out = tmp_path / model
    extract(write_capture(tmp_path, cap), out)

    assert json.loads((out / "http.json").read_text())["url"] == f"https://{host}/v1/messages?beta=true"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cc_replay.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'claude_config.cc_replay'`.

- [ ] **Step 3: Create the package and the addon loader**

`src/claude_config/cc_replay/__init__.py` — empty file.

`src/claude_config/cc_replay/proxy_module.py`:

```python
"""Load `scripts/intercept/proxy.py` as a module.

The addon imports nothing outside the standard library, which is what keeps the
bare `mitmdump -s proxy.py` invocation in its README working — the same
invocation whose survival was why this repo rejected mitmproxy's
`store_streamed_bodies` option. So the dependency runs one way: the package
reaches into the addon, never the reverse.

What is borrowed is `parse_sse_stream` and `error_detail`. A replay reassembled
by a second implementation is not comparable to the capture it exists to be
compared against.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

# src/claude_config/cc_replay/proxy_module.py -> repo root
PROXY_PATH = Path(__file__).resolve().parents[3] / "scripts" / "intercept" / "proxy.py"

_cached: ModuleType | None = None


def load_proxy() -> ModuleType:
    """The addon module, loaded once per process."""
    global _cached
    if _cached is not None:
        return _cached
    if not PROXY_PATH.is_file():
        raise FileNotFoundError(f"intercept addon not found at {PROXY_PATH}")
    spec = importlib.util.spec_from_file_location("intercept_proxy", PROXY_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {PROXY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached = module
    return module
```

- [ ] **Step 4: Create `extract.py`**

```python
"""Write a capture out as an editable request directory.

Three files, because the artifact between extract and send is meant to be
edited by hand: `request.json` is the body, `http.json` the call around it,
`meta.json` what the original call answered. Nothing written here is a secret.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# A capture written before proxy.py recorded the call supplies neither host nor
# path. Both are guessed from the model id, and `headers_source` says so rather
# than letting the guess pass for recorded fact.
MODEL_HOSTS = (("k3", "api.kimi.ai"), ("glm", "api.z.ai"))
DEFAULT_HOST = "api.anthropic.com"
DEFAULT_PATH = "/v1/messages?beta=true"


def synthesized_http(body: dict[str, Any]) -> dict[str, Any]:
    """The least that could have been sent, for a capture that did not record it."""
    model = str(body.get("model", ""))
    host = next(
        (h for prefix, h in MODEL_HOSTS if model.startswith(prefix)), DEFAULT_HOST
    )
    return {
        "method": "POST",
        "url": f"https://{host}{DEFAULT_PATH}",
        "http_version": "HTTP/1.1",
        "request_headers": [
            ["Accept", "application/json"],
            ["Content-Type", "application/json"],
            ["anthropic-version", "2023-06-01"],
        ],
        "headers_source": "synthesized",
    }


def _request_id(http: dict[str, Any]) -> str:
    headers = (http.get("response") or {}).get("headers") or []
    return next((v for k, v in headers if k.lower() == "request-id"), "")


def extract(capture_path: Path, out_dir: Path, *, force: bool = False) -> dict[str, Any]:
    """Write the three files and return the `http.json` that was written."""
    capture = json.loads(Path(capture_path).read_text())
    body = capture.get("request")
    if not isinstance(body, dict):
        raise ValueError(f"{capture_path}: no request body to replay")

    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        raise FileExistsError(
            f"{out_dir} is not empty; pass --force to overwrite what is there"
        )
    out_dir.mkdir(parents=True, exist_ok=True)

    captured = capture.get("http")
    if isinstance(captured, dict):
        # The original response's headers describe the original call, not the
        # one about to be sent.
        http = {k: v for k, v in captured.items() if k != "response"}
        http["headers_source"] = "captured"
    else:
        captured = {}
        http = synthesized_http(body)

    meta = {
        "source": str(Path(capture_path).resolve()),
        "session": capture.get("session") or {},
        "timestamp": capture.get("timestamp", ""),
        "duration_ms": capture.get("duration_ms", 0),
        "status": (captured.get("response") or {}).get("status")
        or (capture.get("error") or {}).get("status")
        or 0,
        "request_id": _request_id(captured),
        "usage": (capture.get("response") or {}).get("usage") or {},
    }

    (out_dir / "request.json").write_text(json.dumps(body, indent=2) + "\n")
    (out_dir / "http.json").write_text(json.dumps(http, indent=2) + "\n")
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return http
```

- [ ] **Step 5: Point the proxy test at the shared loader**

`tests/test_intercept_proxy.py:30-38` defines its own `_load_proxy`. One
definition is enough. Replace:

```python
def _load_proxy():
    spec = importlib.util.spec_from_file_location("intercept_proxy", _PROXY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proxy = _load_proxy()
```

with:

```python
proxy = load_proxy()
```

Add `from claude_config.cc_replay.proxy_module import load_proxy` to the imports
and drop the now-unused `import importlib.util`. Keep `_PROXY`: the test
`test_only_conversation_shaped_bodies_are_logged` reads the addon's source text
through it.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_cc_replay.py tests/test_intercept_proxy.py -v`
Expected: PASS, both files.

- [ ] **Step 7: Commit**

```bash
git add src/claude_config/cc_replay/ tests/test_cc_replay.py tests/test_intercept_proxy.py
git commit -m "$(cat <<'MSG'
cc-replay: extract a capture into an editable request directory

request.json is the body, http.json the call around it, meta.json what the
original answered -- three files because a what-if should be a file you edit,
not a flag you remember, and because the edited request is itself durable and
diffable.

A capture with no http region gets headers_source "synthesized" and a URL
guessed from the model id. The guess is labelled rather than presented as
recorded fact: the original beta list is unrecoverable and no later work
changes that.

proxy_module loads the addon by path so the package can borrow parse_sse_stream
without proxy.py importing anything -- the bare `mitmdump -s proxy.py` in its
README has to keep working. tests/test_intercept_proxy.py now uses that one
loader instead of its own copy.

Claude-Session: d01082f1-9b11-4484-9620-f1923a66d187
MSG
)"
```

---

## Task 5: Credential resolution

**Files:**
- Create: `src/claude_config/cc_replay/credentials.py`
- Test: `tests/test_cc_replay.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cc_replay.py`:

```python
# ── Credentials ─────────────────────────────────────────────────────────────
#
# A capture never carries one. Every resolution names its source, because an
# API key and an OAuth bearer are not the same caller: whether a beta such as
# claude-code-20250219 is gated to the OAuth path is unverified, so a replay
# that diverges from its capture must be able to rule the credential in or out.

import time as _time

from claude_config.cc_replay import credentials as creds


def _store(tmp_path, token="oauth-token-value", expires_in=3600.0):
    path = tmp_path / ".credentials.json"
    path.write_text(json.dumps({
        "claudeAiOauth": {
            "accessToken": token,
            "expiresAt": int((_time.time() + expires_in) * 1000),
        }
    }))
    return path


def test_the_first_party_host_resolves_the_oauth_store_first(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", _store(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-api-key")

    cred = creds.resolve("https://api.anthropic.com/v1/messages?beta=true")
    assert cred is not None
    assert cred.header == "Authorization"
    assert cred.value == "Bearer oauth-token-value"
    assert "claudeAiOauth" in cred.source


def test_an_api_key_fills_in_when_the_store_has_no_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", tmp_path / "absent.json")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-api-key")

    cred = creds.resolve("https://api.anthropic.com/v1/messages")
    assert cred is not None
    assert (cred.header, cred.value) == ("x-api-key", "an-api-key")
    assert cred.source == "$ANTHROPIC_API_KEY"


def test_an_expired_oauth_token_is_refused_by_name(tmp_path, monkeypatch) -> None:
    """A 401 from a stale token reads as an API fault; this does not."""
    monkeypatch.setattr(creds, "OAUTH_STORE", _store(tmp_path, expires_in=-60.0))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="expired"):
        creds.resolve("https://api.anthropic.com/v1/messages")


@pytest.mark.parametrize(
    ("host", "var"),
    [("api.kimi.ai", "KIMI_API_KEY"), ("api.z.ai", "ZAI_API_KEY")],
)
def test_each_provider_host_reads_its_own_key(monkeypatch, host, var) -> None:
    monkeypatch.setenv(var, "provider-key")
    cred = creds.resolve(f"https://{host}/v1/messages")
    assert cred is not None
    assert (cred.header, cred.value, cred.source) == ("Authorization", "Bearer provider-key", f"${var}")


def test_an_unknown_host_is_refused_rather_than_sent_uncredentialed() -> None:
    with pytest.raises(RuntimeError, match="127.0.0.1"):
        creds.resolve("http://127.0.0.1:8080/v1/messages")


def test_no_credential_and_an_explicit_env_var_both_override_the_table(monkeypatch) -> None:
    assert creds.resolve("http://127.0.0.1:8080/v1/messages", none=True) is None

    monkeypatch.setenv("MY_TOKEN", "t")
    cred = creds.resolve("http://127.0.0.1:8080/v1/messages", env_var="MY_TOKEN")
    assert cred is not None
    assert cred.value == "Bearer t"

    monkeypatch.delenv("MY_TOKEN")
    with pytest.raises(RuntimeError, match="MY_TOKEN"):
        creds.resolve("http://127.0.0.1:8080/v1/messages", env_var="MY_TOKEN")


def test_every_source_coming_up_empty_names_what_was_tried(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", tmp_path / "absent.json")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match=r"ANTHROPIC_API_KEY"):
        creds.resolve("https://api.anthropic.com/v1/messages")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cc_replay.py -k "credential or oauth or provider_host or unknown_host or every_source" -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'claude_config.cc_replay.credentials'`.

- [ ] **Step 3: Create `credentials.py`**

```python
"""Resolve a credential for a replay. A capture never carries one.

Resolution is by host, and every resolution names its source. An API key and an
OAuth bearer are not the same caller — whether a beta such as
`claude-code-20250219` is gated to the OAuth path is unverified — so a replay
that diverges from its capture has to be able to rule the credential in or out.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

# Claude Code's own store. Home-rooted, so a replay works from a worktree,
# whose gitignored .env is absent and where no other credential resolves.
OAUTH_STORE = Path.home() / ".claude" / ".credentials.json"


@dataclass(frozen=True)
class Credential:
    header: str
    value: str
    source: str


def _oauth() -> Credential | None:
    if not OAUTH_STORE.is_file():
        return None
    entry = json.loads(OAUTH_STORE.read_text()).get("claudeAiOauth") or {}
    token = entry.get("accessToken")
    if not token:
        return None
    expires_at = entry.get("expiresAt")
    if expires_at and expires_at / 1000 <= time.time():
        when = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(expires_at / 1000))
        raise RuntimeError(
            f"{OAUTH_STORE}: claudeAiOauth expired at {when}. A stale token comes "
            "back as a 401 that reads like an API fault, so it is refused here "
            "instead. Open an interactive Claude Code session to refresh it, or "
            "pass --credential-env with an API key."
        )
    return Credential("Authorization", f"Bearer {token}", f"{OAUTH_STORE}:claudeAiOauth")


def _from_env(var: str, header: str) -> Credential | None:
    value = os.environ.get(var)
    if not value:
        return None
    prefix = "" if header.lower() == "x-api-key" else "Bearer "
    return Credential(header, f"{prefix}{value}", f"${var}")


Source = tuple[str, Callable[[], Credential | None]]

HOST_SOURCES: dict[str, tuple[Source, ...]] = {
    "api.anthropic.com": (
        (f"{OAUTH_STORE}:claudeAiOauth", _oauth),
        ("$ANTHROPIC_API_KEY", lambda: _from_env("ANTHROPIC_API_KEY", "x-api-key")),
    ),
    "api.kimi.ai": (
        ("$KIMI_API_KEY", lambda: _from_env("KIMI_API_KEY", "Authorization")),
    ),
    "api.z.ai": (
        ("$ZAI_API_KEY", lambda: _from_env("ZAI_API_KEY", "Authorization")),
    ),
}


def resolve(
    url: str, *, env_var: str | None = None, none: bool = False
) -> Credential | None:
    """The credential to send to `url`, or None when explicitly asked for none."""
    if none:
        return None
    if env_var:
        cred = _from_env(env_var, "Authorization")
        if cred is None:
            raise RuntimeError(f"${env_var} is unset or empty")
        return cred

    host = urlsplit(url).hostname or ""
    sources = HOST_SOURCES.get(host)
    if sources is None:
        raise RuntimeError(
            f"no credential source is known for host {host!r}. Pass "
            "--credential-env VAR, or --no-credential if the destination needs "
            "none — sending a first-party body somewhere else should read like "
            "the deliberate act it is."
        )
    for _, source in sources:
        cred = source()
        if cred is not None:
            return cred
    raise RuntimeError(
        f"no credential resolved for {host}; tried "
        + ", ".join(label for label, _ in sources)
    )
```

Note: `HOST_SOURCES` captures `OAUTH_STORE`'s value in its label at import time.
The `_oauth` function reads the module global at call time, which is what lets
the tests `monkeypatch.setattr(creds, "OAUTH_STORE", ...)` and have it take
effect. The stale label in the error message is cosmetic and tests only assert
on `$ANTHROPIC_API_KEY`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_cc_replay.py -v`
Expected: PASS, whole file.

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/cc_replay/credentials.py tests/test_cc_replay.py
git commit -m "$(cat <<'MSG'
cc-replay: resolve a credential by host and name the source

A capture carries no credential by design, so a replay resolves its own:
the OAuth store first for api.anthropic.com, then ANTHROPIC_API_KEY as
x-api-key, and one env var each for the Kimi and Z.ai endpoints. The store is
home-rooted, so this also works from a worktree, where no .env exists.

Every resolution names its source because an API key and an OAuth bearer are
not the same caller -- whether claude-code-20250219 is gated to the OAuth path
is unverified, and a replay that diverges needs to be able to rule that out.

An expired claudeAiOauth is refused by name rather than sent: a 401 from a
stale token reads like an API fault. A host outside the table is refused too,
not sent uncredentialed.

Claude-Session: d01082f1-9b11-4484-9620-f1923a66d187
MSG
)"
```

---

## Task 6: `cc-replay send`

**Files:**
- Create: `src/claude_config/cc_replay/send.py`, `src/claude_config/cc_replay/main.py`
- Test: `tests/test_cc_replay.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cc_replay.py`:

```python
# ── Sending ─────────────────────────────────────────────────────────────────

import socket
import threading

from claude_config.cc_replay.send import DEVIATIONS, outgoing_headers, send

SEEN: list[list[str]] = []

_EVENTS = (
    {"type": "message_start", "message": {"id": "msg_replay", "model": "claude-replayed",
                                          "role": "assistant", "usage": {"input_tokens": 5}}},
    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
    {"type": "content_block_delta", "index": 0,
     "delta": {"type": "text_delta", "text": "replayed"}},
    {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 2}},
)


def _serve(conn: socket.socket, status: bytes, payload: bytes | None) -> None:
    buf = b""
    while b"\r\n\r\n" not in buf:
        received = conn.recv(65536)
        if not received:
            conn.close()
            return
        buf += received
    head, _, rest = buf.partition(b"\r\n\r\n")
    lines = head.decode().split("\r\n")
    SEEN.append(lines)
    length = next(
        (int(line.split(":", 1)[1]) for line in lines
         if line.lower().startswith("content-length:")), 0
    )
    while len(rest) < length:
        rest += conn.recv(65536)

    if payload is not None:
        conn.sendall(
            status + b"Content-Type: application/json\r\n"
            b"Content-Length: %d\r\nConnection: close\r\n\r\n" % len(payload) + payload
        )
    else:
        conn.sendall(
            status + b"Content-Type: text/event-stream\r\n"
            b"Transfer-Encoding: chunked\r\nCache-Control: no-cache\r\n"
            b"request-id: req_replayed\r\n\r\n"
        )
        for event in _EVENTS:
            chunk = f"data: {json.dumps(event)}\n\n".encode()
            conn.sendall(b"%x\r\n" % len(chunk) + chunk + b"\r\n")
        conn.sendall(b"0\r\n\r\n")
    conn.close()


@pytest.fixture
def origin():
    """A local origin answering with SSE, or with whatever `respond_with` sets."""
    state: dict = {"status": b"HTTP/1.1 200 OK\r\n", "payload": None}
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)

    def accept_loop() -> None:
        while True:
            try:
                conn, _ = listener.accept()
            except OSError:
                return
            threading.Thread(
                target=_serve, args=(conn, state["status"], state["payload"]), daemon=True
            ).start()

    threading.Thread(target=accept_loop, daemon=True).start()
    SEEN.clear()
    yield listener.getsockname()[1], state
    listener.close()


def test_the_five_deviating_headers_deviate_and_nothing_else_changes() -> None:
    sent = outgoing_headers(HTTP["request_headers"])
    names = [name.lower() for name, _ in sent]

    assert "content-length" not in names
    assert "host" not in names
    assert "connection" not in names
    values = dict(sent)
    assert values["X-Stainless-Retry-Count"] == "0"
    assert values["x-client-request-id"] != "7fa860c6-4611-456e-b4ed-415f87619442"
    # Everything else, casing and order intact.
    assert [name for name, _ in sent] == [
        "Accept", "anthropic-beta", "x-client-request-id",
        "X-Stainless-Retry-Count", "X-Claude-Code-Session-Id",
    ]
    assert values["anthropic-beta"] == "claude-code-20250219,effort-2025-11-24"
    # The session id reached Anthropic on the original call.
    assert values["X-Claude-Code-Session-Id"] == "ea529de9-61c3-422b-8868-b008a66ded9d"
    assert set(DEVIATIONS) == {
        "x-client-request-id", "x-stainless-retry-count",
        "content-length", "host", "connection",
    }


def test_a_send_round_trips_and_the_result_renders_as_a_capture(tmp_path, origin) -> None:
    from claude_config.cc_pretty_intercept.main import main as render_main

    port, _ = origin
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    result = send(out, url=f"http://127.0.0.1:{port}/v1/messages?beta=true",
                  credential=None)

    entry = json.loads(result.read_text())
    assert entry["response"]["id"] == "msg_replay"
    assert entry["response"]["content"] == [{"type": "text", "text": "replayed"}]
    assert entry["http"]["response"]["status"] == 200
    assert entry["replay"]["headers_source"] == "captured"
    assert entry["replay"]["source"].endswith("0007.json")
    assert set(entry["replay"]["deviations"]) == set(DEVIATIONS)
    # The raw stream, kept because comparing streams is what a faithful
    # re-send is for.
    assert "data: " in result.with_suffix(".sse").read_text()

    # The result is a capture, so the capture front-end renders it.
    render_main([str(result), "--show-http"])


def test_the_origin_receives_the_captured_betas_and_a_fresh_request_id(tmp_path, origin) -> None:
    port, _ = origin
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)
    send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    received = {
        line.split(":", 1)[0].lower(): line.split(":", 1)[1].strip()
        for line in SEEN[0][1:] if ":" in line
    }
    assert received["anthropic-beta"] == "claude-code-20250219,effort-2025-11-24"
    assert received["x-stainless-retry-count"] == "0"
    assert received["x-client-request-id"] != "7fa860c6-4611-456e-b4ed-415f87619442"


def test_a_second_send_does_not_overwrite_the_first_result(tmp_path, origin) -> None:
    port, _ = origin
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    first = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)
    second = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    assert first.name == "result-0001.json"
    assert second.name == "result-0002.json"


def test_a_refused_replay_records_the_api_s_own_reason(tmp_path, origin) -> None:
    port, state = origin
    state["status"] = b"HTTP/1.1 429 Too Many Requests\r\n"
    state["payload"] = json.dumps(
        {"type": "error", "error": {"type": "rate_limit_error", "message": "slow down"}}
    ).encode()

    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)
    result = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    entry = json.loads(result.read_text())
    assert "response" not in entry
    assert entry["error"] == {
        "status": 429, "statusText": "Too Many Requests",
        "type": "rate_limit_error", "message": "slow down",
    }


def test_send_refuses_synthesized_headers_until_told_to_accept_them(tmp_path, origin) -> None:
    """A re-send missing the original betas is a different call."""
    port, _ = origin
    cap = capture()
    del cap["http"]
    out = tmp_path / "old"
    extract(write_capture(tmp_path, cap), out)

    with pytest.raises(RuntimeError, match="synthesized"):
        send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    result = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None,
                  accept_synthesized=True)
    assert json.loads(result.read_text())["replay"]["headers_source"] == "synthesized"


def test_the_credential_is_sent_but_never_written_to_the_result(tmp_path, origin) -> None:
    port, _ = origin
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    result = send(
        out, url=f"http://127.0.0.1:{port}/v1/messages",
        credential=creds.Credential("Authorization", "Bearer super-secret", "$TEST"),
    )

    received = {line.split(":", 1)[0].lower() for line in SEEN[0][1:] if ":" in line}
    assert "authorization" in received
    assert "super-secret" not in result.read_text()
    assert json.loads(result.read_text())["replay"]["credential"] == "$TEST"


def test_a_non_streaming_request_is_stored_verbatim(tmp_path, origin) -> None:
    port, state = origin
    state["payload"] = json.dumps(
        {"id": "msg_plain", "model": "m", "content": [{"type": "text", "text": "plain"}]}
    ).encode()

    cap = capture()
    cap["request"]["stream"] = False
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, cap), out)
    result = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    entry = json.loads(result.read_text())
    assert entry["streaming"] is False
    assert entry["response"]["id"] == "msg_plain"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cc_replay.py -k "deviating or round_trips or origin_receives or second_send or refused_replay or synthesized_headers or credential_is_sent or non_streaming" -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'claude_config.cc_replay.send'`.

- [ ] **Step 3: Create `send.py`**

```python
"""Send a request directory and record what came back.

The result is written in the capture format, so `cc-pretty-intercept` renders a
replay with no front-end of its own, and reassembly goes through the proxy's own
`parse_sse_stream` — a replay shaped by a second reassembler is not comparable
to the capture it exists to be compared against.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from claude_config.cc_replay.credentials import Credential
from claude_config.cc_replay.proxy_module import load_proxy

# Headers the client owns, or that would assert something false if repeated.
# Every other captured header goes out as captured, anthropic-beta first among
# them. X-Claude-Code-Session-Id is deliberately not here: it reached the API on
# the original call, so a faithful re-send carries it.
DEVIATIONS = (
    "x-client-request-id",
    "x-stainless-retry-count",
    "content-length",
    "host",
    "connection",
)
_CLIENT_OWNED = frozenset({"content-length", "host", "connection"})


def outgoing_headers(captured: list[list[str]]) -> list[tuple[str, str]]:
    """The captured header list as it goes back out, casing and order intact."""
    sent: list[tuple[str, str]] = []
    for name, value in captured:
        low = name.lower()
        if low in _CLIENT_OWNED:
            continue
        if low == "x-client-request-id":
            value = str(uuid.uuid4())
        elif low == "x-stainless-retry-count":
            value = "0"
        sent.append((name, value))
    return sent


def next_result_path(out_dir: Path) -> Path:
    """`result-NNNN.json` after the highest already there; a send never clobbers."""
    used = [
        int(digits)
        for path in out_dir.glob("result-*.json")
        if (digits := path.stem.removeprefix("result-")).isdigit()
    ]
    return out_dir / f"result-{max(used, default=0) + 1:04d}.json"


def send(
    out_dir: Path,
    *,
    credential: Credential | None,
    url: str | None = None,
    timeout: float = 600.0,
    accept_synthesized: bool = False,
) -> Path:
    """Send what `out_dir` holds; return the path of the result written."""
    out_dir = Path(out_dir)
    body = json.loads((out_dir / "request.json").read_text())
    http = json.loads((out_dir / "http.json").read_text())
    meta = json.loads((out_dir / "meta.json").read_text())

    headers_source = http.get("headers_source", "captured")
    if headers_source == "synthesized" and not accept_synthesized:
        raise RuntimeError(
            f"{out_dir / 'http.json'} carries synthesized headers: the source "
            "capture predates the proxy recording them, so its anthropic-beta "
            "list is unrecoverable. A re-send without it is a different call, "
            "and that difference is what a diagnosis would otherwise blame on "
            "the model. Pass --accept-synthesized-headers to send anyway."
        )

    target = url or http["url"]
    method = http.get("method", "POST")
    headers = outgoing_headers(http.get("request_headers", []))
    if credential is not None:
        headers.append((credential.header, credential.value))
    payload = json.dumps(body).encode()
    streaming = body.get("stream") is True

    started = time.time()
    with httpx.Client(timeout=timeout) as client:
        with client.stream(
            method, target, headers=headers, content=payload
        ) as response:
            received = bytearray()
            for chunk in response.iter_bytes():
                received.extend(chunk)
            status = response.status_code
            reason = response.reason_phrase
            response_headers = [[k, v] for k, v in response.headers.multi_items()]
    duration_ms = int((time.time() - started) * 1000)

    raw = bytes(received).decode("utf-8", errors="replace")
    proxy = load_proxy()

    entry: dict[str, Any] = {
        "timestamp": datetime.fromtimestamp(started, tz=timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        **({"session": meta["session"]} if meta.get("session") else {}),
        "streaming": streaming,
        "request": body,
        "http": {
            "method": method,
            "url": target,
            "http_version": "HTTP/1.1",
            # The credential goes on the wire and not into the file, the same
            # rule the proxy follows.
            "request_headers": [
                [name, value]
                for name, value in headers
                if credential is None or name != credential.header
            ],
            "response": {
                "status": status,
                "reason": reason,
                "headers": response_headers,
            },
        },
        "replay": {
            "source": meta.get("source", ""),
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "headers_source": headers_source,
            "credential": credential.source if credential else "none",
            "deviations": list(DEVIATIONS),
        },
    }

    if status != 200:
        entry["error"] = {
            "status": status,
            "statusText": reason,
            **proxy.error_detail(bytes(received)),
        }
    else:
        entry["response"] = (
            proxy.parse_sse_stream(raw) if streaming else json.loads(raw)
        )

    result = next_result_path(out_dir)
    result.write_text(json.dumps(entry, indent=2) + "\n")
    result.with_suffix(".sse").write_text(raw)
    return result
```

- [ ] **Step 4: Create `main.py`**

```python
"""Re-send a captured API request, faithfully or with edits.

    agent-tools cc-replay extract <capture.json> <dir>
    agent-tools cc-replay send <dir> [--dry-run]

`extract` writes the request as three editable files; `send` fires what is in
them and writes the result in the capture format, so `cc-pretty-intercept`
renders it.

A first-party send spends the subscription's unified 5h/7d rate limit. It is a
real call, and the rate-limit headers it comes back with are recorded in the
result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from claude_config.cc_replay.credentials import resolve
from claude_config.cc_replay.extract import extract
from claude_config.cc_replay.send import outgoing_headers, send


def _describe(out_dir: Path, url: str | None, credential_source: str) -> None:
    body = json.loads((out_dir / "request.json").read_text())
    http = json.loads((out_dir / "http.json").read_text())
    target = url or http["url"]
    betas = next(
        (v for k, v in http.get("request_headers", []) if k.lower() == "anthropic-beta"),
        "(none)",
    )
    payload = len(json.dumps(body).encode())
    print(f"{http.get('method', 'POST')} {target}", file=sys.stderr)
    print(f"  model:      {body.get('model', '?')}", file=sys.stderr)
    print(f"  betas:      {betas}", file=sys.stderr)
    print(f"  headers:    {http.get('headers_source', 'captured')}", file=sys.stderr)
    print(f"  credential: {credential_source}", file=sys.stderr)
    print(f"  body:       {payload:,} bytes", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="cc-replay",
        description="Re-send a captured API request, faithfully or with edits",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ex = sub.add_parser("extract", help="Write a capture out as an editable request")
    ex.add_argument("capture", help="Path to a ~/.claude/requests-log capture")
    ex.add_argument("dir", help="Directory to write request.json/http.json/meta.json")
    ex.add_argument(
        "--force", action="store_true", help="Overwrite a directory that is not empty",
    )

    sd = sub.add_parser("send", help="Send a request directory and record the result")
    sd.add_argument("dir", help="Directory an earlier extract wrote")
    sd.add_argument("--url", help="Send somewhere other than the captured URL")
    sd.add_argument(
        "--credential-env", metavar="VAR",
        help="Take the bearer token from $VAR instead of the per-host default",
    )
    sd.add_argument(
        "--no-credential", action="store_true",
        help="Send no credential at all (a destination that needs none)",
    )
    sd.add_argument(
        "--accept-synthesized-headers", action="store_true",
        help="Send even though the source capture recorded no headers",
    )
    sd.add_argument(
        "--timeout", type=float, default=600.0, help="Seconds before giving up",
    )
    sd.add_argument(
        "--dry-run", action="store_true", help="Print what would be sent and stop",
    )

    args = parser.parse_args(argv)

    if args.command == "extract":
        http = extract(Path(args.capture), Path(args.dir), force=args.force)
        print(f"wrote {args.dir}/", file=sys.stderr)
        for name in ("request.json", "http.json", "meta.json"):
            size = (Path(args.dir) / name).stat().st_size
            print(f"  {name:<14} {size:>9,} bytes", file=sys.stderr)
        print(f"  headers:       {http['headers_source']}", file=sys.stderr)
        return

    out_dir = Path(args.dir)
    http = json.loads((out_dir / "http.json").read_text())
    credential = resolve(
        args.url or http["url"],
        env_var=args.credential_env,
        none=args.no_credential,
    )
    _describe(out_dir, args.url, credential.source if credential else "none")
    if args.dry_run:
        print("--dry-run: nothing sent", file=sys.stderr)
        return

    result = send(
        out_dir,
        credential=credential,
        url=args.url,
        timeout=args.timeout,
        accept_synthesized=args.accept_synthesized_headers,
    )
    entry = json.loads(result.read_text())
    status = entry["http"]["response"]["status"]
    usage = (entry.get("response") or {}).get("usage") or {}
    summary = f"{status}  {entry['duration_ms'] / 1000:.1f}s"
    if usage:
        summary += f"  in {usage.get('input_tokens', 0):,}  out {usage.get('output_tokens', 0):,}"
    print(summary, file=sys.stderr)
    print(f"wrote {result}", file=sys.stderr)
    print(f"      {result.with_suffix('.sse')}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_cc_replay.py -v`
Expected: PASS, whole file.

- [ ] **Step 6: Check the CLI end to end against a real capture, without sending**

```bash
CAP=$(find ~/.claude/requests-log -name '0001.json' | head -1)
uv run python -m claude_config.cc_replay.main extract "$CAP" /tmp/cc-replay-check-$$
uv run python -m claude_config.cc_replay.main send /tmp/cc-replay-check-$$ --dry-run
```

Expected: `extract` lists three files; `send --dry-run` prints the URL, model,
betas (`(none)` for a pre-change capture), `headers: synthesized`, the resolved
credential source, the body size, and `--dry-run: nothing sent`. Nothing is sent.

```bash
rm -rf /tmp/cc-replay-check-$$
```

- [ ] **Step 7: Commit**

```bash
git add src/claude_config/cc_replay/send.py src/claude_config/cc_replay/main.py tests/test_cc_replay.py
git commit -m "$(cat <<'MSG'
cc-replay: send a request directory and record it as a capture

send() fires what request.json and http.json hold and writes result-NNNN.json in
the capture format, so cc-pretty-intercept renders a replay with no front-end of
its own, plus result-NNNN.sse -- replays are few and comparing raw streams is
what a faithful re-send is for.

Reassembly borrows the addon's parse_sse_stream, and a non-200 its error_detail.
A replay shaped by a second implementation would not be comparable to the
capture it exists to be compared against.

Five headers deviate: a fresh x-client-request-id, a zeroed retry count, and the
three the client owns. Everything else goes out as captured, casing and order
intact, X-Claude-Code-Session-Id included -- it reached the API on the original
call. The credential goes on the wire and not into the result.

A synthesized http.json is refused until --accept-synthesized-headers. --dry-run
prints the URL, betas, credential source and body size without sending, because
a first-party send spends the subscription's 5h/7d limit.

Claude-Session: d01082f1-9b11-4484-9620-f1923a66d187
MSG
)"
```

---

## Task 7: Wiring and documentation

**Files:**
- Modify: `pyproject.toml:7-19, 21-27`
- Modify: `agent-tools/src/main.rs:101-108` (enum), `:737-744` (dispatch)
- Modify: `agent-tools/CLAUDE.md`, `scripts/intercept/README.md`, `scripts/CLAUDE.md`, `src/claude_config/CLAUDE.md`, `docs/CLAUDE.md`

- [ ] **Step 1: Declare the dependency and the entry point**

In `pyproject.toml`, add to `dependencies` after `"anthropic>=0.49.0",`:

```toml
  "httpx>=0.28.1",
```

It is present today only as a transitive dependency of `anthropic`; a module
that imports it should say so.

Add to `[project.scripts]`:

```toml
cc-replay = "claude_config.cc_replay.main:main"
```

- [ ] **Step 2: Add the subcommand to `agent-tools`**

In `agent-tools/src/main.rs`, after the `CcPrettyIntercept` variant:

```rust
    /// Re-send a captured API request, faithfully or with edits
    #[command(name = "cc-replay")]
    CcReplay {
        /// Arguments forwarded to cc-replay
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
```

and after the `Cmd::CcPrettyIntercept` dispatch arm:

```rust
            Cmd::CcReplay { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.cc_replay.main"],
                    &args,
                );
            }
```

- [ ] **Step 3: Build and check the subcommand resolves**

Run:
```bash
cd agent-tools && cargo build --release && cargo test
```
Expected: build succeeds, tests pass.

Run: `./agent-tools/target/release/agent-tools cc-replay --help`
Expected: the `cc-replay` usage with the `extract` and `send` subcommands.

- [ ] **Step 4: Document the region in the proxy README**

In `scripts/intercept/README.md`, extend the `## Log format` JSON block with the
region, directly after the `"streaming": true,` line:

```json
  "http": {
    "method": "POST",
    "url": "https://api.anthropic.com/v1/messages?beta=true",
    "http_version": "HTTP/1.1",
    "request_headers": [["anthropic-beta", "claude-code-20250219,..."], ["x-app", "cli"]],
    "credential": {"header": "Authorization", "scheme": "Bearer", "length": 115},
    "response": {"status": 200, "reason": "OK", "headers": [["request-id", "req_..."]]}
  },
```

Then add a section after `## Log format`:

```markdown
## The `http` region

Everything about the call the body cannot say: the method, the URL with its query
string, every request header as an ordered `[name, value]` pair, and the
response's status and headers. Pairs rather than an object because
`Headers.items(multi=True)` keeps a repeated header and the send order, where
`dict()` joins duplicates with `, `.

`anthropic-beta` is the reason the region exists. It varies per request inside
one session — measured on cc 2.1.269, an auxiliary call carried 8 entries and the
main call 14, the main one adding `claude-code-20250219`,
`mid-conversation-system-2026-04-07`, `mid-conversation-tool-changes-2026-07-01`,
`advanced-tool-use-2025-11-20`, `effort-2025-11-24`, `fallback-credit-2026-06-01`
and `extended-cache-ttl-2025-04-11` — so no sibling capture, model id or client
version implies it.

`authorization`, `x-api-key`, `cookie` and `proxy-authorization` never reach
disk. `credential` records the slot instead — which header, which scheme, how
many characters — which is enough to tell an OAuth bearer from an API key and to
know where a replay puts its own.

`http.response.status` is set on every call, 200 included; the top-level
`error.status` a failed call carries is unchanged.

Captures written before 2026-09-30 have no `http` key. Their beta lists are
unrecoverable, and `agent-tools cc-replay` refuses to re-send one as if it were
faithful.
```

- [ ] **Step 5: Document the subcommand in `agent-tools/CLAUDE.md`**

Insert after the `cc-pretty-intercept` bullet (`:9`):

```markdown
- `agent-tools cc-replay extract <capture.json> <dir>` / `agent-tools cc-replay send <dir>` — re-send a captured API request, faithfully or with edits. `extract` writes `request.json` (the body), `http.json` (method, URL, the captured header pairs, `headers_source`) and `meta.json` (source capture, session, and what the original call answered), refusing a non-empty directory without `--force`; edit any of them with anything. `send` resolves a credential, fires, and writes `result-NNNN.json` in the capture format — so `cc-pretty-intercept` renders a replay — plus `result-NNNN.sse`, the decoded stream, which normal captures do not keep. Reassembly borrows the proxy addon's own `parse_sse_stream`, so a replay is comparable to the capture it replays. Five headers deviate from what was captured: a fresh `x-client-request-id`, `X-Stainless-Retry-Count: 0`, and the `Content-Length`/`Host`/`Connection` the client owns; `X-Claude-Code-Session-Id` is repeated, because it reached the API on the original call. Credentials never come from the capture: `api.anthropic.com` resolves `~/.claude/.credentials.json` → `claudeAiOauth.accessToken` and then `ANTHROPIC_API_KEY`, `api.kimi.ai` takes `KIMI_API_KEY` and `api.z.ai` `ZAI_API_KEY`, an expired OAuth entry is refused by name rather than sent to fail as a 401, and a host outside that table is refused rather than sent uncredentialed — `--credential-env VAR` and `--no-credential` override. `--url` retargets a send; `--dry-run` prints the URL, model, beta list, credential source and body size and stops. **A first-party send spends the subscription's unified 5h/7d rate limit** — the `anthropic-ratelimit-unified-*` headers it returns land in the result. A capture recorded before the proxy kept headers extracts with `headers_source: "synthesized"` and is refused by `send` until `--accept-synthesized-headers`: its beta list is unrecoverable, and a re-send without it is a different call.
```

- [ ] **Step 6: Point the two directory guides at it**

In `scripts/CLAUDE.md`, replace the `intercept/` subdirectory row's description
so it names the region and the replay:

```markdown
| `intercept/` | MITM proxy that captures conversation-shaped API calls to `~/.claude/requests-log/` — only from sessions `claude.sh` launched while it was listening; its `README.md` carries the port, the CA setup, the `http` region a capture records the call in, the streaming watchdog and the five things a capture cannot record. `agent-tools cc-replay` re-sends one | Capturing requests; replaying one; diagnosing an intercepted session whose turns abort; judging what a missing capture means |
```

In `src/claude_config/CLAUDE.md`, add a row to the modules table after
`cc_pretty_intercept/`:

```markdown
| `cc_replay/`                        | Re-send a captured API request: `extract` writes it as three editable files, `send` fires them and records the result in the capture format. `proxy_module.py` loads `scripts/intercept/proxy.py` by path so the reassembler is shared without the addon importing anything — the bare `mitmdump -s proxy.py` its README documents has to keep working. `credentials.py` resolves per host and names its source; a capture never carries one | `cc-replay` |
```

- [ ] **Step 7: Correct the stale counts in `docs/CLAUDE.md`**

The `superpowers/` row reads `specs/` (18) and `plans/` (12); the directories
hold 21 and 14 after this plan lands. The drift predates this work — fix it
rather than leaving a number that was already wrong.

Run: `ls docs/superpowers/specs/*.md | wc -l && ls docs/superpowers/plans/*.md | wc -l`
Then set both numbers in that row to what the commands report.

- [ ] **Step 8: Run the whole suite and the guards**

```bash
uv run pytest
scripts/check-prompt-coupling.sh
scripts/check-prompt-rationale.sh
```
Expected: all pass. Nothing here touches an emitted literal or a prompt section,
so both guards should be unaffected — if either fails, that is a real finding.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml agent-tools/src/main.rs agent-tools/CLAUDE.md scripts/intercept/README.md scripts/CLAUDE.md src/claude_config/CLAUDE.md docs/CLAUDE.md
git commit -m "$(cat <<'MSG'
cc-replay: wire the subcommand and document the region

agent-tools cc-replay dispatches to claude_config.cc_replay.main, and httpx is
declared rather than borrowed from anthropic's dependency tree.

The proxy README gains a section on the http region -- what it holds, why
ordered pairs, why the credential is a slot and not a value, and that captures
written before 2026-09-30 have no beta list to recover. agent-tools/CLAUDE.md
carries the subcommand surface including the rate-limit cost of a first-party
send.

Also corrects the spec and plan counts in docs/CLAUDE.md, which were stale
before this change.

Claude-Session: d01082f1-9b11-4484-9620-f1923a66d187
MSG
)"
```

---

## Self-review notes

**Spec coverage.** Every section of the spec maps to a task: the `http` region →
Task 1; typed reading → Task 2; the always-on render line and `--show-http` →
Task 3; `extract`, the three files and the synthesized fallback → Task 4;
credential resolution by host → Task 5; `send`, the five deviations, the shared
reassembler, `.sse` on results only, the synthesized refusal → Task 6; wiring and
the docs → Task 7. The spec's "What this does not do" needs no task by
construction.

**One thing the spec names and no task changes:** the five losses in
`scripts/intercept/README.md`, "What a capture does not record". A call that
never produced a response still writes nothing, request half included. That is a
change to the addon's `error` hook and deliberately out of scope here; the README
edit in Task 7 Step 4 says "five", leaving that section as it stands.

**Deferred by measurement, not by choice:** whether `claude-code-20250219` is
gated to the OAuth credential path. Nothing in this plan can settle it — it needs
two replays of one capture, one per credential type, which is work for after the
tool exists.
