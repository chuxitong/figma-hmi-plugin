/// <reference types="@figma/plugin-typings" />

figma.showUI(__html__, { width: 480, height: 960 });

const BUILD_STAMP = "2026-05-07-r5-vars-bound-tree";
figma.notify(`HMI plugin build ${BUILD_STAMP} loaded`, { timeout: 3 });

type ExportableNode = FrameNode | ComponentNode | InstanceNode;

const MAX_BOUND_VAR_IDS = 200;
const MAX_LOCAL_VARS = 80;
const MAXSubtree_NODES = 4000;

/** Walk from the current selection to the nearest frame-like node (Figma may leave a child node selected). */
function getSelectedFrame(): ExportableNode | null {
  const selection = figma.currentPage.selection;
  if (selection.length === 0) return null;
  let node: BaseNode | null = selection[0];
  for (let depth = 0; depth < 64 && node; depth++) {
    const t = node.type;
    if (t === "PAGE" || t === "DOCUMENT") {
      return null;
    }
    if (t === "FRAME" || t === "COMPONENT" || t === "INSTANCE") {
      return node as ExportableNode;
    }
    const next: BaseNode | null = (node as { parent: BaseNode | null }).parent;
    if (!next) return null;
    node = next;
  }
  return null;
}

/** Some clients pass the unwrapped object; a few pass { pluginMessage: { type, ... } }. */
function normalizePluginMessage(raw: { type?: string; pluginMessage?: { type: string; payload?: any } } | null) {
  if (!raw) return null;
  if (typeof raw.type === "string") {
    return raw as { type: string; payload?: any };
  }
  const inner = raw.pluginMessage;
  if (inner && typeof inner.type === "string") {
    return inner;
  }
  return null;
}

async function collectCssHints(node: ExportableNode): Promise<Record<string, Record<string, string>>> {
  const cssHints: Record<string, Record<string, string>> = {};
  try {
    const css = await (node as any).getCSSAsync();
    cssHints[node.name] = css;
    if ("children" in node) {
      for (const child of node.children.slice(0, 10)) {
        if ("getCSSAsync" in child) {
          const childCss = await (child as any).getCSSAsync();
          cssHints[child.name] = childCss;
        }
      }
    }
  } catch (_err) {
    // getCSSAsync may not be available in all API versions
  }
  return cssHints;
}

/** Raw variable value → short string for the model payload. */
function formatVariableRawValue(val: unknown): string | null {
  if (val === null || val === undefined) return null;
  if (typeof val === "string") return val;
  if (typeof val === "number") return String(val);
  if (typeof val === "boolean") return String(val);
  if (typeof val === "object" && val !== null && "r" in val) {
    const c = val as { r: number; g: number; b: number; a?: number };
    const r = Math.round(c.r * 255);
    const g = Math.round(c.g * 255);
    const b = Math.round(c.b * 255);
    const a = typeof c.a === "number" ? c.a : 1;
    if (a < 1) {
      return `rgba(${r}, ${g}, ${b}, ${parseFloat(a.toFixed(2))})`;
    }
    return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
  }
  return null;
}

function variableCssKey(variable: Variable): string {
  return `--${variable.name.replace(/\//g, "-")}`;
}

function collectAliasIdsFromValue(ids: Set<string>, val: unknown): void {
  if (val === null || val === undefined) return;
  const v = val as { type?: string; id?: string };
  if (Array.isArray(val)) {
    for (let i = 0; i < val.length; i++) {
      const item = val[i] as { type?: string; id?: string };
      if (item && item.type === "VARIABLE_ALIAS" && typeof item.id === "string") {
        ids.add(item.id);
      }
    }
    return;
  }
  if (typeof v === "object" && v.type === "VARIABLE_ALIAS" && typeof v.id === "string") {
    ids.add(v.id);
    return;
  }
}

/** boundVariables maps may include fills[], strokes[], or componentProperties{ name: VariableAlias }. */
function collectAliasIdsFromBoundVariablesRecord(ids: Set<string>, bv: Record<string, unknown>): void {
  const keys = Object.keys(bv);
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i];
    const val = bv[k];
    if (k === "componentProperties" && val && typeof val === "object") {
      const subs = Object.keys(val as object);
      for (let j = 0; j < subs.length; j++) {
        collectAliasIdsFromValue(ids, (val as Record<string, unknown>)[subs[j]]);
      }
    } else {
      collectAliasIdsFromValue(ids, val);
    }
  }
}

function collectAliasesFromPaintRecord(ids: Set<string>, p: Paint): void {
  const binds = (p as { boundVariables?: Record<string, unknown> }).boundVariables;
  if (binds && typeof binds === "object") {
    const ks = Object.keys(binds);
    for (let i = 0; i < ks.length; i++) {
      collectAliasIdsFromValue(ids, binds[ks[i]]);
    }
  }
}

