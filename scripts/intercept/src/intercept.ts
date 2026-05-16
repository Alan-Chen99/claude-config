// Intercepts Claude Code API calls via globalThis.fetch and logs
// request/response pairs to ~/.claude/requests-log/{session}/{N}.json.
//
// Usage:
//   NODE_OPTIONS='--require /path/to/dist/intercept.js' claude
//
// Observability platform integration:
//   The fetch intercept has access to the raw request body and a cloned response.
//   To integrate with any observability platform that instruments the Anthropic SDK
//   (Langfuse, Datadog, Braintrust, etc.), replay the cloned response through an
//   SDK instance with a fetch override:
//
//     const cloned = response.clone();
//     const client = new Anthropic({ apiKey: "unused", fetch: async () => cloned });
//     client.messages.create(requestBody);
//
//   Any instrumentation patching Anthropic's Messages.create will automatically
//   capture the replayed request/response as a trace. This works because the SDK
//   calls fetch internally — the override makes it consume the already-completed
//   response instead of making a real HTTP call.

import * as fs from "fs";
import * as path from "path";
import { parseSSEStream } from "./parse";

// --- Session ID ---
// CC writes ~/.claude/sessions/{pid}.json with { sessionId, pid, cwd, startedAt }.
// The PID file always exists before the first Messages API call: CC writes it
// early in startup (concurrentSessions.ts:registerSession), and the first API
// call requires either user input (interactive) or full print-mode setup.
//
// Swarm teammates are the exception: CC's registerSession() skips for processes
// with --agent-id (spawned teammates). For those, --parent-session-id in argv
// identifies the team lead's session.

let _sessionId: string | null = null;

function argvValue(flag: string): string | undefined {
  const idx = process.argv.indexOf(flag);
  return idx >= 0 && idx + 1 < process.argv.length
    ? process.argv[idx + 1]
    : undefined;
}

function resolveSessionId(): string {
  if (_sessionId) return _sessionId;

  const pidFile = path.join(
    process.env.HOME || "",
    ".claude",
    "sessions",
    `${process.pid}.json`,
  );
  try {
    const data = JSON.parse(fs.readFileSync(pidFile, "utf-8"));
    if (data.sessionId) {
      _sessionId = data.sessionId as string;
      return _sessionId;
    }
  } catch {
    // No PID file — teammate or non-CC usage
  }

  // Swarm teammates receive --parent-session-id via CLI args
  const parentSession = argvValue("--parent-session-id");
  if (parentSession) {
    const agentId = argvValue("--agent-id") ?? process.pid;
    _sessionId = `${parentSession}/teammate-${agentId}`;
    return _sessionId;
  }

  // Non-CC usage (intercept loaded into a different Anthropic client)
  // or registerSession() failed (disk error). PID is the only identifier.
  _sessionId = `pid-${process.pid}`
  return _sessionId;
}

// --- Logging ---

// Cached separately from session ID so all log files land in the same
// directory even if the first write happens before the PID file exists.
// Without this, resolveSessionId() returns "unknown-{pid}" on the first
// call and the real ID on later calls, splitting logs across directories.
let _logDirPath: string | null = null;

function logDir(): string {
  if (_logDirPath) return _logDirPath;
  _logDirPath = path.join(
    process.env.HOME || "",
    ".claude",
    "requests-log",
    resolveSessionId(),
  );
  return _logDirPath;
}

let _counter = 0;

function writeLog(entry: Record<string, unknown>): void {
  const dir = logDir();
  fs.mkdirSync(dir, { recursive: true });
  _counter++;
  const filename = `${String(_counter).padStart(3, "0")}.json`;
  fs.writeFileSync(path.join(dir, filename), JSON.stringify(entry, null, 2));
}

function logError(context: string, err: unknown): void {
  try {
    const dir = logDir();
    fs.mkdirSync(dir, { recursive: true });
    const msg = err instanceof Error ? err.stack || err.message : String(err);
    fs.appendFileSync(
      path.join(dir, "errors.log"),
      `[${new Date().toISOString()}] ${context}: ${msg}\n`,
    );
  } catch {
    // can't write error log
  }
}

// --- Fetch intercept ---

const pendingLogs: Promise<void>[] = [];
const origFetch = globalThis.fetch;

globalThis.fetch = async function (
  input: RequestInfo | URL,
  init?: RequestInit,
  ...rest: unknown[]
): Promise<Response> {
  if (!init?.body) {
    return origFetch.call(this, input, init, ...(rest as []));
  }

  let body: Record<string, unknown>;
  try {
    body = JSON.parse(init.body as string);
  } catch {
    return origFetch.call(this, input, init, ...(rest as []));
  }

  if (!body.model || !body.messages) {
    return origFetch.call(this, input, init, ...(rest as []));
  }

  const startMs = Date.now();
  const response = await origFetch.call(this, input, init, ...(rest as []));

  if (!response.ok) {
    // Log failed requests with the request body — for debugging "why did the
    // API return 400?" the request is the most important piece.
    writeLog({
      timestamp: new Date(startMs).toISOString(),
      duration_ms: Date.now() - startMs,
      session_id: resolveSessionId(),
      streaming: body.stream === true,
      error: { status: response.status, statusText: response.statusText },
      request: body,
    });
    return response;
  }

  // Skip logging if we're shutting down — the clone reader may never
  // complete because the host process is about to call process.exit().
  if (_shuttingDown) {
    return response;
  }

  const cloned = response.clone();
  const streaming = body.stream === true;

  const p = (async () => {
    try {
      const parsed = streaming
        ? parseSSEStream(await cloned.text())
        : await cloned.json();

      writeLog({
        timestamp: new Date(startMs).toISOString(),
        duration_ms: Date.now() - startMs,
        session_id: resolveSessionId(),
        streaming,
        request: body,
        response: parsed,
      });
    } catch (e) {
      logError("log", e);
    }
  })();

  pendingLogs.push(p);
  p.finally(() => {
    const idx = pendingLogs.indexOf(p);
    if (idx >= 0) pendingLogs.splice(idx, 1);
  });

  return response;
};

// --- Shutdown ---
// This script is loaded into the host process (Claude Code) via --require.
// The host has its own signal handlers that clean up terminal state, flush
// session data, and call process.exit(). We must NOT call process.exit()
// ourselves — doing so races the host's cleanup and can leave the terminal
// with mouse tracking / extended keyboard / hidden cursor enabled.
//
// Strategy:
//  - Signal handlers: drain pending log writes, nothing more.
//  - beforeExit: same drain. Fires when the event loop empties naturally
//    (never happens in practice — CC always calls process.exit() — but
//    correct to handle).
//  - Pending logs that haven't drained when the host calls process.exit()
//    are lost. This is acceptable: the host's terminal/session cleanup is
//    more important than logging.

let _shuttingDown = false;

async function shutdown(): Promise<void> {
  if (_shuttingDown) return;
  _shuttingDown = true;
  await Promise.allSettled(pendingLogs);
}

process.on("beforeExit", shutdown);
process.on("SIGTERM", () => void shutdown());
process.on("SIGINT", () => void shutdown());
