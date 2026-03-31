/// <reference types="@figma/plugin-typings" />

figma.showUI(__html__, { width: 480, height: 640 });

figma.ui.onmessage = async (msg: { type: string; payload?: any }) => {
  if (msg.type === "export-frame") {
    const selection = figma.currentPage.selection;
    if (selection.length === 0) {
      figma.ui.postMessage({ type: "error", message: "Please select a frame first." });
      return;
    }

    const node = selection[0];
    if (node.type !== "FRAME" && node.type !== "COMPONENT" && node.type !== "INSTANCE") {
      figma.ui.postMessage({ type: "error", message: "Selected node must be a Frame, Component, or Instance." });
      return;
    }

    try {
      const pngBytes = await node.exportAsync({
        format: "PNG",
        constraint: { type: "SCALE", value: 2 },
      });

      const base64 = figma.base64Encode(pngBytes);

      let cssHints: Record<string, Record<string, string>> = {};
      if (msg.payload?.includeCssHints) {
        try {
          const css = await (node as any).getCSSAsync();
          cssHints[node.name] = css;
          if ("children" in node) {
            for (const child of (node as FrameNode).children.slice(0, 10)) {
              if ("getCSSAsync" in child) {
                const childCss = await (child as any).getCSSAsync();
                cssHints[child.name] = childCss;
              }
            }
          }
        } catch {
          // getCSSAsync may not be available in all API versions
        }
      }

      let variables: Record<string, string> = {};
      if (msg.payload?.includeVariables) {
        try {
          const localVars = await figma.variables.getLocalVariablesAsync();
          for (const v of localVars.slice(0, 50)) {
            const collection = await figma.variables.getVariableCollectionById(v.variableCollectionId);
            if (collection && collection.modes.length > 0) {
              const modeId = collection.modes[0].modeId;
              const val = v.valuesByMode[modeId];
              if (typeof val === "string" || typeof val === "number") {
                variables[`--${v.name.replace(/\//g, "-")}`] = String(val);
              }
            }
          }
        } catch {
          // Variables API may not be available
        }
      }

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
      figma.ui.postMessage({ type: "error", message: `Export failed: ${err.message}` });
    }
  }

  if (msg.type === "ping") {
    figma.ui.postMessage({ type: "pong", message: "Plugin sandbox is alive." });
  }
};
