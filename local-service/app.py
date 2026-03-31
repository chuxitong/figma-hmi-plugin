"""
Local AI service for HMI Code Generator Figma plugin.
Wraps the UI2Code^N model into HTTP endpoints.
"""

import base64
import io
import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from renderer import render_html_to_png

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HMI Code Generator Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None


def get_model():
    """Lazy-load the UI2Code^N model on first request."""
    global model
    if model is None:
        logger.info("Loading UI2Code^N model (this may take ~45 seconds)...")
        try:
            from model_wrapper import UI2CodeModel
            model = UI2CodeModel()
            logger.info("Model loaded successfully.")
        except ImportError:
            logger.warning(
                "model_wrapper not found. Using stub model for development."
            )
            model = StubModel()
    return model


class StubModel:
    """Development stub when the real model is not available."""

    def generate(self, image_bytes: bytes, **kwargs) -> str:
        return (
            "<!DOCTYPE html>\n<html><head><style>\n"
            "  body { background: #1e1e2e; color: #e0e0e0; font-family: sans-serif; "
            "padding: 24px; }\n"
            "  .card { background: #2a2a3e; border-radius: 8px; padding: 16px; "
            "margin: 8px; display: inline-block; width: 200px; }\n"
            "  .status { display: inline-block; width: 12px; height: 12px; "
            "border-radius: 50%; margin-right: 8px; }\n"
            "  .ok { background: #4caf50; }\n"
            "  .warn { background: #ff9800; }\n"
            "</style></head><body>\n"
            "<h2>Equipment Status</h2>\n"
            '<div class="card"><span class="status ok"></span>Pump A — Running</div>\n'
            '<div class="card"><span class="status warn"></span>Pump B — Warning</div>\n'
            "</body></html>"
        )

    def refine(self, reference_bytes: bytes, current_code: str, **kwargs) -> str:
        return current_code.replace("margin: 8px", "margin: 12px")

    def edit(self, current_code: str, instruction: str, **kwargs) -> str:
        if "secondary" in instruction.lower():
            return current_code.replace("background: #2a2a3e", "background: #3a3a4e")
        return current_code


# ── Request / Response models ──


class GenerateRequest(BaseModel):
    image_base64: str
    frame_name: str = "Untitled"
    width: int = 1280
    height: int = 720
    css_hints: Optional[dict] = None
    variables: Optional[dict] = None


class RefineRequest(BaseModel):
    reference_image_base64: str
    current_code: str
    css_hints: Optional[dict] = None
    variables: Optional[dict] = None


class EditRequest(BaseModel):
    current_code: str
    instruction: str


class RenderRequest(BaseModel):
    html_code: str
    width: int = 1280
    height: int = 720


class CodeResponse(BaseModel):
    code: str
    preview_base64: Optional[str] = None
    explanation: Optional[str] = None


class RenderResponse(BaseModel):
    image_base64: str


# ── Endpoints ──


@app.post("/generate", response_model=CodeResponse)
async def generate(req: GenerateRequest):
    """Generate HTML/CSS code from a UI screenshot."""
    image_bytes = base64.b64decode(req.image_base64)
    m = get_model()

    code = m.generate(
        image_bytes,
        frame_name=req.frame_name,
        width=req.width,
        height=req.height,
        css_hints=req.css_hints,
        variables=req.variables,
    )

    preview_b64 = None
    try:
        preview_bytes = await render_html_to_png(code, req.width, req.height)
        preview_b64 = base64.b64encode(preview_bytes).decode()
    except Exception as e:
        logger.warning(f"Preview rendering failed: {e}")

    return CodeResponse(
        code=code,
        preview_base64=preview_b64,
        explanation="Initial code generated from screenshot.",
    )


@app.post("/refine", response_model=CodeResponse)
async def refine(req: RefineRequest):
    """Refine code to better match the reference mockup."""
    ref_bytes = base64.b64decode(req.reference_image_base64)
    m = get_model()

    code = m.refine(
        ref_bytes,
        req.current_code,
        css_hints=req.css_hints,
        variables=req.variables,
    )

    preview_b64 = None
    try:
        preview_bytes = await render_html_to_png(code)
        preview_b64 = base64.b64encode(preview_bytes).decode()
    except Exception as e:
        logger.warning(f"Preview rendering failed: {e}")

    return CodeResponse(
        code=code,
        preview_base64=preview_b64,
        explanation="Code refined to better match the reference image.",
    )


@app.post("/edit", response_model=CodeResponse)
async def edit(req: EditRequest):
    """Edit existing code according to a natural-language instruction."""
    m = get_model()
    code = m.edit(req.current_code, req.instruction)

    preview_b64 = None
    try:
        preview_bytes = await render_html_to_png(code)
        preview_b64 = base64.b64encode(preview_bytes).decode()
    except Exception as e:
        logger.warning(f"Preview rendering failed: {e}")

    return CodeResponse(
        code=code,
        preview_base64=preview_b64,
        explanation=f'Edit applied: "{req.instruction}"',
    )


@app.post("/render", response_model=RenderResponse)
async def render(req: RenderRequest):
    """Render HTML code to a PNG screenshot."""
    image_bytes = await render_html_to_png(req.html_code, req.width, req.height)
    return RenderResponse(image_base64=base64.b64encode(image_bytes).decode())


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
