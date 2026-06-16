from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.graph.builder import build_graph
from app.data.platform_rules import PLATFORM_RULES, ASSET_TYPES
from app.schemas.requests import BatchGenerateRequest, GenerateRequest

app = FastAPI(title="Ecom Visual Factory", version="0.1.0")
graph = build_graph()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/platforms")
def list_platforms() -> dict:
    """Return available platforms and their basic info (no image rules to keep response light)."""
    return {
        "platforms": [
            {
                "key": k,
                "name": v["name"],
                "description": v.get("description", ""),
                "needs_manual_review": v.get("needs_manual_review", False),
            }
            for k, v in PLATFORM_RULES.items()
        ],
        "asset_types": ASSET_TYPES,
    }


@app.get("/api/v1/platform-rules/{platform_key}")
def get_platform_rules(platform_key: str) -> dict:
    """Return full platform rules including image requirements."""
    rules = PLATFORM_RULES.get(platform_key)
    if not rules:
        raise HTTPException(status_code=404, detail=f"Platform '{platform_key}' not found")
    return rules


@app.post("/api/v1/generate")
def generate(payload: GenerateRequest) -> dict:
    state = payload.to_state()
    return graph.invoke(state)


@app.post("/api/v1/batch-generate")
def batch_generate(payload: BatchGenerateRequest) -> dict:
    results = []
    for item in payload.items:
        results.append(graph.invoke(item.to_state()))
    return {"count": len(results), "results": results}


@app.get("/")
def index() -> HTMLResponse:
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>index.html not found</h1>", status_code=404)
