# Technical Note: Figma Data Extraction for HMI Code Generation

## 1. Overview

This document describes which data can be extracted from a Figma document through the Plugin API and how it will be passed to the external AI service. Data is categorized as **mandatory** (required for basic functionality) or **optional** (enhances generation quality).

## 2. Mandatory Data

### 2.1 Selected Frame Export (PNG)

The primary input to the model is a rasterized screenshot of the selected frame.

- **API method:** `node.exportAsync({ format: 'PNG', constraint: { type: 'SCALE', value: 2 } })`
- **Returns:** `Uint8Array` (PNG bytes)
- **Usage:** Sent as a base64-encoded image in the request body to the local service.
- **Notes:** Scale factor of 2 ensures sufficient resolution for the model to read text labels and fine UI details.

### 2.2 Frame Metadata

Basic properties of the selected frame are needed to set the correct viewport for code generation.

| Property | API | Purpose |
|----------|-----|---------|
| Frame name | `node.name` | Used as page title / component identifier |
| Width | `node.width` | Sets the HTML viewport width |
| Height | `node.height` | Sets the HTML viewport height |
| Background | `node.backgrounds` | Sets the body/container background color |

### 2.3 Message Passing Between Plugin Logic and UI

Communication between the plugin sandbox (`code.ts`) and the plugin UI (`ui.html`) is essential for the workflow.

- **Sandbox → UI:** `figma.ui.postMessage(data)`
- **UI → Sandbox:** `parent.postMessage({ pluginMessage: data }, '*')`
- **Usage:** The sandbox extracts design data and sends it to the UI; the UI forwards it to the local service via `fetch()`.

## 3. Optional Data (Quality Enhancers)

### 3.1 Design Variables

Figma design variables (tokens) provide semantic information about the design system: colors, spacing, typography scales, border radii, etc.

- **API method:** `figma.variables.getLocalVariablesAsync()` and `figma.variables.getVariableCollectionByIdAsync(id)`
- **Returns:** Variable collections with names, types, and resolved values.
- **Extracted information:**
  - Color tokens (e.g., `--color-primary: #1A73E8`)
  - Spacing tokens (e.g., `--spacing-md: 16px`)
  - Typography tokens (e.g., `--font-size-h1: 24px`)
- **Passed to service as:** A JSON dictionary of CSS custom properties.

```json
{
  "variables": {
    "--color-primary": "#1A73E8",
    "--color-danger": "#D32F2F",
    "--color-background": "#1E1E2E",
    "--spacing-sm": "8px",
    "--spacing-md": "16px",
    "--font-size-body": "14px",
    "--font-size-h1": "24px",
    "--border-radius": "4px"
  }
}
```

### 3.2 CSS Hints

The `getCSSAsync()` method returns Inspect-panel-like CSS snippets for a given node.

- **API method:** `node.getCSSAsync()`
- **Returns:** A dictionary of CSS property-value pairs.
- **Usage:** Collected for key elements (direct children of the selected frame or user-selected sub-elements).
- **Passed to service as:** An array of CSS hint objects.

```json
{
  "css_hints": [
    {
      "node_name": "StatusCard",
      "css": {
        "width": "280px",
        "height": "160px",
        "background": "#2A2A3E",
        "border-radius": "8px",
        "padding": "16px"
      }
    }
  ]
}
```

### 3.3 Node Tree Structure (Lightweight)

A simplified tree of the selected frame's children can provide layout context.

- **Extracted from:** Recursive traversal of `node.children`
- **Collected properties:** `name`, `type`, `x`, `y`, `width`, `height`
- **Depth limit:** 2–3 levels to keep the payload manageable.

## 4. Data Flow Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Figma Desktop                      │
│                                                      │
│  ┌──────────────┐   postMessage   ┌───────────────┐ │
│  │   code.ts    │ ──────────────► │    ui.html    │ │
│  │  (sandbox)   │ ◄────────────── │   (iframe)    │ │
│  │              │   postMessage   │               │ │
│  │ • exportPNG  │                 │ • fetch()     │ │
│  │ • getVars    │                 │ • display     │ │
│  │ • getCSS     │                 │ • user input  │ │
│  └──────────────┘                 └───────┬───────┘ │
│                                           │         │
└───────────────────────────────────────────┼─────────┘
                                            │ HTTP
                                            ▼
                                 ┌─────────────────────┐
                                 │    Local Service     │
                                 │  (localhost:8000)    │
                                 │                      │
                                 │ • /generate          │
                                 │ • /refine            │
                                 │ • /edit              │
                                 │ • /render            │
                                 └─────────────────────┘
```

## 5. Summary Table

| Data | Mandatory | Optional | API Method |
|------|:---------:|:--------:|------------|
| Frame PNG screenshot | ✅ | | `exportAsync()` |
| Frame dimensions | ✅ | | `node.width`, `node.height` |
| Frame name | ✅ | | `node.name` |
| Message passing | ✅ | | `postMessage` |
| Design variables | | ✅ | `figma.variables.*` |
| CSS hints | | ✅ | `getCSSAsync()` |
| Node tree structure | | ✅ | `node.children` traversal |
