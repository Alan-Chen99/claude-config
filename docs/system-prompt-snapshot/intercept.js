// Intercepts Claude Code API calls and logs system prompts + full request bodies.
//
// Usage:
//   NODE_OPTIONS='--require /path/to/intercept.js' claude
//
// Output:
//   ~/.claude/http-logs/<session>/001-system.txt   — system prompt text
//   ~/.claude/http-logs/<session>/001-request.json — full API request body
//
// Session dir is created automatically per launch. No cleanup needed between runs.
// The main system prompt is typically the largest *-system.txt file.

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const rand = crypto.randomBytes(3).toString('hex');
const sessionDir = path.join(
  process.env.HOME || '/root', '.claude', 'http-logs', `${ts}_${rand}`
);
fs.mkdirSync(sessionDir, { recursive: true });

const origFetch = globalThis.fetch;
let callNum = 0;

globalThis.fetch = async function(url, options, ...rest) {
  if (options && options.body && typeof url === 'string' && url.includes('anthropic')) {
    try {
      const body = JSON.parse(options.body);
      if (body.system) {
        callNum++;
        const prefix = String(callNum).padStart(3, '0');
        const systemTexts = body.system
          .filter(s => s.type === 'text')
          .map(s => s.text);
        const content = systemTexts.join('\n\n---BLOCK_SEPARATOR---\n\n');
        fs.writeFileSync(path.join(sessionDir, `${prefix}-system.txt`), content);
        fs.writeFileSync(
          path.join(sessionDir, `${prefix}-request.json`),
          JSON.stringify(body, null, 2)
        );
      }
    } catch(e) {}
  }
  return origFetch.call(this, url, options, ...rest);
};
