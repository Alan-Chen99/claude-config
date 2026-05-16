// SSE stream parser: reconstructs an Anthropic Messages API response
// from a stream of server-sent events.

export interface ContentBlock {
  type: string;
  [key: string]: unknown;
}

export interface ParsedMessage {
  id: string;
  model: string;
  role: string;
  content: ContentBlock[];
  stop_reason: string | null;
  // Set when the API sends an error event mid-stream (e.g. overloaded).
  // null means no error event was received.
  error: { type: string; message: string } | null;
  usage: {
    input_tokens: number;
    output_tokens: number;
    cache_creation_input_tokens?: number;
    cache_read_input_tokens?: number;
  };
}

export function parseSSEStream(raw: string): ParsedMessage {
  const message: ParsedMessage = {
    id: "",
    model: "",
    role: "assistant",
    content: [],
    stop_reason: null,
    error: null,
    usage: { input_tokens: 0, output_tokens: 0 },
  };

  const textAccum = new Map<number, string>();
  const jsonAccum = new Map<number, string>();
  const thinkingAccum = new Map<number, string>();

  for (const line of raw.split("\n")) {
    if (!line.startsWith("data: ")) continue;
    let event: Record<string, unknown>;
    try {
      event = JSON.parse(line.slice(6));
    } catch {
      continue;
    }

    switch (event.type) {
      case "message_start": {
        const msg = event.message as Record<string, unknown>;
        message.id = String(msg.id ?? "");
        message.model = String(msg.model ?? "");
        message.role = String(msg.role ?? "assistant");
        const u = msg.usage as Record<string, number> | undefined;
        if (u) {
          message.usage.input_tokens = u.input_tokens ?? 0;
          if (u.cache_creation_input_tokens)
            message.usage.cache_creation_input_tokens = u.cache_creation_input_tokens;
          if (u.cache_read_input_tokens)
            message.usage.cache_read_input_tokens = u.cache_read_input_tokens;
        }
        break;
      }

      case "content_block_start": {
        const idx = event.index as number;
        const block = event.content_block as Record<string, unknown>;
        const t = String(block.type ?? "unknown");
        if (t === "tool_use") {
          message.content[idx] = { type: t, id: String(block.id ?? ""), name: String(block.name ?? ""), input: {} };
        } else {
          message.content[idx] = { type: t };
        }
        break;
      }

      case "content_block_delta": {
        const idx = event.index as number;
        const delta = event.delta as Record<string, unknown>;
        const dt = delta.type;
        if (dt === "text_delta") {
          textAccum.set(idx, (textAccum.get(idx) ?? "") + String(delta.text ?? ""));
        } else if (dt === "input_json_delta") {
          jsonAccum.set(idx, (jsonAccum.get(idx) ?? "") + String(delta.partial_json ?? ""));
        } else if (dt === "thinking_delta") {
          thinkingAccum.set(idx, (thinkingAccum.get(idx) ?? "") + String(delta.thinking ?? ""));
        }
        break;
      }

      case "message_delta": {
        const delta = event.delta as Record<string, unknown>;
        if (delta.stop_reason) message.stop_reason = String(delta.stop_reason);
        const u = event.usage as Record<string, number> | undefined;
        if (u?.output_tokens) message.usage.output_tokens = u.output_tokens;
        break;
      }

      case "error": {
        const err = event.error as Record<string, unknown> | undefined;
        if (err) {
          message.error = {
            type: String(err.type ?? "unknown"),
            message: String(err.message ?? ""),
          };
        }
        break;
      }
    }
  }

  for (const [idx, text] of textAccum) {
    if (message.content[idx]) message.content[idx].text = text;
  }
  for (const [idx, json] of jsonAccum) {
    if (message.content[idx]) {
      try {
        message.content[idx].input = JSON.parse(json);
      } catch {
        message.content[idx].input = json;
      }
    }
  }
  for (const [idx, thinking] of thinkingAccum) {
    if (message.content[idx]) message.content[idx].thinking = thinking;
  }

  return message;
}
