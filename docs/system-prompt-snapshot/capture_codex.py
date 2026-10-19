"""mitmdump addon: capture Codex Responses HTTP bodies / WebSocket JSON frames.

CODEX_CAPTURE_DIR must name a private scratch directory. No headers are saved.
Only request frames and terminal response frames are retained. See
../codex-prompt-capture.md for invocation, redactions and limitations.
"""

import json
import os
from pathlib import Path


REDACT_KEYS = {"safety_identifier", "x-codex-installation-id", "installation_id", "creator_user_id", "creator_account_id"}


def sanitize(value):
    """Keep linkage IDs; redact persistent account/device IDs, including nested JSON."""
    if isinstance(value, dict):
        result = {}
        for key, val in value.items():
            if key in REDACT_KEYS:
                result[key] = "[redacted]"
            elif key == "x-codex-turn-metadata" and isinstance(val, str):
                result[key] = json.dumps(sanitize(json.loads(val)), separators=(",", ":"), ensure_ascii=False)
            else:
                result[key] = sanitize(val)
        return result
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value



class Capture:
    def __init__(self):
        self.sequence = 0
        self.buffers = {}

    def save(self, obj, kind):
        out = Path(os.environ["CODEX_CAPTURE_DIR"])
        out.mkdir(parents=True, exist_ok=True)
        self.sequence += 1
        path = out / f"{self.sequence:03}-{kind}.json"
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite {path}")
        path.write_text(json.dumps(sanitize(obj), indent=2, ensure_ascii=False) + "\n")

    @staticmethod
    def target(flow):
        return flow.request.host in {"chatgpt.com", "api.openai.com"} and "/responses" in flow.request.path

    def request(self, flow):
        if self.target(flow) and flow.request.raw_content:
            try:
                obj = json.loads(flow.request.get_text())
            except ValueError:
                return
            self.save(obj, "request")

    def responseheaders(self, flow):
        if not self.target(flow) or flow.response.status_code == 101:
            return
        chunks = self.buffers[flow.id] = []

        def relay(chunk):
            chunks.append(chunk)
            return chunk

        flow.response.stream = relay

    def response(self, flow):
        chunks = self.buffers.pop(flow.id, None)
        if chunks is None:
            return
        # Delegate gzip/br decoding to mitmproxy after retaining the wire chunks.
        flow.response.raw_content = b"".join(chunks)
        text = flow.response.get_text(strict=False)
        try:
            obj = json.loads(text)
        except ValueError:
            for line in text.splitlines():
                if line.startswith("data:"):
                    try:
                        event = json.loads(line[5:].lstrip())
                    except ValueError:
                        continue
                    self.terminal(event)
        else:
            self.save(obj, "result")

    def terminal(self, obj):
        if obj.get("type") in {"response.completed", "response.failed", "error"}:
            self.save(obj, "result")

    def websocket_message(self, flow):
        if not self.target(flow):
            return
        msg = flow.websocket.messages[-1]
        try:
            obj = json.loads(msg.content)
        except (ValueError, UnicodeDecodeError):
            return
        if msg.from_client:
            self.save(obj, "request")
        else:
            self.terminal(obj)

    def error(self, flow):
        self.buffers.pop(flow.id, None)


addons = [Capture()]