function collectAliasesFromEffects(ids: Set<string>, effects: readonly Effect[]): void {
  for (let e = 0; e < effects.length; e++) {
    const ef = effects[e] as { boundVariables?: Record<string, unknown> };
    if (!ef.boundVariables) continue;
    const ks = Object.keys(ef.boundVariables);
    for (let i = 0; i < ks.length; i++) {
      collectAliasIdsFromValue(ids, ef.boundVariables[ks[i]]);
    }
  }
}

function collectAliasesFromLayoutGrids(ids: Set<string>, grids: readonly LayoutGrid[]): void {
  for (let g = 0; g < grids.length; g++) {
    const grid = grids[g] as { boundVariables?: Record<string, unknown> };
    if (!grid.boundVariables) continue;
    const ks = Object.keys(grid.boundVariables);
    for (let i = 0; i < ks.length; i++) {
      collectAliasIdsFromValue(ids, grid.boundVariables[ks[i]]);
    }
  }
}

async function traverseForVariableAliases(
  ids: Set<string>,
  root: SceneNode,
  counters: { nodes: number; depth: number },
  maxDepth: number,
): Promise<void> {
  if (counters.nodes >= MAXSubtree_NODES || counters.depth > maxDepth) return;
  counters.nodes += 1;

  const n = root as any;

  if (n.boundVariables && typeof n.boundVariables === "object") {
    collectAliasIdsFromBoundVariablesRecord(ids, n.boundVariables as Record<string, unknown>);
  }

  if ("fills" in n && n.fills !== figma.mixed && Array.isArray(n.fills)) {
    for (let i = 0; i < n.fills.length; i++) {
      collectAliasesFromPaintRecord(ids, n.fills[i]);
      const fillsi = n.fills[i];
      const stops = fillsi && typeof fillsi === "object" ? (fillsi as GradientPaint).gradientStops : null;
      if (Array.isArray(stops)) {
        for (let s = 0; s < stops.length; s++) {
          const st = stops[s] as ColorStop | undefined;
          if (st && st.boundVariables) {
            const ks = Object.keys(st.boundVariables);
            for (let j = 0; j < ks.length; j++) {
              collectAliasIdsFromValue(ids, (st.boundVariables as Record<string, unknown>)[ks[j]]);
            }
          }
        }
      }
    }
  }

  if ("strokes" in n && n.strokes !== figma.mixed && Array.isArray(n.strokes)) {
    for (let i = 0; i < n.strokes.length; i++) {
      collectAliasesFromPaintRecord(ids, n.strokes[i]);
    }
  }

  if ("effects" in n && Array.isArray(n.effects)) {
    collectAliasesFromEffects(ids, n.effects as readonly Effect[]);
  }

  if ("layoutGrids" in n && Array.isArray(n.layoutGrids)) {
    collectAliasesFromLayoutGrids(ids, n.layoutGrids as readonly LayoutGrid[]);
  }

  if (n.type === "TEXT") {
    try {
      const textNode = n as TextNode;
      const fn = textNode.fontName;
      if (fn !== figma.mixed && fn && typeof fn === "object" && "family" in fn && "style" in fn) {
        await figma.loadFontAsync(fn as FontName);
      }
      const segments = textNode.getStyledTextSegments(["boundVariables"]);
      for (let s = 0; s < segments.length; s++) {
        const seg = segments[s] as { boundVariables?: Record<string, unknown> };
        if (!seg.boundVariables) continue;
        collectAliasIdsFromBoundVariablesRecord(ids, seg.boundVariables);
      }
    } catch (_e) {
      // skip text segments when font load fails
    }
  }

  if ("children" in n && Array.isArray(n.children)) {
    counters.depth += 1;
    for (let c = 0; c < n.children.length; c++) {
      const child = n.children[c];
      await traverseForVariableAliases(ids, child as SceneNode, counters, maxDepth);
    }
    counters.depth -= 1;
  }
}

async function resolveVariableIntoMap(variable: Variable, consumer: SceneNode, out: Record<string, string>): Promise<void> {
  const key = variableCssKey(variable);
  let str: string | null = null;
  try {
    const resolved = variable.resolveForConsumer(consumer as SceneNode);
    if (resolved) {
      str = formatVariableRawValue(resolved.value);
    }
  } catch (_e) {
    str = null;
  }
  if (!str) {
    const coll = await figma.variables.getVariableCollectionByIdAsync(variable.variableCollectionId);
    if (coll && coll.modes.length > 0) {
      const modeId = coll.modes[0].modeId;
      const val = variable.valuesByMode[modeId];
      str = formatVariableRawValue(val);
    }
  }
  if (str !== null && str !== "") {
    out[key] = str;
  }
}

/**
 * Enumerate VARIABLE_ALIAS ids used under `root`, then resolve each variable (library + local).
 */
