# Local Service API Reference

**Base URL:** `http://localhost:8000`

## Endpoints

### POST `/generate`

Generate HTML/CSS code from a UI screenshot.

**Request Body:**

```json
{
  "image_base64": "<base64-encoded PNG>",
  "frame_name": "Equipment Status Dashboard",
  "width": 1280,
  "height": 720,
  "css_hints": {
    "StatusCard": {
      "width": "280px",
      "background": "#2a2a3e",
      "border-radius": "8px"
    }
  },
  "variables": {
    "--color-primary": "#1A73E8",
    "--color-danger": "#D32F2F",
    "--spacing-md": "16px"
  }
}
```

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `image_base64` | string | Yes | Base64-encoded PNG screenshot of the Figma frame |
| `frame_name` | string | No | Name of the frame (used as page title) |
| `width` | int | No | Frame width in px (default: 1280) |
| `height` | int | No | Frame height in px (default: 720) |
| `css_hints` | object | No | CSS hints from Figma Inspect for key elements |
| `variables` | object | No | Figma design variables as CSS custom properties |

**Response:**

```json
{
  "code": "<!DOCTYPE html>\n<html>...</html>",
  "preview_base64": "<base64-encoded PNG of rendered result>",
  "explanation": "Initial code generated from screenshot."
}
```

---

### POST `/refine`

Iteratively improve generated code to better match the original mockup.

**Request Body:**

```json
{
  "reference_image_base64": "<base64-encoded original Figma screenshot>",
  "current_code": "<!DOCTYPE html>\n<html>...</html>",
  "css_hints": {},
  "variables": {}
}
```

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `reference_image_base64` | string | Yes | Base64-encoded PNG of the original Figma frame |
| `current_code` | string | Yes | The current HTML/CSS code to refine |
| `css_hints` | object | No | CSS hints from Figma |
| `variables` | object | No | Figma design variables |

**Response:** Same format as `/generate`.

---

### POST `/edit`

Modify existing code based on a natural-language instruction.

**Request Body:**

```json
{
  "current_code": "<!DOCTYPE html>\n<html>...</html>",
  "instruction": "Make the alarm block more prominent"
}
```

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `current_code` | string | Yes | The current HTML/CSS code to modify |
| `instruction` | string | Yes | Natural-language edit instruction |

**Response:** Same format as `/generate`.

---

### POST `/render`

Render HTML code to a PNG image (utility endpoint).

**Request Body:**

```json
{
  "html_code": "<!DOCTYPE html>\n<html>...</html>",
  "width": 1280,
  "height": 720
}
```

**Response:**

```json
{
  "image_base64": "<base64-encoded PNG>"
}
```

---

### GET `/health`

Health check.

**Response:**

```json
{
  "status": "ok",
  "model_loaded": true
}
```

## Demo Request / Response

### Demo: Generate Code

**Request:**

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "frame_name": "Equipment Status Dashboard",
    "width": 1280,
    "height": 720
  }'
```

**Response:**

```json
{
  "code": "<!DOCTYPE html>\n<html><head><style>\n  body { background: #1e1e2e; color: #e0e0e0; font-family: sans-serif; padding: 24px; }\n  .card { background: #2a2a3e; border-radius: 8px; padding: 16px; margin: 8px; display: inline-block; width: 200px; }\n  .status { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }\n  .ok { background: #4caf50; }\n  .warn { background: #ff9800; }\n</style></head><body>\n<h2>Equipment Status</h2>\n<div class=\"card\"><span class=\"status ok\"></span>Pump A — Running</div>\n<div class=\"card\"><span class=\"status warn\"></span>Pump B — Warning</div>\n</body></html>",
  "preview_base64": "iVBORw0KGgoAAAANSUhEUg...",
  "explanation": "Initial code generated from screenshot."
}
```

### Demo: Edit by Request

**Request:**

```bash
curl -X POST http://localhost:8000/edit \
  -H "Content-Type: application/json" \
  -d '{
    "current_code": "<!DOCTYPE html><html><head><style>body{background:#1e1e2e;color:#e0e0e0;}.card{background:#2a2a3e;border-radius:8px;padding:16px;margin:8px;}</style></head><body><div class=\"card\">Pump A</div></body></html>",
    "instruction": "Make the card background lighter and add a green left border"
  }'
```

**Response:**

```json
{
  "code": "<!DOCTYPE html><html><head><style>body{background:#1e1e2e;color:#e0e0e0;}.card{background:#3a3a4e;border-radius:8px;padding:16px;margin:8px;border-left:4px solid #4caf50;}</style></head><body><div class=\"card\">Pump A</div></body></html>",
  "preview_base64": "iVBORw0KGgoAAAANSUhEUg...",
  "explanation": "Edit applied: \"Make the card background lighter and add a green left border\""
}
```
