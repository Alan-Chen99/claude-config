# mcp__claude-in-chrome__gif_creator

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Manage GIF recording and export for browser automation sessions. Control when to start/stop recording browser actions (clicks, scrolls, navigation), then export as an animated GIF with visual overlays (click indicators, action labels, progress bar, watermark). All operations are scoped to the tab's group. When starting recording, take a screenshot immediately after to capture the initial state as the first frame. When stopping recording, take a screenshot immediately before to capture the final state as the last frame. For export, either provide 'coordinate' to drag/drop upload to a page element, or set 'download: true' to download the GIF.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": [
        "start_recording",
        "stop_recording",
        "export",
        "clear"
      ],
      "description": "Action to perform: 'start_recording' (begin capturing), 'stop_recording' (stop capturing but keep frames), 'export' (generate and export GIF), 'clear' (discard frames)"
    },
    "tabId": {
      "type": "number",
      "description": "Tab ID to identify which tab group this operation applies to"
    },
    "download": {
      "type": "boolean",
      "description": "Always set this to true for the 'export' action only. This causes the gif to be downloaded in the browser."
    },
    "filename": {
      "type": "string",
      "description": "Optional filename for exported GIF (default: 'recording-[timestamp].gif'). For 'export' action only."
    },
    "options": {
      "type": "object",
      "description": "Optional GIF enhancement options for 'export' action. Properties: showClickIndicators (bool), showDragPaths (bool), showActionLabels (bool), showProgressBar (bool), showWatermark (bool), quality (number 1-30). All default to true except quality (default: 10).",
      "properties": {
        "showClickIndicators": {
          "type": "boolean",
          "description": "Show orange circles at click locations (default: true)"
        },
        "showDragPaths": {
          "type": "boolean",
          "description": "Show red arrows for drag actions (default: true)"
        },
        "showActionLabels": {
          "type": "boolean",
          "description": "Show black labels describing actions (default: true)"
        },
        "showProgressBar": {
          "type": "boolean",
          "description": "Show orange progress bar at bottom (default: true)"
        },
        "showWatermark": {
          "type": "boolean",
          "description": "Show Claude logo watermark (default: true)"
        },
        "quality": {
          "type": "number",
          "description": "GIF compression quality, 1-30 (lower = better quality, slower encoding). Default: 10"
        }
      }
    }
  },
  "required": [
    "action",
    "tabId"
  ]
}
```