async function collectBoundVariablesForSubtree(root: ExportableNode): Promise<Record<string, string>> {
  const ids = new Set<string>();
  await traverseForVariableAliases(ids, root, { nodes: 0, depth: 0 }, 256);
  let idList = Array.from(ids);
  if (idList.length > MAX_BOUND_VAR_IDS) {
    idList = idList.slice(0, MAX_BOUND_VAR_IDS);
  }

  const out: Record<string, string> = {};
  for (let i = 0; i < idList.length; i++) {
    const vid = idList[i];
    const variable = await figma.variables.getVariableByIdAsync(vid);
    if (!variable) continue;
    await resolveVariableIntoMap(variable, root, out);
  }
  return out;
}

/**
 * Older behavior: enumerate local definitions in file (excluding keys already merged from bindings).
 */
async function mergeUnusedLocalDefinitions(out: Record<string, string>): Promise<void> {
  try {
    const localVars = await figma.variables.getLocalVariablesAsync();
    const sliceEnd = Math.min(localVars.length, MAX_LOCAL_VARS);
    for (let i = 0; i < sliceEnd; i++) {
      const v = localVars[i];
      const key = variableCssKey(v);
      if (Object.prototype.hasOwnProperty.call(out, key)) continue;
      const coll = await figma.variables.getVariableCollectionByIdAsync(v.variableCollectionId);
      if (!coll || coll.modes.length === 0) continue;
      const modeId = coll.modes[0].modeId;
      const raw = v.valuesByMode[modeId];
      const str = formatVariableRawValue(raw);
      if (str !== null && str !== "") out[key] = str;
    }
  } catch (_err) {
    // Variables API unavailable
  }
}

/**
 * When "Include variables" is on: subtree-bound variables first (captures Libraries → Fill),
 * plus any extra local defs not represented.
 */
async function collectVariables(scope: ExportableNode | null): Promise<Record<string, string>> {
  const merged: Record<string, string> = {};
  try {
    if (scope !== null) {
      const bound = await collectBoundVariablesForSubtree(scope);
      const bk = Object.keys(bound);
      for (let i = 0; i < bk.length; i++) {
        merged[bk[i]] = bound[bk[i]];
      }
    }
    await mergeUnusedLocalDefinitions(merged);
  } catch (_err) {
    // keep partial
  }
  return merged;
}

figma.ui.onmessage = async (raw: { type?: string; pluginMessage?: { type: string; payload?: any }; payload?: any }) => {
  const msg = normalizePluginMessage(raw);
  if (!msg) return;

  if (msg.type === "export-frame") {
    const node = getSelectedFrame();
    if (!node) {
      figma.notify("HMI: select a frame (or something inside a frame) first.", { error: true, timeout: 5 });
      figma.ui.postMessage({
        type: "error",
        message:
          "No Frame / Component / Instance in current selection. Click the frame name in the Layers list, or we will find one if you double-clicked inside a frame in a new build — re-import the plugin and try again.",
      });
      return;
    }

    figma.notify(`HMI: exporting "${node.name}"… (may take 10–40s for large frames)`, { timeout: 4 });
    figma.ui.postMessage({
      type: "status",
      message:
        `Sandbox: exporting "${node.name}" as PNG @2x (large frames can take 10–40s; watch Log below)…`,
    });

    try {
      const pngBytes = await node.exportAsync({
        format: "PNG",
        constraint: { type: "SCALE", value: 2 },
      });
      const base64 = figma.base64Encode(pngBytes);

      // No optional chaining: Figma's plugin sandbox engine rejects ?. in emitted code.
      const pay = msg.payload;
      const cssHints = pay && pay.includeCssHints ? await collectCssHints(node) : {};
      const variables = pay && pay.includeVariables ? await collectVariables(node) : {};

      figma.ui.postMessage({
        type: "frame-exported",
        data: {
          imageBase64: base64,
          frameName: node.name,
          width: Math.round(node.width),
          height: Math.round(node.height),
          cssHints,
          variables,
        },
      });
    } catch (err: any) {
      figma.notify("HMI: export failed — see Log.", { error: true, timeout: 5 });
      const em = err && typeof err.message === "string" ? err.message : String(err);
      figma.ui.postMessage({ type: "error", message: "Export failed: " + em });
    }
    return;
  }

  if (msg.type === "request-context") {
    // Re-fetch optional context (variables / css hints) without re-exporting
    const node = getSelectedFrame();
    const pay = msg.payload;
    const cssHints = node && pay && pay.includeCssHints ? await collectCssHints(node) : {};
    const variables = node && pay && pay.includeVariables ? await collectVariables(node) : {};

    figma.ui.postMessage({
      type: "context-ready",
      requestId: pay && pay.requestId,
      data: { cssHints, variables },
    });
    return;
  }

  if (msg.type === "ping") {
    figma.ui.postMessage({ type: "pong", message: `Plugin sandbox is alive. build=${BUILD_STAMP}` });
    return;
  }

  if (msg.type === "self-test") {
    figma.notify(`HMI: self-test received from UI (build ${BUILD_STAMP}).`, { timeout: 4 });
    figma.ui.postMessage({
      type: "status",
      message: `Self-test OK: sandbox responded (build ${BUILD_STAMP}).`,
    });
    return;
  }
};
