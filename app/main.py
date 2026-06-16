from fastapi import FastAPI

from app.graph.builder import build_graph
from app.schemas.requests import BatchGenerateRequest, GenerateRequest

app = FastAPI(title="Ecom Visual Factory", version="0.1.0")
graph = build_graph()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
